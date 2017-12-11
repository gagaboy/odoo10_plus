# Part of Flectra See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from flectra import api, fields, models
from flectra.tools.translate import _
from flectra.tools.sql import drop_view_if_exists
from flectra.exceptions import UserError, ValidationError


class HrActivitySheet(models.Model):
    _name = "hr.activity.sheet"
    _table = 'hr_activity_sheet'
    _inherit = ['mail.thread']
    _description = "Activities Sheet"
    _order = "id desc"

    @api.model
    def _get_active_employee(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        return employee or False

    @api.model
    def _get_end_date(self):
        active_user = self.env['res.users'].browse(self.env.uid)
        range = \
            active_user.company_id and \
            active_user.company_id.sheet_generaton_period or 'weekly'
        date = fields.Date.context_today(self)
        if range == 'weekly':
            date = (datetime.today() + relativedelta(
                weekday=6)).strftime('%Y-%m-%d')
        elif range == 'monthly':
            date = (datetime.today() + relativedelta(
                months=+1, day=1, days=-1)).strftime('%Y-%m-%d')
        elif range == 'yearly':
            date = time.strftime('%Y-12-31')
        return date

    @api.model
    def _get_start_date(self):
        active_user = self.env['res.users'].browse(self.env.uid)
        range = \
            active_user.company_id and \
            active_user.company_id.sheet_generaton_period or 'weekly'
        date = fields.Date.context_today(self)
        if range == 'weekly':
            date = (datetime.today() + relativedelta(
                weekday=0, days=-6)).strftime('%Y-%m-%d')
        elif range == 'monthly':
            date = time.strftime('%Y-%m-01')
        elif range == 'yearly':
            date = time.strftime('%Y-01-01')
        return date

    name = fields.Char(
        string="Activity Sheet",
        states={'unapproved': [('readonly', True)],
                'approved': [('readonly', True)]})
    start_date = fields.Date(
        string='From Date', default=_get_start_date,
        index=True, states={'new': [('readonly', False)]})
    end_date = fields.Date(
        string='To Date', default=_get_end_date,
        index=True, states={'new': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company')
    user_id = fields.Many2one(
        'res.users', related='employee_id.user_id', string='User', store=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', default=_get_active_employee)
    department_id = fields.Many2one(
        'hr.department', string='Department',
        default=lambda self: self.env['res.company']._company_default_get())
    activity_ids = fields.One2many(
        'account.analytic.line', 'activity_sheet_id',
        string='Activity lines',
        states={
            'draft': [('readonly', False)],
            'new': [('readonly', False)]})
    state = fields.Selection([
        ('new', 'New'),
        ('draft', 'Draft'),
        ('unapproved', 'To Approve'),
        ('approved', 'Approved')], index=True, track_visibility='onchange',
        string='Activity Status', default='new')
    activity_account_ids = fields.One2many(
        'hr.activity.sheet.account', 'activity_sheet_id',
        string='Analytic Activity Account')

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'unapproved':
            return 'hr_activity_sheet.mt_unapproved_activity'
        elif 'state' in init_values and self.state == 'approved':
            return 'hr_activity_sheet.mt_approve_activity'
        return super(HrActivitySheet, self)._track_subtype(init_values)

    @api.multi
    def name_get(self):
        result = []
        for activity in self:
            current_week = datetime.strptime(
                activity.start_date, '%Y-%m-%d').isocalendar()[1]
            name = 'Activity Week ' + str(current_week)
            result.append((activity.id, name))
        return result

    @api.multi
    def write(self, vals):
        if vals.get('employee_id'):
            user = self.env['hr.employee'].browse(
                vals.get('employee_id')).user_id.id
            if not user:
                raise UserError(_('Activity will be created only if employee '
                                  'contains its related user.'))
            self._is_overlaping(user=user)
        return super(HrActivitySheet, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals.get('employee_id'))
            if not employee.user_id:
                raise UserError(_(
                    'Activity will be created only if employee '
                    'contains its related user.'))
        vals['state'] = 'draft'
        res = super(HrActivitySheet, self).create(vals)
        return res

    @api.multi
    def copy(self, default=None):
        raise UserError(_('You cannot duplicate an activity sheet.'))
        return super(HrActivitySheet, self).copy(default)

    @api.multi
    def unlink(self):
        activities = self.env['account.analytic.line']
        for activity in self:
            if activity.state in ['unapproved', 'approved']:
                raise UserError(_('submitted activity cannot be deleted.'))
            activities += activity.activity_ids.filtered(
                lambda line: not line.task_id)
        activities.unlink()
        return super(HrActivitySheet, self).unlink()

    @api.multi
    def set_activity_unapproved(self):
        for activity in self:
            manager = activity.employee_id and activity.employee_id.parent_id
            if manager and manager.user_id:
                self.message_subscribe_users(user_ids=[manager.user_id.id])
        self.write({'state': 'unapproved'})
        return True

    @api.onchange('employee_id')
    def on_employee_id_change(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id
            self.user_id = self.employee_id.user_id

    @api.multi
    def set_activity_draft(self):
        self.ensure_one()
        has_group = self.env.user.has_group(
            'hr_timesheet.group_hr_timesheet_user')
        if not has_group:
            raise UserError(_('Activities can only be Approved or Refused '
                              'by Managers'))
        self.write({'state': 'draft'})
        return True

    @api.multi
    def set_activity_approved(self):
        self.ensure_one()
        has_group = self.env.user.has_group(
            'hr_timesheet.group_hr_timesheet_user')
        if not has_group:
            raise UserError(_('Activities can only be Approved by Managers.'))
        if self.filtered(lambda sheet: sheet.state != 'unapproved'):
            raise UserError(_("Kindly submit your activity first!."))
        self.write({'state': 'approved'})

    @api.constrains('employee_id', 'end_date', 'start_date')
    def _is_overlaping(self, user=False):
        for activity in self:
            user_id = user or activity.user_id and activity.user_id.id
            if user:
                self.env.cr.execute('''
                        SELECT id
                        FROM hr_activity_sheet
                        WHERE
                        id <> %s
                        AND user_id=%s
                        AND (start_date <= %s and %s <= end_date)
                        ''', (activity.id, user_id, activity.end_date,
                              activity.start_date))
                if any(self.env.cr.fetchall()):
                    raise ValidationError(_(
                        'Activity sheet cannot be duplicated!.'))


class HrActivitySheetAccount(models.Model):
    _name = "hr.activity.sheet.account"
    _description = "Periodical Activity"
    _order = 'name'
    _auto = False

    name = fields.Many2one('account.analytic.account',
                           string='Project / Analytic Account', readonly=True)
    activity_sheet_id = fields.Many2one('hr.activity.sheet', string='Sheet')
    utilized_hour = fields.Float('Total Time', digits=(16, 2))

    _depends = {
        'hr.activity.sheet': ['user_id', 'start_date', 'end_date'],
        'account.analytic.line': ['user_id', 'date',
                                  'account_id', 'unit_amount']}

    @api.model_cr
    def init(self):
        drop_view_if_exists(self._cr, 'hr_activity_sheet_account')
        self._cr.execute("""create view hr_activity_sheet_account as (
            select
                min(line.id) as id,
                line.account_id as name,
                s.id as activity_sheet_id,
                sum(line.unit_amount) as utilized_hour
            from
                account_analytic_line line
                    LEFT JOIN hr_activity_sheet s
                        ON s.user_id = line.user_id
                        AND (
                        s.end_date >= line.date AND s.start_date <= line.date)
            group by line.account_id, s.id
        )""")
