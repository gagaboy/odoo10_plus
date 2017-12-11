# Part of Odoo S.A.,Flectra See LICENSE file for full copyright and
# licensing details.

from flectra import api, fields, models
from flectra.tools.translate import _


class FinalInvoiceCreate(models.TransientModel):
    _name = 'final.invoice.create'

    name = fields.Boolean('Log of Activity')
    product_id = fields.Many2one('product.product', 'Product')
    time = fields.Boolean('Time Spent')
    date = fields.Boolean('Date ')
    price = fields.Boolean('Cost')

    @api.multi
    def create_invoice(self):
        self.ensure_one()
        context = self.env.context or {}

        if 'default_type' in context:
            del context['default_type']

        account_analytic_line_ids = self.env['account.analytic.line'].search([
            ('invoice_id', '=', False),
            ('account_id', 'in', context.get('active_ids')),
            ('to_invoice', '!=', False),
        ])
        invoice_ids = self.env['account.analytic.line'].create_invoice_cost(
            account_analytic_line_ids.ids, self.read()[0])
        action_invoice = self.env.ref('account.action_invoice_tree1').read()[0]
        action_invoice.update({'domain': [('id', 'in', invoice_ids),
                                          ('type', '=', 'out_invoice')]})
        action_invoice.update({'name': _('Invoices')})
        return action_invoice
