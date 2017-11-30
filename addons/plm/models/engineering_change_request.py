# Part of Flectra. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from flectra import api, fields, models, SUPERUSER_ID, _
from flectra.exceptions import UserError, ValidationError


class EngineeringChangeRequestAcceptance(models.Model):
    _name = 'engineering.change.request.acceptance'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'ir.attachment']

    ecr_id = fields.Many2one('engineering.change.request', string="ECR")
    name = fields.Selection([('reviewer', 'Reviewer'),
                             ('approver', 'Approver')], required=True,
                            string="Role")
    user_id = fields.Many2one(
        'res.users', 'User', track_visibility='always')
    date = fields.Datetime(string="Date ")
    action = fields.Selection([('review', 'Review'), ('approve', 'Approve'),
                               ('reject', 'Reject')])
    category_ids = fields.Many2many('plm.category', string="Category")
    reason_id = fields.Many2one('plm.reason', string="Reason")
    reason = fields.Text(string="Remarks")
    active_reviewer = fields.Boolean(string="Active Reviewer ",
                                     compute='_active_user')
    active_approver = fields.Boolean(string="Active Approver ",
                                     compute='_active_user')

    @api.depends('user_id')
    def _active_user(self):
        user = self.env.user.id
        for rec in self:
            if rec.name == 'reviewer' and rec.user_id.id == user or \
                    user == SUPERUSER_ID:
                rec.active_reviewer = True
            if rec.name == 'approver' and rec.user_id.id == user or \
                    user == SUPERUSER_ID:
                rec.active_approver = True


