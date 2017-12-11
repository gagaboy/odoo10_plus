# Part of Odoo S.A.,Flectra See LICENSE file for full copyright and
# licensing details.

import time

from flectra import api, fields, models
from flectra.exceptions import UserError
from flectra.tools.translate import _


class HrEmployee(models.Model):

    _inherit = "hr.employee"

    product_id = fields.Many2one("product.product", string="Product")
    journal_id = fields.Many2one("account.journal", string="Journal")


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    @api.multi
    def _calculate_amt_invoiced(self):
        amount = 0.0
        self._cr.execute('SELECT account_id as account_id, l.invoice_id '
                         'FROM hr_analytic_timesheet h '
                         'LEFT JOIN account_analytic_line l '
                         'ON (h.line_id=l.id) '
                         'WHERE l.account_id = ANY(%s)', (self.ids))

        invoice_check = {}
        for rec in self._cr.dictfetchall():
            invoice_check.setdefault(
                rec['account_id'], []).append(rec['invoice_id'])

        res = {}
        for account in self:
            invoice_ids = filter(None, list(
                set(invoice_check.get(account.id, []))))
            for invoice in self.env['account.invoice'].browse(invoice_ids):
                res.setdefault(account.id, 0.0)
                amount += invoice.amount_untaxed or 0.0
            account.amt_invoiced = round(amount, 2)

    date = fields.Date("Date ")
    use_timesheets = fields.Boolean("Use Timesheets ")
    use_tasks = fields.Boolean('Use Tasks ')
    to_invoice = fields.Many2one(
        'hr_activity_invoice.factor', string='Activity Invoicing Ratio')
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist')
    quantity_max = fields.Float("Prepaid Service Units")
    amt_max = fields.Float('Max. Invoice Price')
    amt_invoiced = fields.Float(
        compute=_calculate_amt_invoiced, string='Invoiced Amount',
        help="Total invoiced")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('pending', 'To Renew'),
        ('close', 'Closed'),
        ('cancelled', 'Cancelled')], string="Status", default="draft")

    @api.model
    def _trigger_project_creation(self, vals):
        return vals.get('use_tasks') and \
            'project_creation_in_progress' not in self.env.context

    @api.multi
    def project_create(self, vals):
        self.ensure_one()
        res = False
        project = self.env['project.project']
        project_search = project.with_context(active_test=False).search(
            [('analytic_account_id', '=', self.id)])
        if not project_search and self._trigger_project_creation(vals):
            res = project.create({
                'name': vals.get('name'),
                'analytic_account_id': self.id,
                'use_tasks': True,
            })
        return res and res.id or False

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.pricelist_id = self.partner_id and \
            self.partner_id.property_product_pricelist and \
            self.partner_id.property_product_pricelist.id or \
            False

    @api.multi
    def close(self):
        for account in self:
            account.state = 'close'

    @api.multi
    def cancel(self):
        for account in self:
            account.state = 'cancelled'

    @api.multi
    def open(self):
        for account in self:
            account.state = 'open'

    @api.multi
    def pending(self):
        for account in self:
            account.state = 'pending'


