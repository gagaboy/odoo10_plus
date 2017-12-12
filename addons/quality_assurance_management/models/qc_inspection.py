# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _
from flectra.addons import decimal_precision as dp
from flectra.exceptions import UserError


class QcInspection(models.Model):
    _name = 'qc.inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'QC Inspection'

    name = fields.Char(string="Reference", copy=False, default=lambda self: _(
        'New'), readonly=True, required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_categ_id = fields.Many2one('product.category',
                                       string='Product Category')
    product_uom_id = fields.Many2one('product.uom', string='Unit of Measure')
    product_qty = fields.Float('Quantity', default=1.0, required=True,
                               digits=dp.get_precision('Unit of Measure'))
    partner_id = fields.Many2one('res.partner', string="Partner")
    inspection_date = fields.Date(string="Date",
                                  default=fields.Date.context_today)
    reference = fields.Char(string="Reference")
    ref_date = fields.Date(string="Ref. Date")
    qc_team_id = fields.Many2one('qc.team', string="QC Team",
                                 track_visibility='onchange')
    responsible_id = fields.Many2one('res.users', string="Responsible")
    qc_test_id = fields.Many2one('qc.test', string="QC Test")
    quantitative_ids = fields.One2many('quantitative.quality', 'inspection_id',
                                       string="Quantitative")
    qualitative_ids = fields.One2many('qualitative.quality', 'inspection_id',
                                      string="Qualitative")
    purchase_id = fields.Many2one('purchase.order', string="Purchase")
    picking_id = fields.Many2one('stock.picking', string="Picking")
    picking_type_id = fields.Many2one('stock.picking.type', string="Operation")
    production_id = fields.Many2one('mrp.production', 'Production Order')
    sale_id = fields.Many2one('sale.order', string="Sale Order")
    reason_id = fields.Many2one('inspection.reason', string="Reason")
    remarks = fields.Text(string="Remarks")
    color = fields.Integer(compute='_check_color', string="Color")
    incident_ids = fields.One2many('incident.report', 'inspection_id',
                                   string='Incident Report')
    incident_count = fields.Integer('# Incident Reports',
                                    compute="_compute_incident_count")
    quality_state = fields.Selection([('todo', 'To do'), ('pass', 'Passed'),
                                      ('fail', 'Failed')], string='Status',
                                     track_visibility='onchange',
                                     default='todo', copy=False)

    @api.multi
    def _compute_incident_count(self):
        self.ensure_one()
        self.incident_count = len(self.incident_ids)

    @api.onchange('qc_team_id')
    def get_responsible_id(self):
        self.ensure_one()
        return {'domain': {'responsible_id': [
            ('id', 'in', self.qc_team_id.member_ids.ids)]}}

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'quality_state' in init_values and self.quality_state == 'fail':
            return 'quality_assurance_management.mt_qc_fail'
        elif 'quality_state' in init_values and self.quality_state == 'todo':
            return 'quality_assurance_management.mt_qc_create'
        return super(QcInspection, self)._track_subtype(init_values)

    @api.multi
    def _check_color(self):
        for record in self:
            res = {'todo': 15,
                   'pass': 10,
                   'fail': 1,
                   }
            record.color = res.get(record.quality_state, False)

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'qc.inspection') or _('New')
        return super(QcInspection, self).create(vals)

    @api.multi
    def create_inspection_line(self):
        self.ensure_one()
        for line in self.qc_test_id.quantitative_ids:
            self.env['quantitative.quality'].create({
                'name': line.name,
                'type': line.type,
                'min_dimension': line.min_dimension,
                'min_value': line.min_value,
                'max_dimension': line.max_dimension,
                'max_value': line.max_value,
                'inspection_id': self.id
            })

        for line in self.qc_test_id.qualitative_ids:
            self.env['qualitative.quality'].create({
                'name': line.name,
                'type': line.type,
                'question_ids': [(0, 0, {'question': x.question}) for x in
                                 line.question_ids],
                'inspection_id': self.id
            })
        return True

    @api.multi
    def action_pass(self):
        self.ensure_one()
        quantitative_ids = [line for line in self.quantitative_ids
                            if not line.dimension_status]
        qualitative_ids = [line for line in self.qualitative_ids
                           if not line.dimension_status]
        if quantitative_ids or qualitative_ids:
            raise UserError(_('Please fill the %s field value for all '
                              'lines') % (
                                (quantitative_ids and 'Inspected Value') or (
                                    qualitative_ids and 'Results')))
        else:
            self.write({'quality_state': 'pass'})

    @api.multi
    def action_incident(self):
        self.ensure_one()
        incident_vals = {
            'inspection_id': self.id,
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            'qc_team_id': self.qc_team_id.id,
            'inspection_reason_id': self.reason_id.id,
            'responsible_id': self.responsible_id.id,
        }
        incident = self.env['incident.report'].create(incident_vals)
        return {
            'name': _('Incident Report'),
            'res_model': 'incident.report',
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref(
                'quality_assurance_management.incident_report_form_view').id,
                       'form')],
            'context': {'default_inspection_id': self.id},
            'res_id': incident.id,
        }

    @api.multi
    def action_open_incident(self):
        incident = self.mapped('incident_ids')
        report = self.env.ref(
            'quality_assurance_management.action_incident_report_view').read()[
            0]
        report['context'] = {
            'default_inspection_id': self.id
        }
        if len(incident) > 1:
            report['domain'] = [('id', 'in', incident.ids)]
        elif len(incident) == 1:
            report['views'] = [(self.env.ref(
                'quality_assurance_management.incident_report_form_view').id,
                                'form')]
            report['res_id'] = incident.ids[0]
        return report

    @api.multi
    def unlink(self):
        for qc in self:
            if qc.quality_state not in ('todo'):
                raise UserError(_('You can not delete a Passed or Failed QC '
                                  'Inspection!'))
        return super(QcInspection, self).unlink()
