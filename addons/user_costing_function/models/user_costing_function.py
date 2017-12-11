# Part of Flectra See LICENSE file for full copyright and licensing details.

import flectra.addons.decimal_precision as dp
from flectra import api, fields, models
from flectra.exceptions import ValidationError
from flectra.tools.translate import _


class UserCostingFunction(models.Model):
    _name = "user.costing.function"
    _description = "Costing Price per User"
    _rec_name = "user_id"

    user_id = fields.Many2one("res.users", string="User", required=True)
    cost = fields.Float('Cost Price',
                        digits=dp.get_precision('Product Price'))
    product_id = fields.Many2one("product.product", string="Service")
    account_id = fields.Many2one("account.analytic.account",
                                 string="Analytic Account")
    uom_id = fields.Many2one(related='product_id.uom_id',
                             string="Unit of Measure")

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.user_id:
            emp_id = self.env['hr.employee'].search(
                [('user_id', '=', self.user_id.id)], limit=1)
            prod = emp_id.product_id or self.product_id
            self.cost = prod.list_price or 0.0
            self.uom_id = prod.uom_id.id or False


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    user_costing_ids = fields.One2many('user.costing.function', 'account_id',
                                       string='Users/Products Rel.', copy=True)


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    def _get_price(self, account, product_id, user_id, qty):
        res = super(AccountAnalyticLine, self)._get_price(
            account, product_id, user_id, qty)
        if not account.user_costing_ids:
            return res
        for user_costing_id in account.user_costing_ids:
            if user_costing_id.user_id.id == user_id:
                return user_costing_id.cost
        return res

    @api.v8
    @api.onchange('product_id', 'product_uom_id', 'unit_amount', 'currency_id')
    def on_change_unit_amount(self):
        result = super(AccountAnalyticLine, self).on_change_unit_amount()
        if not self.move_id and not self.task_id:
            unit = self.product_uom_id
            price = self.product_id.price_compute(
                'standard_price', uom=unit)
            currency = \
                self.company_id.currency_id or \
                self.account_id.company_id.currency_id or False
            amount_unit = price and price[self.product_id.id] or 0.0
            for user_costing_id in self.account_id.user_costing_ids:
                if user_costing_id.user_id.id == self.user_id.id:
                    amount_unit = user_costing_id.cost
            self.amount = currency and currency.round(
                (amount_unit * self.unit_amount) or 0.0) * -1
        return result

    def _get_recursive_user_account(self, user_id, account_id):
        user_account = self.env['user.costing.function'].search(
            [('user_id', '=', user_id.id), ('account_id', '=', account_id.id)])
        if user_account:
            return user_account
        else:
            if account_id.parent_id:
                return self._get_recursive_user_account(
                    user_id, account_id.parent_id.id)
            return False

    @api.multi
    def set_account_details(self, product):
        self.product_id = product.id
        account_expense = \
            product.property_account_expense_id.id or \
            product.categ_id.property_account_expense_categ_id.id
        if not account_expense:
            raise ValidationError(_(
                'Warning!\nPlease define expense account for'
                'product: "%s" (id:%d)') % (product.name, product.id,))
        if self.unit_amount:
            self.on_change_unit_amount()
        self.general_account_id = account_expense

    @api.onchange('user_id')
    def on_user_id_change(self):
        if self.account_id:
            user_account = self._get_recursive_user_account(
                self.user_id, self.account_id)
            if user_account:
                product = user_account.product_id
                self.set_account_details(product)

    @api.onchange('account_id')
    def onchange_account_id(self):
        if self.account_id:
            if not self.user_id:
                return super(AccountAnalyticLine, self).onchange_account_id()
            user_account = self._get_recursive_user_account(
                self.user_id, self.account_id)
            if not user_account:
                return super(AccountAnalyticLine, self).onchange_account_id()
            else:
                product = user_account.product_id
                self.product_uom_id = product.uom_id.id
                self.set_account_details(product)
