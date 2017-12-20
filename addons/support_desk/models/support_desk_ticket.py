# Part of Flectra. See LICENSE file for full copyright and licensing details.

import uuid
from datetime import datetime
from flectra import api, fields, models


class SupportdeskSkills(models.Model):
    _name = 'supportdesk.skill'
    _description = 'Skills'

    name = fields.Char('Name')
    description = fields.Text('Skill')
    sequence = fields.Integer('Sequence')
    agent_ids = fields.Many2many('res.users', 'Agents')


class SupportdeskCategory(models.Model):
    _name = 'supportdesk.category'
    _description = 'SupportDesk Category'

    name = fields.Char(required=True, translate=True)
    category_color = fields.Integer('Index Color')


class SupportdeskType(models.Model):
    _name = 'supportdesk.ticket.type'
    _description = 'SupportDesk Ticket Type'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=1)


class SupportdeskTicket(models.Model):
    _name = 'supportdesk.ticket'
    _description = 'Supportdesk Ticket'
    _inherit = ['mail.thread', 'utm.mixin', 'mail.activity.mixin',
                'portal.mixin']
    _order = 'priority desc, id desc'

    def _default_supporteam_id(self):
        team_obj = self.env['supportdesk.team']
        support_team_id = self._context.get('default_team_id')
        if not support_team_id:
            return team_obj.search(
                [('agent_ids', 'in', self.env.uid)], limit=1).id or \
                team_obj.search([], limit=1).id
        return support_team_id

    @api.model
    def _get_group_stage_ids(self, stages, domain, order):
        domain = stages and [('id', 'in', stages.ids)] or []
        if self._context.get('default_team_id'):
            if domain:
                domain = ['|', ('team_ids', 'in', [
                    self.env.context['default_team_id']])] + domain
            else:
                domain = [('team_ids', 'in', [self.env.context[
                    'default_team_id']])]

        return stages.search(domain, order=order)

    number = fields.Char(string='#Ticket No')
    name = fields.Char('Subject', required=True, index=True)
    description = fields.Html()
    active = fields.Boolean(default=True)
    ticket_color = fields.Integer(string='Color Index')
    support_team_id = fields.Many2one('supportdesk.team', string='Team',
                                      default=_default_supporteam_id,
                                      index=True)
    access_token = fields.Char('Security Token', copy=False,
                               default=lambda self: str(uuid.uuid4()),
                               required=True)

    type_id = fields.Many2one('supportdesk.ticket.type', string="Type")
    category_ids = fields.Many2many('supportdesk.category',
                                    string='Categories')
    company_id = fields.Many2one(related='support_team_id.company_id',
                                 string='Company', store=True, readonly=True)

    skill_ids = fields.Many2many('supportdesk.skill', 'rel_skill_ticket',
                                 'ticket_id', 'skill_id', 'Skills')
    stage_id = fields.Many2one('supportdesk.stage', string='Stage',
                               track_visibility='onchange',
                               group_expand='_get_group_stage_ids', copy=False,
                               index=True,
                               domain="[('team_ids', '=', support_team_id)]")
    kanban_state = fields.Selection(
        [('normal', 'Normal'), ('blocked', 'Blocked'),
            ('done', 'Ready for next stage')], string='Kanban State',
        default='normal', required=True, track_visibility='onchange')
    responsible_user_id = fields.Many2one('res.users', string='Assigned to',
                                          track_visibility='onchange', )
    assignee_partner_id = fields.Many2one('res.partner', 'Assignee Partner')
    partner_id = fields.Many2one('res.partner', string='Requestor')
    email = fields.Char(related='requestor_email', string='Requestor Email')
    requestor_name = fields.Char(string='Requestor Name')
    requestor_email = fields.Char(string='Requestor Email')

    resolved_date = fields.Date("Resolved Date")
    resolved_hours = fields.Integer("Resolved Hours",
                                    compute='_compute_resolved_hours',
                                    store=True)
    active_sla_policy = fields.Boolean(string='SLA Active',
                                       compute='_set_sla_policy_fail',
                                       store=True)
    sla_policy_fail = fields.Boolean(string='Failed SLA Policy',
                                     compute='_set_sla_policy_fail',
                                     store=True)
    priority = fields.Selection(
        [('0', 'Normal'), ('1', 'Low Priority'), ('2', 'High Priority'),
         ('3', 'Critical')], string='Priority', default='0')
    overdue_date = fields.Datetime(string='Overdue Date',
                                   compute='_get_sla_policy', store=True)
    sla_policy_id = fields.Many2one('supportdesk.sla', string='SLA Policy',
                                    compute='_get_sla_policy', store=True)
    sla_policy_name = fields.Char(string='SLA Policy name',
                                  compute='_get_sla_policy', store=True)

    def get_hours_diff_from_dates(self, create_date):
        time_difference = datetime.now() - fields.Datetime.from_string(
            create_date)
        taken_hours = (time_difference.seconds) / 3600 + \
            time_difference.days * 24
        return taken_hours

    @api.depends('resolved_date')
    def _compute_resolved_hours(self):
        for support_ticket in self:
            if not support_ticket.create_date:
                continue
            support_ticket.resolved_hours = self.get_hours_diff_from_dates(
                support_ticket.create_date)

    def _onchange_team_values(self, team):
        user_id = team.assign_user_to_tickets()
        return {
            'responsible_user_id': user_id and user_id or False,
            'stage_id': self.env['supportdesk.stage'].search(
                [('team_ids', 'in', team.id)], order='sequence', limit=1).id
        }

    @api.model
    def default_get(self, fields):
        res = super(SupportdeskTicket, self).default_get(fields)
        if res.get('support_team_id'):
            values = self._onchange_team_values(
                self.env['supportdesk.team'].browse(res['support_team_id']))
            if (not fields or 'responsible_user_id' in fields) and \
                    'responsible_user_id' not in res:
                res['responsible_user_id'] = values['responsible_user_id']
            if (not fields or 'stage_id' in fields) and 'stage_id' not in res:
                res['stage_id'] = values['stage_id']
        return res

    @api.onchange('support_team_id', 'partner_id')
    def onchange_support_team_partner_id(self):
        if self.support_team_id:
            values = self._onchange_team_values(self.support_team_id)
            if not self.stage_id or self.stage_id not in \
                    self.support_team_id.stage_ids:
                self.stage_id = values['stage_id']
            if not self.responsible_user_id:
                self.responsible_user_id = values['responsible_user_id']
        if self.partner_id:
            self.requestor_name = self.partner_id.name
            self.requestor_email = self.partner_id.email

    @api.depends('support_team_id', 'type_id', 'create_date', 'priority')
    def _get_sla_policy(self):
        sla_obj = self.env['supportdesk.sla']
        for support_ticket in self:
            sla = sla_obj.search([
                ('team_id', '=', support_ticket.support_team_id.id),
                ('priority', '<=', support_ticket.priority),
                ('ticket_type_id', 'in', [support_ticket.type_id.id, False])],
                order="resolve_time_days, resolve_time_hours", limit=1)
            ticket_create_date = fields.Datetime.from_string(
                support_ticket.create_date)
            working_calendar = support_ticket.support_team_id and \
                support_ticket.support_team_id.working_hour_ids or \
                self.env.user.company_id.resource_calendar_id
            if sla and support_ticket.sla_policy_id != sla and \
                    support_ticket.active and \
                    support_ticket.create_date:
                support_ticket.sla_policy_id = sla.id
                support_ticket.sla_policy_name = sla.name
                if sla.resolve_time_days > 0 or sla.resolve_time_hours > 0:
                    overdue_date = working_calendar.plan_days(
                        sla.resolve_time_days + 1,
                        ticket_create_date, compute_leaves=True)
                    overdue_date = overdue_date.replace(
                        hour=ticket_create_date.hour,
                        minute=ticket_create_date.minute,
                        second=ticket_create_date.second,
                        microsecond=ticket_create_date.microsecond)
                else:
                    overdue_date = ticket_create_date

                support_ticket.overdue_date = working_calendar.plan_hours(
                    sla.resolve_time_hours, overdue_date, compute_leaves=True)

    @api.depends('overdue_date', 'stage_id.sequence',
                 'sla_policy_id.stage_id.sequence')
    def _set_sla_policy_fail(self):

        for support_ticket in self:
            active_sla_policy = True
            sla_policy_fail = False
            if not support_ticket.overdue_date:
                active_sla_policy = False
                sla_policy_fail = False
            if support_ticket.overdue_date and \
                    support_ticket.stage_id.sequence >= \
                    support_ticket.sla_policy_id.stage_id.sequence \
                    and support_ticket.responsible_user_id and \
                    fields.Datetime.now() > \
                    support_ticket.overdue_date:
                active_sla_policy = False
                sla_policy_fail = True
            support_ticket.active_sla_policy = active_sla_policy
            support_ticket.sla_policy_fail = sla_policy_fail

    @api.onchange('responsible_user_id')
    def onchange_responsible_user_id(self):
        self.assignee_partner_id = self.responsible_user_id and \
            self.responsible_user_id.partner_id or False

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        if self.stage_id and self.stage_id.set_done and \
                self.support_team_id and \
                self.support_team_id.ticket_assignation != 'manual':
            unassigned_tickets = self.search([
                ('stage_id.set_done', '=',  False),
                ('responsible_user_id', '=', False),
                ('support_team_id', '=', self.support_team_id.id)
            ])
            if unassigned_tickets:
                self.support_team_id.assign_user_to_tickets()

    @api.model
    def recalculate_open_tickets(self):
        tickets = self.search([('stage_id.set_done', '=', False)])
        tickets._get_sla_policy()
        tickets._set_sla_policy_fail()
        tickets._compute_resolved_hours()
        return True

    @api.multi
    def own_ticket_assignment(self):
        self.ensure_one()
        self.responsible_user_id = self.env.user

    @api.multi
    def unlink(self):
        schedule_act_obj = self.env['schedule.activity']
        mail_act_obj = self.env['mail.activity']
        for record in self:
            schedule_act_obj.search([
                ('res_reference_id', '=', record.id)]).unlink()
            mail_act_obj.search(
                [('res_id', '=', record.id)]).unlink()
        return super(SupportdeskTicket, self).unlink()

    @api.multi
    def write(self, vals):
        now = fields.Datetime.now()
        stage_obj = self.env["supportdesk.stage"]
        for support_ticket in self:
            if vals.get('stage_id') and stage_obj.browse(
                    vals['stage_id']).set_done:
                vals.update({'resolved_date': now})
            if vals.get('partner_id'):
                support_ticket.message_subscribe([vals['partner_id']])
        return super(SupportdeskTicket, self).write(vals)

    @api.model
    def create(self, vals):
        res = super(SupportdeskTicket, self).create(vals)
        res.number = str(res.id)
        return res
