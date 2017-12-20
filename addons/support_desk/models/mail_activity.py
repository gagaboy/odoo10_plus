# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    schedule_ticket_line = fields.One2many(
        'schedule.activity', 'mail_activity_id', string="Schedule Ticket ID")

    @api.model
    def create(self, values):
        res = super(MailActivity, self).create(values)

        if values.get('res_model_id') == self.env['ir.model'].search([(
                'model', '=', 'supportdesk.ticket')]).id:
            ticket_id = self.env['supportdesk.ticket'].browse(res.res_id)
            self.env['schedule.activity'].create({
                'activity_type_id': res.activity_type_id.id,
                'summary': res.summary,
                'note': res.note,
                'feedback': res.feedback,
                'date_deadline': res.date_deadline,
                'user_id': res.user_id.id,
                'mail_activity_id': res.id,
                'res_reference_id': ticket_id.id,
            })
        return res

    @api.multi
    def write(self, values):
        res = super(MailActivity, self).write(values)
        activity = self.env['schedule.activity'].search(
            [('mail_activity_id', '=', self.id)])
        if not self.feedback and activity:
            activity.write({
                'activity_type_id': self.activity_type_id.id,
                'summary': self.summary,
                'note': self.note,
                'date_deadline': self.date_deadline,
                'user_id': self.user_id.id,
            })
        return res

    @api.multi
    def unlink(self):
        activity_obj = self.env['schedule.activity']
        ticket_model = self.env['ir.model'].search(
            [('model', '=', 'supportdesk.ticket')])
        for record in self:
            if ticket_model and record.res_model_id.id == ticket_model.id:
                activity_id = activity_obj.search(
                    [('mail_activity_id', '=', record.id)])
                if activity_id and activity_id.res_state != 'done':
                    activity_id.res_state = 'cancel'
        return super(MailActivity, self).unlink()

    def action_feedback(self, feedback=False):
        message = self.env['mail.message']
        if feedback:
            self.write(dict(feedback=feedback))
        for activity in self:
            record = self.env[activity.res_model].browse(activity.res_id)
            record.message_post_with_view(
                'mail.message_activity_done',
                values={'activity': activity},
                subtype_id=self.env.ref('mail.mt_activities').id,
                mail_activity_type_id=activity.activity_type_id.id,
            )
            message |= record.message_ids[0]

        if self.res_model_id.id == self.env['ir.model'].search([(
                'model', '=', 'supportdesk.ticket')]).id:
            schedule_activity_id = self.env['schedule.activity'].search([(
                'mail_activity_id', '=', self.id)])
            if schedule_activity_id:
                schedule_activity_id.write({
                    'res_state': 'done',
                    'feedback': self.feedback
                })
        self.unlink()
        return message.ids and message.ids[0] or False
