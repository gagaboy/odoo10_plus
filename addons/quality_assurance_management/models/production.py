# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _
from flectra.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.multi
    def _compute_incident_count(self):
        self.ensure_one()
        self.incident_count = len(self.incident_ids)

    @api.multi
    def _compute_inspection_count(self):
        self.ensure_one()
        self.inspection_count = len(self.inspection_ids)

    inspection_ids = fields.One2many('qc.inspection', 'production_id',
                                     string="Inspections")
    qc_product = fields.Boolean(string="QC Product",
                                compute='check_qc_boolean')
    incident_ids = fields.One2many('incident.report',
                                   'production_id', string="Incident Report")
    incident_count = fields.Integer(string="# Incident Reports",
                                    compute="_compute_incident_count")
    inspection_count = fields.Integer(string="# Inspection",
                                      compute="_compute_inspection_count")

    @api.multi
    def check_qc_boolean(self):
        self.ensure_one()
        self.qc_product = False
        if self.inspection_ids:
            self.qc_product = True

    @api.multi
    def action_assign(self):
        for manufacture in self:
            manufacture.move_raw_ids._action_assign()
            qc_product_id = self.env['qc.test'].search([
                ('state', '=', 'approve'),
                ('picking_type_ids', 'in', self.picking_type_id.id),
                '|', ('product_id', '=', manufacture.product_id.id),
                '&', ('product_id', '=', False), (
                    'product_tmpl_id', '=',
                    manufacture.product_id.product_tmpl_id.id)
            ])
            qc_categ_id = self.env['qc.test'].search([
                ('categ_id', '=', manufacture.product_id.categ_id.id),
                ('state', '=', 'approve'),
                ('picking_type_ids', 'in', self.picking_type_id.id)])
            qc_test_ids = qc_product_id + qc_categ_id
            if qc_product_id or qc_categ_id:
                for qc in set(qc_test_ids):
                    inspection = self.env['qc.inspection'].create({
                        'product_id': manufacture.product_id.id,
                        'product_categ_id': manufacture.product_id.categ_id.id,
                        'picking_type_id': manufacture.picking_type_id.id,
                        'product_qty': manufacture.product_qty,
                        'reference': manufacture.name,
                        'ref_date': manufacture.date_planned_start,
                        'production_id': self.id,
                        'qc_test_id': qc.id,
                        'qc_team_id': qc.qc_team_id.id,
                        'responsible_id': qc.responsible_id.id,
                    })
                    inspection.create_inspection_line()
        return True

    @api.multi
    def create_incident(self):
        self.ensure_one()
        incident = self.env['incident.report'].create({
            'default_product_tmpl_id': self.product_id.product_tmpl_id.id
        })
        return {
            'name': _('Incident Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'incident.report',
            'views': [(self.env.ref(
                'quality_assurance_management.incident_report_form_view').id,
                       'form')],
            'res_id': incident.id,
        }

    @api.multi
    def button_mark_done(self):
        for manufacture in self:
            for inspection in manufacture.inspection_ids:
                if inspection.quality_state == 'todo':
                    raise UserError(_('Please complete the process of Quality '
                                      'Inspection'))
        return super(MrpProduction, self).button_mark_done()

    @api.multi
    def action_cancel(self):
        result = super(MrpProduction, self).action_cancel()
        for inspection in self.inspection_ids:
            if inspection.quality_state == 'todo':
                inspection.unlink()
        return result

    @api.multi
    def action_quality_control(self):
        self.ensure_one()
        action = self.env.ref(
            'quality_assurance_management.action_qc_inspection').read()[0]
        action.update({
            'domain': [('production_id', '=', self.id)],
            'context': {'default_production_id': self.id}
        })
        return action

    @api.multi
    def action_incident_report(self):
        self.ensure_one()
        report = self.env.ref(
            'quality_assurance_management.action_incident_report_view').read()[
            0]
        report.update({
            'context': {'default_production_id': self.id},
            'views': [(False, 'form')]
        })
        return report
