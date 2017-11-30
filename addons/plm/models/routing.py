# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    @api.multi
    def _get_old_versions(self):
        self.ensure_one()
        parent = self.parent_routing
        old_version = self.env['mrp.routing']
        while parent:
            old_version += parent
            parent = parent.parent_routing
        self.old_versions = old_version

    name = fields.Char(
        states={'historical': [('readonly', True)]})
    sequence = fields.Integer('Sequence ',
                              help="Gives the sequence order "
                                   "when displaying a list of "
                                   "routing.")
    change_order_ids = fields.One2many('engineering.change.order', 'latest_routing_id', 'ECOs')
    total_change_order = fields.Integer('Total Change Orders',
                                        compute='_compute_engineering_change_order_data')
    parent_routing = fields.Many2one('mrp.routing', string='Parent BoM',
                                     copy=False)
    active = fields.Boolean(readonly=True, default=False,
                            states={'draft': [('readonly', False)]})
    historical_date = fields.Date(string='Historical Date ', readonly=True)
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('active', 'Active'),
                   ('historical', 'Historical')], string='State ',
        index=True, readonly=True, default='draft', copy=False)
    version = fields.Integer(states={'historical': [('readonly', True)]},
                             copy=False, default=1)
    old_versions = fields.Many2many('mrp.routing', string='Old Versions ',
                                    compute='_get_old_versions')
    change_order_type = fields.Selection(
        [('permanent', 'Permanent'), ('temporary', 'Temporary'),
         ('new_product_intro', 'New Product Introduction')], string='Type')

    @api.multi
    def _compute_engineering_change_order_data(self):
        self.ensure_one()
        self.total_change_order = len(self.change_order_ids)

    @api.multi
    def action_engineering_change_order(self):
        self.ensure_one()
        change_orders = self.env['engineering.change.order'].search(
            [('latest_routing_id', '=', self.id)])
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
    def button_new_version(self):
        self.ensure_one()
        new_routing = self._copy_routing()
        self.button_historical()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form, tree',
            'view_mode': 'form',
            'res_model': 'mrp.routing',
            'res_id': new_routing.id,
            'target': 'current',
        }

    @api.multi
    def _copy_routing(self):
        self.ensure_one()
        new_routing = self.copy({
            'version': self.version + 1,
            'active': False,
            'name': str(self.name) + "[" + str(self.version + 1) + "]",
        })
        return new_routing

    @api.multi
    def button_activate(self):
        self.ensure_one()
        self.write({
            'active': True,
            'state': 'active'
        })

    @api.multi
    def button_historical(self):
        self.ensure_one()
        self.write({
            'active': False,
            'state': 'historical',
            'historical_date': fields.Date.today()
        })
