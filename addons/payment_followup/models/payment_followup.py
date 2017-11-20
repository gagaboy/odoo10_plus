# Part of Flectra See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _


class PaymentFollowup(models.Model):
    _name = 'payment.followup'
    _description = 'Payment Follow-up'

    name = fields.Char(string="Name",
                       readonly=True, related='company_id.name')
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'payment.followup'))
    payment_followup_line = fields.One2many('payment.followup.line',
                                            'payment_followup_id', 'Follow-up', copy=True)

    _sql_constraints = [('unique_followup_company_id', 'unique(company_id)',
                         'Payment follow-up creation is allowed only once per company.')]


class PaymentFollowupLine(models.Model):
    _name = 'payment.followup.line'
    _description = 'Payment Follow-up Criteria'
    _order = 'waiting_period'

    @api.multi
    def _get_default_mail_template_id(self):
        try:
            return self.env.ref(
                'payment_followup.email_template_payment_followup_default').id
        except ValueError:
            return False

    name = fields.Char('Reference', required=True)
    number = fields.Integer('Ref. Number')
    payment_followup_id = fields.Many2one('payment.followup', 'Payment Follow-up',
                             required=True, ondelete="cascade")
    waiting_period = fields.Integer('Waiting Period', required=True)

    reminder_mail = fields.Boolean('Mail Reminder', default=True)
    template_id = fields.Many2one('mail.template', 'Template',
                                       ondelete='set null',
                                       default=_get_default_mail_template_id)
    reminder_communication = fields.Boolean('Reminder Communication', default=True)
    todo_activity = fields.Text('TODO Activity')
    manual_activity = fields.Boolean('Manual Activity', default=False)
    user_id = fields.Many2one('res.users', 'Responsible', ondelete='set null')
    communication = fields.Text(
        'Communication', translate=True,
        default="""
            Dear Sir,
            Our Ref: %(partner_name)s,
            
            It has come to our attention that your account is overdue for payment.
            
            We are not aware of any disputes or reason for non-payment, therefore we would respectfully remind you that you have exceeded the trading terms for these outstanding amounts and we would be grateful to receive your remittance as soon as possible.
            We look forward to hearing from you.
            
            Yours sincerely
    """)

    _sql_constraints = [('unique_followup_waiting_period', 'unique(payment_followup_id, waiting_period)',
                         'Waiting period has to be different!')]

    @api.multi
    def _is_valid_message(self):
        self.ensure_one()
        for line in self:
            if line.communication:
                try:
                    line.communication % {'partner_name': '', 'date': '',
                                    'user_signature': '',
                                    'company_name': ''}
                except:
                    return False
        return True

    _constraints = [
        (_is_valid_message,
         'Invalid description, use the right legend or %% if '
         'you want to use the percent character.', ['communication']),
    ]
