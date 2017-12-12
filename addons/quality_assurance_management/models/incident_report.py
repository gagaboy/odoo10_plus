# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _
from flectra.exceptions import UserError


class IncidentReport(models.Model):
    _name = 'incident.report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Incident Report'

    name = fields.Char(string="Reference", copy=False, default=lambda self: _(
        'New'), readonly=True, required=True)
    product_tmpl_id = fields.Many2one('product.template', string="Product")
    qc_team_id = fields.Many2one('qc.team', string="Team",
                                 track_visibility='onchange')
    responsible_id = fields.Many2one('res.users', string="Responsible")
    inspection_reason_id = fields.Many2one('inspection.reason',
                                           string="Reason")
    start_date = fields.Datetime(string="Start Date",
                                 default=fields.Datetime.now())
    end_date = fields.Datetime(string="End Date")
    improvements = fields.Text(string="Improvements")
    protections = fields.Text(string="Protections")
    inspection_id = fields.Many2one('qc.inspection', string="Inspection")
    picking_id = fields.Many2one('stock.picking', string="Picking")
    production_id = fields.Many2one('mrp.production', string="Production")
    remarks = fields.Text(string="Remarks")
    state = fields.Selection([('new', 'New'), ('confirm', 'Confirmed'),
                              ('in_progress', 'In Progress'),
                              ('done', 'Done')],
                             default='new', string="State")

    @api.onchange('qc_team_id')
    def get_responsible_id(self):
        return {'domain': {'responsible_id': [
            ('id', 'in', self.qc_team_id.member_ids.ids)]}}

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'incident.report') or _('New')
        return super(IncidentReport, self).create(vals)

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        self.write({
            'state': 'confirm'})

    @api.multi
    def action_inprogress(self):
        self.ensure_one()
        self.write({
            'state': 'in_progress'})

    @api.multi
    def action_done(self):
        self.ensure_one()
        self.write({
            'state': 'done', 'end_date': fields.Datetime.now()})

    @api.multi
    def unlink(self):
        for inc in self:
            if inc.state == 'done':
                raise UserError(_('You can not delete Incident Report which '
                                  'is done'))
        return super(IncidentReport, self).unlink()
