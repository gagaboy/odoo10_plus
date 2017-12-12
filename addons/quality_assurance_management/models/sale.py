# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    READONLY_STATES = {
        'sale': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get(
            'company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'outgoing'),
                                 ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search(
                [('code', '=', 'outgoing'), ('warehouse_id', '=', False)])
        return types[:1]

    qc_count = fields.Integer(string="Qc Count", compute='_compute_inspection')
    inspection_ids = fields.One2many('qc.inspection', 'sale_id',
                                     string="Inspection")
    picking_type_id = fields.Many2one('stock.picking.type',
                                      string="Deliver To",
                                      states=READONLY_STATES, required=True,
                                      default=_default_picking_type)

    @api.multi
    def _compute_inspection(self):
        self.ensure_one()
        self.qc_count = len(self.inspection_ids)

    @api.multi
    def action_quality_control(self):
        self.ensure_one()
        action = self.env.ref(
            'quality_assurance_management.action_qc_inspection').read()[0]
        action.update({
            'context': {'default_sale_id': self.id},
            'domain': [('sale_id', '=', self.id)]
        })
        return action

    @api.multi
    def action_confirm(self):
        for line in self.order_line:
            qc_product_id = self.env['qc.test'].search([
                ('state', '=', 'approve'),
                ('picking_type_ids', 'in', self.picking_type_id.id),
                '|', ('product_id', '=', line.product_id.id),
                '&', ('product_id', '=', False), (
                    'product_tmpl_id', '=',
                    line.product_id.product_tmpl_id.id)
            ])
            qc_categ_id = self.env['qc.test'].search([
                ('categ_id', '=', line.product_id.categ_id.id),
                ('state', '=', 'approve'),
                ('picking_type_ids', 'in', self.picking_type_id.id)])
            qc_test_ids = qc_product_id + qc_categ_id
            if qc_product_id or qc_categ_id:
                for qc in qc_test_ids:
                    inspection = self.env['qc.inspection'].create({
                        'product_id': line.product_id.id,
                        'product_categ_id': line.product_id.categ_id.id,
                        'picking_type_id': self.picking_type_id.id,
                        'product_qty': line.product_uom_qty,
                        'reference': self.name,
                        'ref_date': fields.Datetime.now(),
                        'partner_id': self.partner_id.id,
                        'sale_id': self.id,
                        'qc_team_id': qc.qc_team_id.id,
                        'responsible_id': qc.responsible_id.id,
                        'qc_test_id': qc.id,
                    })
                    inspection.create_inspection_line()
        return super(SaleOrder, self).action_confirm()
