# Part of Flectra See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def _compute_balance(self):
        for aml in self:
            aml.amount_balance = aml.debit - aml.credit

    date_payment_followup = fields.Date('Follow-up Date', index=True)
    payment_followup_line_id = fields.Many2one(
        'payment.followup.line', 'Follow-up Line',
        ondelete='restrict')
    amount_balance = fields.Float(compute='_compute_balance',
                           string="Balance")
