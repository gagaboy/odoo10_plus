# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _
from flectra.exceptions import UserError


class Picking(models.Model):
    _inherit = "stock.picking"

    qc_po_count = fields.Integer(string="QC Count Purchase",
                                 compute='_compute_inspection')
    qc_so_count = fields.Integer(string="QC Count Sale",
                                 compute='_compute_inspection')
    inspection_ids = fields.One2many('qc.inspection',
                                     'picking_id', string="Inspection")
    incident_ids = fields.One2many('incident.report',
                                   'picking_id', string="Incident Report")
    qc_product = fields.Boolean(string="QC Product Check",
                                compute='check_qc_product')

    @api.multi
    def _compute_inspection(self):
        self.ensure_one()
        self.qc_po_count = len(self.purchase_id.inspection_ids)
        self.qc_so_count = len(self.sale_id.inspection_ids)

    @api.multi
    def check_qc_product(self):
        self.ensure_one()
        self.qc_product = False
        if self.sale_id and self.sale_id.inspection_ids or \
                self.purchase_id and self.purchase_id.inspection_ids:
            self.qc_product = True

    @api.multi
    def action_quality_control(self):
        self.ensure_one()
        report = self.env.ref(
            'quality_assurance_management.action_qc_inspection').read()[0]
        report.update({
            'context': {
                'default_purchase_id': self.purchase_id.id,
                'default_sale_id': self.sale_id.id
            },
            'domain': [('purchase_id', '=', self.purchase_id.id),
                       ('sale_id', '=', self.sale_id.id)]
        })
        return report

    @api.multi
    def create_incident(self):
        self.ensure_one()
        incident = self.env['incident.report'].create({
            'default_picking_id': self.id,
        })
        return {
            'name': _('Incident Report'),
            'res_model': 'incident.report',
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref(
                'quality_assurance_management.incident_report_form_view').id,
                       'form')],
            'context': {'default_picking_id': self.id},
            'res_id': incident.id,
        }

    @api.multi
    def action_done(self):
        inspect_product = self.mapped('move_line_ids').filtered(
            lambda x: x.qty_done != 0).mapped('product_id')
        inspect_purchase = self.purchase_id.inspection_ids.filtered(
            lambda x: x.quality_state == 'todo' and
                      x.product_id in inspect_product)
        inspect_sale = self.sale_id.inspection_ids.filtered(
            lambda x: x.quality_state == 'todo' and
                      x.product_id in inspect_product)
        if inspect_purchase or inspect_sale:
            raise UserError(_('Please Complete the Process of Inspection '
                              'first!'))
        return super(Picking, self).do_transfer()

    @api.multi
    def action_cancel(self):
        res = super(Picking, self).action_cancel()
        self.sudo().mapped('sale_id.inspection_ids').filtered(
            lambda x: x.quality_state == 'todo').unlink()
        self.sudo().mapped('purchase_id.inspection_ids').filtered(
            lambda x: x.quality_state == 'todo').unlink()
        return res
