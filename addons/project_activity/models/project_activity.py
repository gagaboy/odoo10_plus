# Part of Flectra See LICENSE file for full copyright and licensing details.

from flectra import fields, models, api, _
from flectra.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def unlink(self):
        parnters = self.env['project.project'].search(
            [('partner_id', 'in', self.ids)])
        if parnters:
            raise UserError(_('Invalid Action! \n'
                              'Unable to delete project partner'))
        return super(ResPartner, self).unlink()


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.multi
    def get_activities(self):
        action = self.env.ref('hr_timesheet.act_hr_timesheet_line_by_project')
        view = self.env.ref('hr_timesheet.hr_timesheet_line_tree')
        return {
            'name': _('Activities'),
            'help': action.help,
            'type': action.type,
            'views': [[view.id, 'tree']],
            'target': action.target,
            'context': {
                'search_default_account_id': [self.analytic_account_id.id],
                'default_account_id': self.analytic_account_id.id},
            'res_model': action.res_model,
        }

    @api.onchange('partner_id')
    def on_partner_id_change(self):
        if self and self.partner_id:
            # set Invoiceable = 100%
            self.to_invoice = self.env.ref(
                'hr_activity_invoice.activity_factor_1') or False


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    product_id = fields.Many2one(
        'product.product', string='Product',
        default=lambda self: self.env['hr.employee'].search(
            [('user_id', '=', self._uid)], limit=1).product_id)

    @api.onchange('account_id')
    def on_account_id_change(self):
        if self.account_id:
            if self.account_id.state in ['close', 'cancelled']:
                raise UserError(_('Invalid Account! '
                                  '\nAccount selected is not active.'))
            self.to_invoice = self.account_id.to_invoice.id or False

    @api.v8
    @api.onchange('product_id', 'product_uom_id', 'unit_amount', 'currency_id')
    def on_change_unit_amount(self):
        result = super(AccountAnalyticLine, self).on_change_unit_amount()
        if not self.move_id and not self.amount:
            currency = self.company_id and self.company_id.currency_id or \
                       self.account_id and self.account_id.company_id and \
                       self.account_id.company_id.currency_id or False
            unit = self.product_uom_id
            price = self.product_id.price_compute(
                'standard_price', uom=unit)
            amount_unit = price and price[self.product_id.id] or 0.0
            self.amount = currency and currency.round(
                    (amount_unit * self.unit_amount) or 0.0) * -1 or 0.0
        return result

    @api.model
    def create(self, vals):
        res_config = self.env['res.config.settings'].search(
            [], limit=1, order="id DESC")
        user_wise_product = \
            res_config and res_config.module_analytic_user_function
        if vals.get('account_id'):
            account = self.env['account.analytic.account'].browse(
                vals.get('account_id'))
            product = user_wise_product and account and \
                account.user_product_ids and \
                account.user_product_ids.filtered(
                  lambda account: account.user_id.id == vals.get(
                      'user_id')).mapped('product_id') or False
            if product:
                vals.update({'product_id': product and product.id})
        elif vals.get('task_id'):
            account = self.env['project.task'].browse(
                vals['task_id']).project_id.analytic_account_id
            vals['account_id'] = account and account.id
            product = user_wise_product and account and \
                account.user_product_ids and \
                account.user_product_ids.filtered(
                  lambda account: account.user_id.id == vals.get(
                      'user_id')).mapped('product_id') or False
            if product:
                vals.update({'product_id': product and product.id})
        res = super(AccountAnalyticLine, self).create(vals)
        res.on_account_id_change()
        if not res.move_id:
            res.on_change_unit_amount()
        return res


class Task(models.Model):
    _inherit = "project.task"

    @api.multi
    def unlink(self):
        for task in self:
            if task.timesheet_ids:
                task.timesheet_ids.unlink()
        return super(Task, self).unlink()

    @api.onchange('project_id')
    def _onchange_project(self):
        super(Task, self)._onchange_project()
        if self.project_id:
            self.company_id = self.project_id.company_id and self.project_id.company_id.id or False