class EngineeringChangeRequest(models.Model):
    _name = 'engineering.change.request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'ir.attachment']

    name = fields.Char(string='ECR No.', required=True,
                       copy=False, readonly=True,
                       states={'draft': [('readonly', False)]},
                       default=lambda self: _('New'))
    requested_by = fields.Many2one('res.users', string="Requested By ",
                                   required=True,
                                   default=lambda self: self.env.user,
                                   track_visibility='always')
    manufacture_order = fields.Many2one('mrp.production',
                                        string="Manufacturing Order",
                                        store=True)
    sale_id = fields.Many2one('sale.order', string="Sale Order", store=True,
                              domain=[('name',
                                       '=', 'manufacture_order.sale_id.name')])
    ecr_date = fields.Datetime(string="Date", default=datetime.today())
    dwg_no = fields.Char(string="Dwg. No.")
    type = fields.Selection([('permanent', 'Permanent'),
                             ('temporary', 'Temporary'),
                             ('new_product_intro',
                              'New Product Introduction')],
                            string='Type', default='permanent')
    production_status = fields.Selection([('manufacture_order_on_hold',
                                           'Manufacturing Order On Hold'),
                                          ('production_on_hold',
                                           'Production On Hold')],
                                         string='Production Status ')
    description_request = fields.Text(string="Description")
    reason_request = fields.Text(string="Reason For Request")
    comments = fields.Text(string="Comments ")
    activation = fields.Selection([('directly', 'As soon as possible'),
                                    ('at_date', 'At Date')])
    company_id = fields.Many2one('res.company', string="Company",
                                 default=lambda self: self.env['res.company']
                                 ._company_default_get('sale.order'))
    category_ids = fields.Many2many('plm.category', string="Categories")
    priority = fields.Selection([('normal', 'NORMAL'), ('urgent', 'URGENT'),
                                 ('externaly_urgent', 'EXTREMELY URGENT')])
    approval_ids = fields.One2many('engineering.change.request.acceptance', 'ecr_id', 'Approvals',
                                   help='Approvals by stage',
                                   track_visibility='always')
    product_id = fields.Many2one('product.product', string="Product",
                                 required=True)
    product_tmpl_id = fields.Many2one('product.template',
                                      related='product_id.product_tmpl_id',
                                      string="Product", required=True)
    effective_date = fields.Date(string="Effective Date ")
    total_change_order = fields.Integer('# ECOs', compute='_compute_engineering_change_order_data')
    change_order_ids = fields.One2many('engineering.change.order', 'ecr_id', 'ECO to be applied')
    reviewed_boolean = fields.Boolean(string="Reviewed")
    approved_boolean = fields.Boolean(string="Approved")
    color = fields.Integer(compute='_check_color', string="Color")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'),
                              ('reviewed', 'Reviewed'),
                              ('approved', 'Approved'),
                              ('rejected', 'Rejected'),
                              ('cancel', 'Cancelled')], string='Status',
                             track_visibility='always', default='draft')

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'draft':
            return 'plm.mt_ecr_create'
        elif 'state' in init_values and self.state == 'reviewed':
            return 'plm.mt_plm_review'
        elif 'state' in init_values and self.state == 'approved':
            return 'plm.mt_plm_approve'
        elif 'state' in init_values and self.state == 'rejected':
            return 'plm.mt_plm_reject'
        return super(EngineeringChangeRequest, self)._track_subtype(init_values)

    @api.multi
    def _check_color(self):
        for record in self:
            res = {'draft': 1,
                   'confirm': 11,
                   'reviewed': 2,
                   'approved': 3,
                   }
            record.color = res.get(record.state, False)

    @api.multi
    def _compute_engineering_change_order_data(self):
        eco_data = self.env['engineering.change.order'].read_group([
            ('product_tmpl_id', 'in', self.mapped('product_tmpl_id').ids),
            ('state', '=', 'in_progress')],
            ['product_tmpl_id'], ['product_tmpl_id'])
        result = dict((data['product_tmpl_id'][0],
                       data['product_tmpl_id_count']) for data in eco_data)
        for bom in self:
            bom.total_change_order = len(bom.change_order_ids)
            bom.eco_inprogress_count = result.get(bom.product_tmpl_id.id, 0)

    @api.multi
    def change_state_review(self):
        self.ensure_one()
        self.reviewed_boolean = False
        reviewed_ids = len(self.approval_ids.search([
            ('ecr_id', '=', self.id), ('action', '=', 'review')]))
        total_reviewer_ids = len(self.approval_ids.search([
            ('ecr_id', '=', self.id), ('name', '=', 'reviewer')]))
        if total_reviewer_ids == reviewed_ids or \
                self.env.user.id == SUPERUSER_ID:
            self.write({'state': 'reviewed',
                        'reviewed_boolean': True})

    @api.multi
    def change_state_approve(self):
        self.ensure_one()
        self.approved_boolean = False
        approved_ids = len(self.approval_ids.search([
            ('ecr_id', '=', self.id), ('action', '=', 'approve')]))
        total_approver_ids = len(self.approval_ids.search([
            ('ecr_id', '=', self.id), ('name', '=', 'approver')]))
        if total_approver_ids == approved_ids or \
                self.env.user.id == SUPERUSER_ID:
            self.write({'state': 'approved',
                        'approved_boolean': True})

    @api.multi
    def change_state_reject(self):
        self.ensure_one()
        rejected_ids = len(self.approval_ids.search([
            ('ecr_id', '=', self.id), ('action', '=', 'reject')]))
        total_reject_ids = len(self.approval_ids.search([
            ('ecr_id', '=', self.id), ('name', 'in', ['approver',
                                                      'reviewer'])]))
        if total_reject_ids == rejected_ids or \
                self.env.user.id == SUPERUSER_ID:
            self.write({'state': 'reject'})

    @api.multi
    def action_engineering_change_order(self):
        self.ensure_one()
        change_orders = self.env['engineering.change.order'].search(
            [('ecr_id', '=', self.id)])
        action = self.env.ref(
            'plm.engineering_change_order_action_main').read()[0]
        action['context'] = {
            'default_ecr_id': self.id,
            'default_product_tmpl_id': self.product_tmpl_id.id
        }
        if len(change_orders) > 1:
            action['domain'] = [('id', 'in', change_orders.ids)]
        elif len(change_orders) == 1:
            action['views'] = [
                (self.env.ref('plm.engineering_change_order_view_form').id,
                 'form')]
            action['res_id'] = change_orders.ids[0]
        return action

    @api.multi
    def action_send_for_confirm(self):
        self.ensure_one()
        self.create_approver()
        self.create_reviewer()
        self.write({'state': 'confirm'})

    @api.multi
    def create_reviewer(self):
        for category in self.category_ids:
            self.env['engineering.change.request.acceptance'].create({
                'name': 'reviewer',
                'user_id': category.reviewer.id,
                'ecr_id': self.id,
                'category_ids': [(6, 0, category.ids)]
            })
        return True

    @api.multi
    def create_approver(self):
        for category in self.category_ids:
            self.env['engineering.change.request.acceptance'].create({
                'name': 'approver',
                'user_id': category.approver.id,
                'ecr_id': self.id,
                'category_ids': [(6, 0, category.ids)]
            })
        return True

    @api.multi
    def action_cancel(self):
        self.ensure_one()
        self.approval_ids.unlink()
        self.write({'state': 'cancel'})

    @api.multi
    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft',
                    'reviewed_boolean': False,
                    'approved_boolean': False})

    @api.multi
    def action_reset_to_confirm(self):
        self.ensure_one()
        rejected = self.approval_ids.filtered(
            lambda user: user.action == 'reject')
        if rejected:
            for line in rejected:
                vals = {}
                if line.name == 'reviewer':
                    vals.update({'state': 'confirm'})
                if line.name == 'approver':
                    vals.update({'state': 'reviewed'})
                if vals:
                    self.write(vals)
            rejected.write({'action': None})

    @api.multi
    def unlink(self):
        for ecr in self:
            if ecr.state not in ('draft', 'cancel'):
                raise UserError(_('You can not delete a'
                                  'Confirmed ECR! Try to cancel it before.'))
        return super(EngineeringChangeRequest, self).unlink()

    @api.onchange('product_id', 'activation')
    def onchange_product_id(self):
        self.effective_date = None
        if self.product_id.produce_delay:
            ecr_date = fields.Datetime.from_string(self.ecr_date)
            self.effective_date = \
                ecr_date + timedelta(days=self.product_id.produce_delay)

    @api.onchange('manufacture_order')
    def onchange_manufacture_order(self):
        self.sale_id = None
        if self.manufacture_order.sale_id:
            self.sale_id = self.manufacture_order.sale_id.id

    @api.onchange('type')
    def onchange_type_id(self):
        self.production_status = self.type == 'permanent' and \
                                 'production_on_hold' or \
                                 'manufacture_order_on_hold'

    @api.constrains('ecr_date', 'effective_date')
    def ecr_date_greater(self):
        eff_date = self.effective_date
        if self.ecr_date and eff_date and eff_date <= self.ecr_date:
            raise ValidationError(
                _("Effectivity Date should be grater than ECR Date"))

    @api.constrains('requested_by', 'category_ids')
    def _check_requested_by(self):
        if self.requested_by:
            for category in self.category_ids:
                if not category.approver or not category.reviewer:
                    raise ValidationError(
                        _("Categories must have Approver and Reviewer."))
                if category.approver.id and self.requested_by.id and \
                        category.reviewer == self.requested_by:
                    raise ValidationError(
                        _("Requester and Approver or Reviewer of"
                          "Categories must be different users."))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']).next_by_code(
                    'engineering.change.request') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'engineering.change.request') or _('New')
        result = super(EngineeringChangeRequest, self).create(vals)
        return result


class Product(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = self.env['product.product'].search(
            ['|', ('route_ids', 'like', _('Make To Order')),
             ('route_ids', 'like', _('Manufacture'))])
        return recs.name_get()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    total_change_order = fields.Integer('Total Change Orders',
                                        compute='_compute_engineering_change_order_data')
    change_order_ids = fields.One2many('engineering.change.order', 'product_tmpl_id', 'ECOs')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = self.env['product.template'].search(
            ['|', ('route_ids', 'like', _('Make To Order')),
             ('route_ids', 'like', _('Manufacture'))])
        return recs.name_get()

    @api.multi
    def _compute_engineering_change_order_data(self):
        self.ensure_one()
        self.total_change_order = len(self.change_order_ids)
