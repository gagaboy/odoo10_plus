# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _
from flectra.exceptions import UserError, ValidationError


class EngineeringChangeOrder(models.Model):
    _name = 'engineering.change.order'
    _description = 'Engineering Change Order'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin',
                'ir.attachment']

    name = fields.Char(string='Name', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    ecr_id = fields.Many2one('engineering.change.request', string="ECR")
    ecr_date = fields.Date(string="ECR Date")
    ecr_requester = fields.Char(string="ECR Requester")
    type = fields.Selection([('permanent', 'Permanent'),
                             ('temporary', 'Temporary'),
                             ('new_product_intro',
                              'New Product Introduction')],
                            string='Type', default='permanent')
    user_id = fields.Many2one('res.users', 'Responsible',
                              default=lambda self: self.env.user,
                              track_visibility='always')
    description = fields.Text(string='Description')
    activation = fields.Selection([('directly', 'At the Earliest'),
                                   ('manual', 'Manual')],
                                  string='Activation ',
                                  compute='_adjust_activation',
                                  inverse='_activation_date', store=True)
    activated_on = fields.Date('Activation Date ',
                               track_visibility='always',
                               help="For reference only.", store=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('in_progress', 'In Progress'),
                              ('done', 'Done')], track_visibility='always',
                             default='draft', string='Status')
    product_tmpl_id = fields.Many2one('product.template',
                                      string="Product ", required=True)
    active = fields.Boolean('Active ', default=True,
                            help="If the active field is set to False, it"
                                 "will allow you to hide the engineering"
                                 "change order without removing it.")
    applicability = fields.Selection([('bom', 'Bill of Materials'),
                                      ('routing', 'Routing'),
                                      ('both', 'BoM and Routing')],
                                     string='Applicability', default='bom',
                                     track_visibility='always', required=True)
    latest_routing_id = fields.Many2one('mrp.routing', 'New Routing',
                                     track_visibility='always',
                                     copy=False)
    routing_id = fields.Many2one('mrp.routing', "Routing")
    bom_id = fields.Many2one('mrp.bom', "BOM",
                             track_visibility='always')
    color = fields.Integer('Color Index', default=1)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.user.company_id)

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'draft':
            return 'plm.mt_engineering_change_order_create'
        return super(EngineeringChangeOrder, self)._track_subtype(init_values)

    @api.constrains('ecr_date', 'activated_on')
    def ecr_date_greater(self):
        eff_date = self.activated_on
        if self.ecr_date and eff_date and eff_date <= self.ecr_date:
            raise ValidationError(
                _("Effectivity Date Should be greater than ECR Date"))

    @api.onchange('ecr_id')
    def onchange_ecr_id(self):
        if self.ecr_id:
            self.ecr_date = self.ecr_id.ecr_date or False
            self.ecr_requester = self.ecr_id.requested_by.name
            self.product_tmpl_id = self.ecr_id.product_id.product_tmpl_id.id
            self.type = self.ecr_id.type or False
            self.activated_on = self.ecr_id.effective_date or False

    @api.depends('activated_on')
    def _adjust_activation(self):
        for eco in self:
            eco.activation = 'manual' if eco.activated_on else 'directly'

    def _activation_date(self):
        for eco in self:
            if eco.activation == 'directly':
                eco.activated_on = False

    @api.onchange('product_tmpl_id')
    def product_template_change(self):
        if self.product_tmpl_id.bom_ids:
            self.bom_id = self.product_tmpl_id.bom_ids and \
                          self.product_tmpl_id.bom_ids.ids[0] or False

    @api.onchange('bom_id', 'applicability')
    def bom_applicability_change(self):
        if self.applicability == 'both':
            self.routing_id = self.bom_id.routing_id

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']).next_by_code('engineering.change.order') \
                               or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'engineering.change.order') or _('New')
        result = super(EngineeringChangeOrder, self).create(vals)
        return result

    @api.multi
    def unlink(self):
        for eco in self:
            if eco.state not in ('draft', 'cancel'):
                raise UserError(_('You can not delete a Confirmed ECO!'
                                  'Try to cancel it before.'))
        return super(EngineeringChangeOrder, self).unlink()

    @api.multi
    def action_in_progress(self):
        self.ensure_one()
        self.write({'state': 'in_progress'})

    @api.multi
    def action_done(self):
        self.ensure_one()
        self.write({'state': 'done'})

    @api.multi
    def action_view_bill_of_materials(self):
        self.ensure_one()
        bom_id = self.env['mrp.bom'].search([('active', '=', True),
                                             ('product_tmpl_id', '=',
                                              self.product_tmpl_id.id)],
                                            limit=1)
        if not bom_id:
            return True
        result = {'name': _('Engineering Change Order BoM'),
                  'type': 'ir.actions.act_window',
                  'view_type': 'form',
                  'view_mode': 'form',
                  'res_model': 'mrp.bom',
                  'target': 'current',
                  'res_id': False}
        if self.type == 'permanent':
            result.update({'res_id': bom_id.id})
        else:
            new_bom = self.bom_id.copy({
                'active': False,
                'parent_bom': self.bom_id.id,
                'change_order_type': self.type,
                'code': self.ecr_id.manufacture_order.name,
                'version': self.bom_id.version or False
            })
            result.update({'res_id': new_bom.id})
        return result

    @api.multi
    def change_order_routing_details(self):
        self.ensure_one()
        result = {
            'name': _('Engineering Change Order Routing'),
            'res_model': 'mrp.routing',
            'res_id': False,
            'target': 'current',
            'view_type': 'form',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
        }
        if self.type == 'permanent':
            result.update({'res_id': self.latest_routing_id.id})
        else:
            latest_routing_id = self.latest_routing_id.copy({
                'active': False,
                'change_order_type': self.type
            })
            result.update({'res_id': latest_routing_id.id})
        return result
