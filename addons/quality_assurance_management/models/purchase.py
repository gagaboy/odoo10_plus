# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    inspection_ids = fields.One2many('qc.inspection', 'purchase_id',
                                     string="Inspection")

    @api.multi
    def action_quality_control(self):
        self.ensure_one()
        action = self.env.ref(
            'quality_assurance_management.action_qc_inspection').read()[0]
        action.update({
            'domain': [('purchase_id', '=', self.id)],
            'context': {'default_purchase_id': self.id}
        })
        return action

    @api.multi
    def action_view_picking(self):
        ins_obj = self.env['qc.inspection']
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
                for qc in set(qc_test_ids):
                    inspection = ins_obj.create({
                        'product_id': line.product_id.id,
                        'product_categ_id': line.product_id.categ_id.id,
                        'picking_type_id': self.picking_type_id.id,
                        'product_qty': line.product_qty,
                        'purchase_id': self.id,
                        'qc_test_id': qc.id,
                        'reference': self.name,
                        'ref_date': self.date_order,
                        'partner_id': self.partner_id.id,
                        'qc_team_id': qc.qc_team_id.id,
                        'responsible_id': qc.responsible_id.id
                    })
                    inspection.create_inspection_line()
        return super(PurchaseOrder, self).action_view_picking()
