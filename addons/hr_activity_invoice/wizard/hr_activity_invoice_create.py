# Part of Odoo S.A.,Flectra See LICENSE file for full copyright and
# licensing details.

from flectra import api, fields, models
from flectra.exceptions import UserError
from flectra.tools.translate import _


class HRActivityInvoiceCreate(models.TransientModel):
    _name = 'hr.activity.invoice.create'
    _description = 'Create invoice from timesheet'

    name = fields.Boolean('Description', default=True)
    product_id = fields.Many2one('product.product', 'Product')
    price = fields.Boolean('Cost')
    date = fields.Boolean('Date ', default=True)
    time = fields.Boolean('Time spent')

    @api.multi
    def create_invoice(self):
        self.ensure_one()
        data = self.read()[0]
        context = self.env.context
        line_obj = self.env['account.analytic.line']

        invoice_ids = line_obj.create_invoice_cost(
            context.get('active_ids'), data)
        act_win = self.env.ref('account.action_invoice_tree1').read()[0]
        act_win.update({'domain': [('id', 'in', invoice_ids),
                                   ('type', '=', 'out_invoice')]})
        act_win.update({'name': _('Invoices')})
        return act_win

    @api.model
    def view_init(self, fields):
        data = self.env.context and self.env.context.get('active_ids', [])
        for analytic in self.env['account.analytic.line'].browse(data):
            if analytic.invoice_id:
                raise UserError(_(
                    "Invoice has already been linked to some of the \
                    analytic line(s)!"))
