# Part of Flectra. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from flectra import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_id = fields.Many2one('sale.order', string="Sale Order",
                              compute="get_sale_id", store=True)
    total_change_order = fields.Integer(
        'Total Change Orders',
        compute='_compute_engineering_change_order_data')
    change_request_ids = fields.One2many(
        'engineering.change.request', 'manufacture_order', 'ECR')

    @api.multi
    def button_engineering_change_request(self):
        self.ensure_one()
        change_request = self.env['engineering.change.request'].search(
            [('manufacture_order', '=', self.id)])
        action = self.env.ref(
            'plm.action_engineering_change_request').read()[0]
        action['context'] = {
            'default_product_tmpl_id': self.product_tmpl_id.id,
            'default_manufacture_order': self.id
        }
        if len(change_request) > 1:
            action['domain'] = [('id', 'in', change_request.ids)]
        elif len(change_request) == 1:
            action['views'] = [
                (self.env.ref('plm.engineering_change_request_form_view').id,
                 'form')]
            action['res_id'] = change_request.ids[0]
        return action

    @api.multi
    def _compute_engineering_change_order_data(self):
        self.ensure_one()
        self.total_change_order = len(self.change_request_ids)

    @api.depends('origin')
    def get_sale_id(self):
        sale_order = self.env['sale.order']
        for mo in self:
            mo.sale_id = sale_order.search([('name', '=', mo.origin)])

    @api.multi
    def create_ecr(self):
        self.ensure_one()
        ecr = self.env['engineering.change.request'].create({
            'requested_by': self.env.user.id,
            'ecr_date': datetime.today().date(),
            'product_id': self.product_id.id,
            'manufacture_order': self.id,
            'sale_id': self.sale_id.id,
        })
        return ecr
