# Part of Flectra See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _
from flectra.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    activity_sheet_id = fields.Many2one(
        'hr.activity.sheet', string='Activity',
        compute='_compute_activity_sheet_count', store=True)
    activity_sheet_count = fields.Many2one(
        'hr.activity.sheet', string='Activity Count',
        compute='_compute_activity_sheet_count',
        search='_search_sheet', ondelete='cascade', index=True)

    @api.multi
    def _is_valid_status(self):
        for activity in self:
            if activity.activity_sheet_id and \
                    activity.activity_sheet_id.state not in ('draft', 'new'):
                raise UserError(_(
                    'Confirmed activities’ entries cannot be updated.'))
        return True

    @api.multi
    def unlink(self):
        self._is_valid_status()
        return super(AccountAnalyticLine, self).unlink()

    @api.multi
    def write(self, values):
        self._is_valid_status()
        return super(AccountAnalyticLine, self).write(values)

    @api.depends('activity_sheet_count.employee_id',
                 'activity_sheet_count.end_date',
                 'activity_sheet_count.start_date',
                 'user_id', 'date', 'project_id')
    def _compute_activity_sheet_count(self):
        for activity in self:
            if not activity.project_id:
                continue
            sheets = self.env['hr.activity.sheet'].search(
                [('state', 'in', ['draft', 'new']),
                 ('employee_id.user_id.id', '=', activity.user_id.id),
                 ('end_date', '>=', activity.date),
                 ('start_date', '<=', activity.date)], limit=1)
            activity.activity_sheet_count = sheets or False
            activity.activity_sheet_id = sheets or False

    @api.multi
    def _search_sheet(self, operator, value):
        assert operator == 'in'
        activities = self.env['hr.activity.sheet'].browse(value)
        activity_ids = []
        for activity in activities:
            self._cr.execute("""
                    SELECT l.id
                        FROM account_analytic_line l
                    WHERE %(user_id)s = l.user_id
                        AND %(end_date)s >= l.date
                        AND %(start_date)s <= l.date
                    GROUP BY l.id""", {
                'user_id': activity.employee_id.user_id.id,
                'end_date': activity.end_date,
                'start_date': activity.start_date})
            activity_ids.extend([value[0] for value in self._cr.fetchall()])
        return [('id', 'in', activity_ids)]
