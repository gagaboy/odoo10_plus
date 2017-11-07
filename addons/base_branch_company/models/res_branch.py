# -*- coding: utf-8 -*-

from flectra import api, fields, models


class ResBranch(models.Model):
    _name = "res.branch"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    active = fields.Boolean(string='Active', default=True)
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', string="Company",
        default=lambda self: self.env.user.company_id, required=True)
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State',
                               ondelete='restrict')
    country_id = fields.Many2one('res.country', string='Country',
                                 ondelete='restrict')
    email = fields.Char()
    phone = fields.Char()
    mobile = fields.Char()

    _sql_constraints = [('branch_code_company_uniq', 'unique (code,company_id)',
                         'The branch code must be unique per company!')]

    @api.model
    def create(self, vals):
        partner_id = self.env['res.partner'].create({'name': vals['name']})
        vals.update({'partner_id': partner_id.id})
        res = super(ResBranch, self).create(vals)
        vals.pop("name", None)
        vals.pop("code", None)
        vals.pop("partner_id", None)
        vals.update({'branch_id': res.id})
        partner_id.write(vals)
        return res

    @api.multi
    def write(self, vals):
        res = super(ResBranch, self).write(vals)
        vals.pop("name", None)
        vals.pop("code", None)
        ctx = self.env.context.copy()
        if 'branch' not in ctx:
            self.partner_id.write(vals)
        return res


class Users(models.Model):

    _inherit = "res.users"

    @api.model
    def branch_default_get(self, user):
        if not user:
            user = self._uid
        return self.env['res.users'].browse(user).default_branch_id

    @api.model
    def _get_default_branch(self):
        return self.branch_default_get(self._uid)

    branch_ids = fields.Many2many('res.branch',
                                  'res_barnch_users_rel',
                                  'user_id',
                                  'branch_id',
                                  'Branches')
    default_branch_id = fields.Many2one('res.branch', 'Default branch',
                                        default=_get_default_branch,
                                        domain="[('company_id','=',company_id)"
                                               "]")


class Partner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "ir.branch.company.mixin"]

    @api.multi
    def write(self, vals):
        field_list = ['street', 'street2', 'zip', 'city', 'state_id',
                      'country_id', 'email', 'phone', 'mobile']
        branch_vals = dict((f, vals[f]) for f in field_list if f in vals)
        if branch_vals and self.branch_id:
            ctx = self.env.context.copy()
            ctx.update({'branch': True})
            self.branch_id.with_context(ctx).write(branch_vals)
        result = super(Partner, self).write(vals)
        return result