class HrActivityInvoiceFactor(models.Model):
    _name = "hr_activity_invoice.factor"
    _order = 'factor'

    customer_name = fields.Char('Name')
    name = fields.Char('Internal Name', translate=True)
    factor = fields.Float('Discount (%)', default=0.0)


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def _get_default_general_account(self):
        employee_id = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        if employee_id:
            if employee_id.product_id and employee_id.product_id.property_account_income_id:
                return employee_id.product_id.property_account_income_id.id
        return False

    @api.model
    def _get_default_journal(self):
        employee_id = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        if employee_id:
            journal_id = self.env['account.invoice'].default_get(
                ['journal_id'])['journal_id']
            return employee_id.journal_id and employee_id.journal_id.id or \
                journal_id or False
        return False

    to_invoice = fields.Many2one(
        'hr_activity_invoice.factor', string='Invoiceable')
    invoice_id = fields.Many2one(
        'account.invoice', string='Invoice', ondelete="set null")
    general_account_id = fields.Many2one(
        "account.account", string="Account",
        default=_get_default_general_account, ondelete='restrict')
    journal_id = fields.Many2one(
        "account.journal", string="Journal", default=_get_default_journal,
        ondelete="cascade")

    @api.onchange('account_id')
    def onchange_account_id(self):
        if self.account_id and self.account_id.state == 'pending':
            raise UserError(_('This account is in pending state.\
                \nYou can not work on this account !'))
        self.to_invoice = \
            self.account_id and \
            self.account_id.to_invoice and \
            self.account_id.to_invoice.id or False

    @api.multi
    def write(self, vals):
        self._check_if_invoiced(vals)
        return super(AccountAnalyticLine, self).write(vals)

    @api.multi
    def _check_if_invoiced(self, vals):
        if not vals.get('invoice_id', False):
            for analytic_line in self:
                if analytic_line.invoice_id:
                    raise UserError(
                        _('You can not modify an invoiced line!'))
        return True

    def _get_price(self, account, product_id, user_id, qty):
        inv_price = 0.0
        if account.pricelist_id:
            inv_price = self.env['product.pricelist'].price_get(
                product_id, qty or 1.0, account.partner_id.id)[
                account.pricelist_id.id]
        return inv_price

    def _cost_invoice_generate(self, partner, company_id, currency_id,
                               analytic_lines):
        last_date = False
        if partner.property_payment_term_id:
            payment_terms = self.env['account.payment.term'].compute(
                value=1, date_ref=time.strftime('%Y-%m-%d'))
            if payment_terms:
                payment_terms = [line[0] for line in payment_terms]
                payment_terms.sort()
                last_date = payment_terms[-1]

        return {
            'payment_term_id':
                partner and partner.property_payment_term_id and
                partner.property_payment_term_id.id or False,
            'partner_id': partner and partner.id or False,
            'account_id': partner.property_account_receivable_id and partner.property_account_receivable_id.id or False,
            'currency_id': currency_id,
            'company_id': company_id,
            'name': "%s - %s" % (time.strftime('%d/%m/%Y'),
                                 analytic_lines[0].account_id.name),
            'date_due': last_date,
            'fiscal_position_id':
                partner and
                partner.property_account_position_id and
                partner.property_account_position_id.id or False,
        }

    def _prepare_invoice_line_cost(
            self, invoice_id, product_id, uom, user_id, factor_id, account,
            analytic_lines, journal_type, data):

        quantity_total = sum(line.unit_amount for line in analytic_lines)
        price_unit = sum(line.amount for line in analytic_lines) * - \
            1.0 / quantity_total
        if data.get('product'):
            if isinstance(data.get('product'), (tuple, list)):
                product_id = data.get('product')[0]
            else:
                product_id = data.get('product')
            price_unit = self.with_context({'uom': uom})._get_price(
                account, product_id, user_id, quantity_total)
        elif journal_type == 'sale' and product_id:
            price_unit = self.with_context({'uom': uom})._get_price(
                account, product_id, user_id, quantity_total)

        invoice_factor = self.env['hr_activity_invoice.factor'].browse(
            factor_id)
        invoice_line = dict({
            'name': invoice_factor.customer_name or '',
            'quantity': quantity_total,
            'account_id': account and account.id or False,
            'product_id': product_id,
            'account_analytic_id': account and account.id or False,
            'discount': invoice_factor.factor,
            'price_unit': price_unit,
            'invoice_id': invoice_id and invoice_id.id or False,
            'uom_id': uom,
        })
        if product_id:
            product = self.env['product.product'].browse(product_id)
            factor_name = product.name_get()[0][1]
            if invoice_factor.customer_name:
                factor_name += ' - %s' % (invoice_factor.customer_name)
            general_account = product.property_account_income_id or \
                product.categ_id.property_account_income_categ_id
            if not general_account:
                msg = _("Income account for the \
                    product '{}' is missing...").format(product.name)
                raise UserError(msg)
            taxes = product.taxes_id or general_account.tax_ids
            tax = invoice_id.partner_id.property_account_position_id.map_tax(
                taxes)
            vals = dict({
                'account_id': general_account.id,
                'invoice_line_tax_ids': [(6, 0, tax.ids)],
                'name': factor_name,
            })
            invoice_line.update(vals)

            note = []
            for analytic_line in analytic_lines:
                details = []
                if data.get('date', False):
                    details.append(analytic_line['date'])
                if data.get('time', False):
                    if analytic_line['product_uom_id']:
                        details.append("%s %s" % (
                            analytic_line.unit_amount,
                            analytic_line.product_uom_id.name))
                    else:
                        details.append("%s" % (analytic_line['unit_amount'], ))

                if data.get('name', False):
                    details.append(analytic_line['name'])
                if details:
                    note.append(
                        u' - '.join(map(lambda x: x or '', details)))
            if note:
                invoice_line['name'] += "\n" + \
                    ("\n".join(map(lambda x: x or '', note)))
        return invoice_line

    def create_invoice_cost(self, line_ids, data):
        invoices = []
        invoice_res, invoice_lines_res = {}, {}
        currency_id = False

        for line in self.browse(line_ids):
            key = (
                line.account_id.id,
                line.account_id.company_id.id,
                line.account_id.pricelist_id and
                line.account_id.pricelist_id.currency_id.id or
                line.account_id.company_id.currency_id.id)
            invoice_res.setdefault(key, []).append(line)

        for (key_id, company_id, currency_id), analytic_lines in \
                invoice_res.items():
            account = analytic_lines[0].account_id
            partner = account.partner_id
            if not (partner or currency_id):
                raise UserError(_("Contract '%s' is Incomplete. \
                    Customer and Currency are required.") % (account.name))

            current_invoice = self._cost_invoice_generate(
                partner, company_id, currency_id, analytic_lines)

            last_invoice = self.env['account.invoice'].with_context({
                'lang': partner.lang,
                'company_id': company_id,
                'force_company': company_id,
            }).create(current_invoice)
            invoices.append(last_invoice.id)

            for line in analytic_lines:
                account = line.account_id
                if not line.to_invoice:
                    raise UserError(_(
                        'Invoice can\'t be created for non-invoiceable \
                            line for %s.') % (line.product_id.name))

                key = (line.product_id.id, line.product_uom_id.id,
                       line.user_id.id, line.to_invoice.id,
                       line.account_id, line.journal_id.type)

                invoice_lines_res.setdefault(key, []).append(line)

            for (product_id, uom, user_id, factor_id, account,
                    journal_type), lines_to_invoice \
                    in invoice_lines_res.items():
                if not product_id:
                    sp_id = self.product_id.search([
                        ('name', 'ilike', 'Support')
                    ])
                    if sp_id and not uom:
                        uom = sp_id.uom_id.id or False
                        product_id = sp_id.id

                current_invoice_line = self._prepare_invoice_line_cost(
                    last_invoice, product_id, uom, user_id, factor_id,
                    account, lines_to_invoice, journal_type, data)
                self.env['account.invoice.line'].create(current_invoice_line)

            for line in analytic_lines:
                line.invoice_id = last_invoice.id

            last_invoice.compute_taxes()
        return invoices


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.multi
    def create_analytic_lines(self):
        res = super(AccountMoveLine, self).create_analytic_lines()
        for line in self:
            invoice_id = line.invoice_id and line.invoice_id.type \
                in ('out_invoice', 'out_refund') and \
                line.invoice_id.id or False
            for analytic_line in line.analytic_line_ids:
                analytic_line.invoice_id = invoice_id
                analytic_line.to_invoice = analytic_line.account_id.to_invoice\
                    and analytic_line.account_id.to_invoice.id or False
        return res
