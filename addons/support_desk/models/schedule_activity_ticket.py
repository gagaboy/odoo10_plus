# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _
from flectra.exceptions import UserError
from datetime import date
import math


class ScheduleActivity(models.Model):
    _name = 'schedule.activity'
    _rec_name = 'activity_type_id'

    activity_type_id = fields.Many2one('mail.activity.type', 'Activity')
    summary = fields.Char('Summary')
    note = fields.Html('Note')
    feedback = fields.Html('Feedback')
    date_deadline = fields.Date('Due Date', index=True)
    due_days = fields.Char('Due In', compute='_compute_days')
    res_reference_id = fields.Many2one('supportdesk.ticket', string="Ticket")
    mail_activity_id = fields.Many2one('mail.activity', string="Mail "
                                                               "activity ID")
    user_id = fields.Many2one('res.users', 'Assigned to', index=True)

    res_state = fields.Selection([
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel')], string='State', default='in_progress')

    @api.depends('date_deadline')
    def _compute_days(self):
        for record in self:
            today = date.today()
            date_deadline = fields.Date.from_string(record.date_deadline)
            diff = (date_deadline - today)
            if diff.days == 0:
                record.due_days = 'Today'
            elif diff.days == 1:
                record.due_days = 'Tomorrow'
            elif diff.days == -1:
                record.due_days = 'Yesterday'
            elif diff.days > 1:
                record.due_days = ('Due in %d days' % math.fabs(diff.days))
            elif diff.days < -1:
                record.due_days = ('%d days overdue' % math.fabs(diff.days))

    @api.multi
    def unlink(self):
        for record in self:
            if record.res_state == 'in_progress':
                raise UserError(_(
                    'You cannot remove activity which is in Progress state'))
        return super(ScheduleActivity, self).unlink()
