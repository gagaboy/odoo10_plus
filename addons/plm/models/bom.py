# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.multi
    def _get_old_versions(self):
        self.ensure_one()
        parent = self.parent_bom
        old_version = self.env['mrp.bom']
        while parent:
            old_version += parent
            parent = parent.parent_bom
        self.old_versions = old_version

    @api.multi
    def _compute_engineering_change_order_data(self):
        self.ensure_one()
        self.total_change_order = len(self.change_order_ids)

    name = fields.Char(string='Name',
                       states={'historical': [('readonly', True)]})
    code = fields.Char(string='Code',
                       states={'historical': [('readonly', True)]})
    total_change_order = fields.Integer('Total Change Orders',
                       compute='_compute_engineering_change_order_data')
    change_order_ids = fields.One2many(
        'engineering.change.order', 'bom_id', 'ECO to be applied')
    active = fields.Boolean(default=False, readonly=True,
                            states={'draft': [('readonly', False)]})
    historical_date = fields.Date(string='Historical Date ', readonly=True)
    parent_bom = fields.Many2one('mrp.bom', string='Parent BoM ', copy=False)
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'),
                              ('historical', 'Historical')], string='State ',
                             index=True, readonly=True, default='draft',
                             copy=False)
    version = fields.Integer(states={'historical': [('readonly', True)]},
                             copy=False, default=1)
    old_versions = fields.Many2many('mrp.bom', string='Old Versions ',
                                    compute='_get_old_versions')
    product_tmpl_id = fields.Many2one(
        readonly=True, states={'draft': [('readonly', False)]})
    change_order_type = fields.Selection(
        [('permanent', 'Permanent'),
         ('temporary', 'Temporary'),
         ('new_product_intro', 'New Product Introduction')],
        string='Type')

    @api.onchange('product_tmpl_id')
    def product_template_change(self):
        if self.product_tmpl_id:
            self.product_uom_id = self.product_tmpl_id.uom_id.id
            self.name = self.product_tmpl_id.name

    @api.multi
    def action_engineering_change_order(self):
        self.ensure_one()
        change_orders = self.env['engineering.change.order'].search(
            [('bom_id', '=', self.id)])
        action = self.env.ref(
            'plm.engineering_change_order_action_main').read()[0]
        if len(change_orders) > 1:
            action['domain'] = [('id', 'in', change_orders.ids)]
        elif len(change_orders) == 1:
            action['views'] = [
                (self.env.ref('plm.engineering_change_order_view_form').id,
                 'form')]
            action['res_id'] = change_orders.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def button_draft(self):
        self.ensure_one()
        self.write({
            'active': False,
            'state': 'draft',
        })

    @api.multi
    def button_activate(self):
        self.ensure_one()
        self.write({
            'active': True,
            'state': 'active'
        })

    @api.multi
    def _copy_bom(self):
        self.ensure_one()
        new_bom = self.copy({
            'version': self.version + 1,
            'active': False,
            'parent_bom': self.id,
            'name': str(self.product_tmpl_id.name) + "[" + str(
                self.version + 1) + "]"
        })
        return new_bom

    @api.multi
    def button_historical(self):
        self.ensure_one()
        self.write({
            'active': False,
            'state': 'historical',
            'historical_date': fields.Date.today()
        })

    @api.multi
    def button_new_version(self):
        self.ensure_one()
        new_bom = self._copy_bom()
        self.button_historical()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form, tree',
            'view_mode': 'form',
            'res_model': 'mrp.bom',
            'res_id': new_bom.id,
            'target': 'current',
        }
