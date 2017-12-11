# Part of Flectra S.A.,Flectra See LICENSE file for full copyright and
# licensing details.

import datetime
from dateutil.relativedelta import relativedelta
import logging
import time

from flectra import api, fields, models, tools, _
import flectra.addons.decimal_precision as dp
from flectra.exceptions import UserError, Warning, ValidationError

_logger = logging.getLogger(__name__)


class AnalyticSummaryMonth(models.Model):
    _name = "analytic.summary.month"
    _rec_name = 'month_name'
    _auto = False

    month_name = fields.Char(string='Month', size=24, readonly=True)
    amount = fields.Float(string='Total Time')
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account', readonly=True)

    @api.model_cr
    def init(self):
        cr = self._cr
        tools.drop_view_if_exists(
            cr, 'analytic_summary_month')
        cr.execute(
            'CREATE VIEW analytic_summary_month AS ('
            'SELECT '
            '(TO_NUMBER(TO_CHAR(d.month, \'YYYYMM\'), \'999999\') + ('
            'd.account_id  * 1000000::bigint))::bigint AS id, '
            'd.account_id AS account_id, '
            'TO_CHAR(d.month, \'Mon YYYY\') AS month, '
            'TO_NUMBER(TO_CHAR(d.month, \'YYYYMM\'), \'999999\') AS month_id, '
            'COALESCE(SUM(l.unit_amount), 0.0) AS unit_amount '
            'FROM (SELECT d2.account_id, d2.month FROM '
            '(SELECT a.id AS account_id, l.month AS month '
            'FROM (SELECT DATE_TRUNC(\'month\', l.date) AS month '
            'FROM account_analytic_line AS l, '
            'account_journal AS j '
            'WHERE j.type = \'sale\' '
            'GROUP BY DATE_TRUNC(\'month\', l.date) '
            ') AS l, '
            'account_analytic_account AS a '
            'GROUP BY l.month, a.id '
            ') AS d2 '
            'GROUP BY d2.account_id, d2.month '
            ') AS d '
            'LEFT JOIN '
            '(SELECT l.account_id AS account_id, '
            'DATE_TRUNC(\'month\', l.date) AS month, '
            'SUM(l.unit_amount) AS unit_amount '
            'FROM account_analytic_line AS l, '
            'account_journal AS j '
            'WHERE (j.type = \'sale\') and (j.id=l.journal_id) '
            'GROUP BY l.account_id, DATE_TRUNC(\'month\', l.date) '
            ') AS l '
            'ON ('
            'd.account_id = l.account_id '
            'AND d.month = l.month'
            ') '
            'GROUP BY d.month, d.account_id '
            ')')


class AnalyticSummaryUser(models.Model):
    _name = "analytic.summary.user"
    _rec_name = 'user_id'
    _auto = False
    _order = 'user_id'

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'analytic_summary_user')
        self._cr.execute('''
            CREATE OR REPLACE VIEW analytic_summary_user AS (with mu as
                (select max(id) as max_user from res_users)
            , lu AS(SELECT l.account_id AS account_id,
                 coalesce(l.user_id, 0) AS user_id,
                 SUM(l.unit_amount) AS unit_amount
             FROM account_analytic_line AS l, account_journal AS j
             WHERE (j.type = 'sale' ) and (j.id=l.journal_id)
             GROUP BY l.account_id, l.user_id)
            select (lu.account_id::bigint * mu.max_user) + lu.user_id as id,
                    lu.account_id as account_id,
                    lu.user_id as "user_id",
                    unit_amount from lu, mu)''')

    @api.multi
    def _compute_unit_amount(self):
        self._cr.execute('SELECT MAX(id) FROM res_users')
        m_usr = self._cr.fetchone()[0]

        ac_ids = []
        for y in self.ids:
            temp = int(str(y / m_usr - (y % m_usr == 0 and 1 or 0)))
            ac_ids.append(temp)

        usr_ids = []
        for y in self.ids:
            usr_ids.append(
                int(str(
                    y - ((y / m_usr - (y % m_usr == 0 and 1 or 0)) * m_usr))))

        for record in self:
            self._cr.execute(
                'SELECT id, amount'
                'FROM analytic_summary_user'
                'WHERE analytic_account_id IN %s '
                'AND "user_id" IN %s', (tuple(ac_ids), tuple(usr_ids)))
            res = self._cr.fetchone()
            record.amount = round(res and res[1] or 0.0, 2)

    user_id = fields.Many2one('res.users', string='User')
    amount = fields.Float(
        compute="_compute_unit_amount", string='Total Time', store=True)
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account', readonly=True)


class AnalyticInvoiceLine(models.Model):
    _name = "analytic.invoice.line"

    @api.multi
    @api.depends('qty', 'unit_price')
    def _get_amt_line(self):
        for line in self:
            line.subtotal = round((line.qty * line.unit_price), 2)

    subtotal = fields.Float(
        compute=_get_amt_line, string='Sub Total',
        digits=dp.get_precision('Account'))
    description = fields.Text(string='Description', required=True)
    account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', string='Product', required=True)
    taxes_ids = fields.Many2many("account.tax", string="Taxes")
    uom_id = fields.Many2one(
        'product.uom', string='Unit of Measure', required=True)
    unit_price = fields.Float(string='Unit Price', required=True)
    qty = fields.Float(string='Total Quantity', required=True, default=1)

    @api.onchange('product_id')
    def onchange_product_id(self):
        price = False

        if not self.product_id:
            self.unit_price = 0.0

        if not price:
            price = self.product_id.list_price

        if self.unit_price:
            price = self.unit_price
        elif self.product_id.pricelist_id:
            price = self.product_id.price

        self.uom_id = self.product_id.uom_id and self.product_id.uom_id.id or False
        if (self.uom_id and self.uom_id.id) != (
                self.product_id.uom_id and self.product_id.uom_id.id):
            price = self.uom_id._compute_price(self.unit_price, self.uom_id)

        self.unit_price = price

        if not self.description:
            desc = self.product_id.name_get()
            if desc:
                desc = desc[0][1]
            if self.product_id.description_sale:
                desc += '\n' + self.product_id.description_sale
                self.description = desc


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    @api.multi
    def _users_all(self):
        cr = self._cr
        cr.execute('SELECT MAX(id) FROM res_users')
        max_user = cr.fetchone()[0]
        if self.ids:
            cr.execute(
                'SELECT DISTINCT("user_id") FROM '
                'analytic_summary_user'
                'WHERE analytic_account_id IN %s AND amount != 0.0') % tuple(
                self.ids)
            result = cr.fetchall()
            self.user_ids = \
                result and \
                [4, 0, (int((id * max_user) + x[0]) for x in result)] or \
                [4, 0, []]

    @api.multi
    def _months_all(self):
        cr = self._cr
        if self.ids:
            cr.execute("""SELECT DISTINCT('month_id') FROM \
                analytic_summary_month WHERE analytic_account_id IN %s AND \
                amount != 0.0""") % tuple(self.ids)
            result = cr.fetchall()
            self.month_ids = \
                result and \
                [4, 0, (int(id * 1000000 + int(x[0])) for x in result)] or \
                [4, 0, []]

    @api.multi
    def _get_previous_worked_bill_date(self):
        cr = self._cr
        for record in self:
            cr.execute(
                '''SELECT account_analytic_line.account_id, MAX(date) \
                FROM account_analytic_line \
                WHERE account_id=%s \
                    AND invoice_id IS NOT NULL \
                GROUP BY account_analytic_line.account_id;''' % record.id)

            for account_id, date in cr.fetchone():
                record.previous_worked_bill_date = date

    @api.multi
    def _calculate_ca_to_invoice(self):
        cr = self._cr
        for account in self:
            cr.execute("""
                SELECT product_id, sum(amount), user_id, to_invoice,
                sum(unit_amount), product_uom_id, line.name
                FROM account_analytic_line line
                    LEFT JOIN account_journal journal ON \
                    (journal.id = line.journal_id)
                WHERE account_id = %s
                    AND journal.type != 'purchase'
                    AND invoice_id IS NULL
                    AND to_invoice IS NOT NULL
                GROUP BY product_id, user_id, to_invoice, product_uom_id,
                line.name""" % (account.id))

            records = cr.fetchall()
            amount = 0
            for res in records:
                product_id, price, user_id, factor_id, qty, uom, name = res
                price = -price
                if product_id:
                    line_obj = self.env['account.analytic.line']
                    price = line_obj._get_price(
                        account, product_id, user_id, qty)
                factor = self.env['hr_activity_invoice.factor'].browse(
                    factor_id).factor
                amount += round((price * qty * (
                    100 - factor or 0.0) / 100.0), 2)
            account.uninvoiced_amount = amount

    @api.multi
    def _calculate_previous_bill_date(self):
        cr = self._cr
        for record in self:
            query = """
                SELECT account_analytic_line.account_id,
                DATE(MAX(account_invoice.date_invoice))
                FROM account_analytic_line
                JOIN account_invoice
                ON account_analytic_line.invoice_id=account_invoice.id
                WHERE account_analytic_line.account_id=%s
                    AND account_analytic_line.invoice_id IS NOT NULL
                GROUP BY account_analytic_line.account_id
            """ % (record.id)

            cr.execute(query)
            res = cr.fetchone()
            record.previous_bill_date = res and res[1] or False

    @api.multi
    def _calculate_previous_worked_date(self):
        cr = self._cr
        for record in self:
            cr.execute('''
                SELECT account_analytic_line.account_id, MAX(date)
                FROM account_analytic_line
                WHERE account_id=%s
                    AND invoice_id IS NULL
                GROUP BY account_analytic_line.account_id;
            ''') % (record.id)

            res = cr.fetchone()
            record.previous_worked_date = res and res[1] or False

    @api.multi
    def _calculate_uninvoiced_time(self):
        for record in self:
            self._cr.execute('''
                SELECT account_analytic_line.account_id,
                COALESCE(SUM(unit_amount), 0.0)
                FROM account_analytic_line
                JOIN account_journal
                    ON account_analytic_line.journal_id = \
                    account_journal.id
                WHERE account_analytic_line.account_id=%s
                    AND account_journal.type='sale'
                    AND invoice_id IS NULL
                    AND to_invoice IS NOT NULL
                GROUP BY account_analytic_line.account_id;''') % (record.id)

            res = self._cr.fetchone()
            record.uninvoiced_time = round(res and res[1] or 0.0, 2)

    @api.multi
    def _calculate_hours_quantity(self):
        for record in self:
            self._cr.execute("""
                SELECT account_analytic_line.account_id,
                COALESCE(SUM(unit_amount), 0.0)
                FROM account_analytic_line
                JOIN account_journal
                ON account_analytic_line.journal_id=account_journal.id
                WHERE account_analytic_line.account_id=%s
                AND account_journal.type='sale'
                GROUP BY account_analytic_line.account_id
            """, (record.id,))
            res = self._cr.fetchone()
            record.total_worked_time = round(res and res[1] or 0.0, 2)

    @api.multi
    def _calculate_ca_theorical(self):
        for record in self:
            self._cr.execute("""
                SELECT account_analytic_line.account_id AS account_id, \
                    COALESCE(SUM((
                    account_analytic_line.unit_amount * pt.list_price) \
                            - (
                            account_analytic_line.unit_amount * pt.list_price \
                                * hr.factor)), 0.0) AS somme
                    FROM account_analytic_line \
                    LEFT JOIN account_journal \
                        ON (account_analytic_line.journal_id = \
                        account_journal.id) \
                    JOIN product_product pp \
                        ON (account_analytic_line.product_id = pp.id) \
                    JOIN product_template pt \
                        ON (pp.product_tmpl_id = pt.id) \
                    JOIN account_analytic_account a \
                        ON (a.id=account_analytic_line.account_id) \
                    JOIN hr_activity_invoice_factor hr \
                        ON (hr.id=a.to_invoice) \
                WHERE account_analytic_line.account_id=%s \
                    AND a.to_invoice IS NOT NULL \
                    AND account_journal.type IN \
                    ('purchase', 'sale')
                GROUP BY account_analytic_line.account_id""") % (record.id)

            for account_id, sum in self._cr.fetchone():
                record.theoretical_revenue = round(sum, 2)

    @api.multi
    @api.depends('timesheet_cust_inv_amt')
    def _calculate_cust_inv_amt(self):
        total = 0.0

        if self.ids:
            invoice_lines = self.env["account.invoice.line"].search([
                '&', ('account_analytic_id', 'in', self.ids),
                ('invoice_id.type', 'in', ('out_invoice', 'out_refund')),
                ('invoice_id.state', 'not in', ('draft', 'cancel')),
            ])

            for line in invoice_lines:
                total += -line.price_subtotal if line.invoice_id.type == \
                    'out_refund' else line.price_subtotal

        for account in self:
            account.cust_inv_amt = total - (
                account.timesheet_cust_inv_amt or 0.0)

    @api.multi
    def _calculate_cost(self):
        cr = self._cr
        for record in self:
            cr.execute("""
                SELECT account_analytic_line.account_id,
                COALESCE(SUM(amount), 0.0)
                FROM account_analytic_line
                JOIN account_journal
                ON account_analytic_line.journal_id = \
                account_journal.id
                WHERE account_analytic_line.account_id=%s
                AND amount < 0
                GROUP BY account_analytic_line.account_id""") % (record.id)

            for account_id, sum in cr.fetchone():
                record.account_cost = round(sum, 2)

    @api.multi
    @api.depends('quantity_max', 'total_worked_time')
    def _calculate_left_hours(self):
        for account in self:
            account.left_hours = 0.00
            if account.quantity_max:
                account.left_hours = round((
                    account.quantity_max - account.total_worked_time), 2)

    @api.multi
    @api.depends(
        'estimation_hours_invoice', 'timesheet_cust_inv_amt',
        'uninvoiced_amount')
    def _calculate_left_hours_to_invoice(self):
        for account in self:
            account.left_hours_to_invoice = max(
                account.estimation_hours_invoice -
                account.timesheet_cust_inv_amt,
                account.uninvoiced_amount)

    @api.multi
    @api.depends('total_worked_time', 'uninvoiced_time')
    def _calculate_invoiced_time(self):
        for account in self:
            account.invoiced_time = round((
                account.total_worked_time - account.uninvoiced_time), 2)

    @api.multi
    @api.depends('invoiced_time', 'cust_inv_amt')
    def _calculate_revenue_by_hour(self):
        for account in self:
            account.revenue_by_hour = round((
                account.cust_inv_amt / account.invoiced_time), 2)
            if not account.invoiced_time:
                account.revenue_by_hour = 0.0

    @api.multi
    @api.depends('real_revenue_margin', 'account_cost', 'cust_inv_amt')
    def _calculate_real_margin_per(self):
        for account in self:
            account.real_margin_per = 0.0
            if account.account_cost:
                account.real_margin_per = round((
                    -(account.real_revenue_margin / account.account_cost) *
                    100), 2)

    @api.multi
    def _calculate_invoice_fix_price(self):
        sale_obj = self.env['sale.order']
        for account in self:
            sale_ids = sale_obj.search([
                ('state', '=', 'sale'),
                ('analytic_account_id', '=', account.id)
            ])
            for sale in sale_ids:
                account.invoice_fix_price += sale.amount_untaxed - sum(
                    invoice.amount_untaxed for invoice in sale.invoice_ids
                    if invoice.state != 'cancel')

    @api.multi
    def _calculate_timesheet_cust_inv_amt(self):
        invoice_ids = []
        for account in self:
            analytic_lines = self.env['account.analytic.line'].search([
                ('to_invoice', '!=', False),
                ('invoice_id', '!=', False),
                ('account_id', '=', account.id),
                ('journal_id.type', '=', 'sale'),
                ('product_id.type', '=', 'service'),
                ('invoice_id.type', 'in', ('out_invoice', 'out_refund')),
                ('invoice_id.state', 'not in', ('draft', 'cancel')),
            ])
            for line in analytic_lines:
                amount = 0.0
                if line.invoice_id not in invoice_ids:
                    invoice_ids.append(line.invoice_id)
                    amount_untaxed = line.invoice_id.amount_untaxed
                    amount += -amount_untaxed if line.invoice_id.type \
                        == 'out_refund' else amount_untaxed
                    account.timesheet_cust_inv_amt = amount

    @api.multi
    @api.depends('amt_max', 'cust_inv_amt', 'invoice_fix_price')
    def _calculate_remaining_revenue(self):
        for account in self:
            account.remaining_revenue = max(
                account.amt_max - account.cust_inv_amt,
                account.invoice_fix_price)

    @api.multi
    @api.depends('cust_inv_amt', 'account_cost')
    def _calculate_real_revenue_margin(self):
        for account in self:
            account.real_revenue_margin = round((
                account.cust_inv_amt + account.account_cost), 2)

    @api.multi
    @api.depends('theoretical_revenue', 'account_cost')
    def _calculate_theorical_revenue_margin(self):
        for account in self:
            account.theorical_revenue_margin = round((
                account.theoretical_revenue + account.account_cost), 2)

    @api.multi
    @api.depends('total_worked_time', 'quantity_max')
    def _get_overdue_quantity(self):
        for account in self.filtered(lambda acc: acc.quantity_max > 0.0):
            account.is_overdue_qty = False
            account.is_overdue_qty = bool(
                account.total_worked_time > account.quantity_max)

    @api.multi
    @api.depends('timesheet_invoice', 'fixed_price',
                 'estimation_hours_invoice', 'amt_max')
    def _compute_estimation_total(self):
        total = 0.0
        for account in self:
            if account.timesheet_invoice:
                total = account.estimation_hours_invoice
            if account.fixed_price:
                total += account.amt_max
            account.estimation_total = total

    @api.multi
    @api.depends('timesheet_invoice', 'fixed_price', 'timesheet_cust_inv_amt',
                 'cust_inv_amt')
    def _compute_total_invoiced(self):
        total = 0.0
        for account in self:
            if account.timesheet_invoice:
                total = account.timesheet_cust_inv_amt
            if account.fixed_price:
                total += account.cust_inv_amt
            account.total_invoiced = total

    @api.multi
    @api.depends('timesheet_invoice', 'fixed_price', 'left_hours_to_invoice',
                 'remaining_revenue')
    def _compute_total_remaining(self):
        total = 0.0
        for account in self:
            if account.timesheet_invoice:
                total = account.left_hours_to_invoice
            if account.fixed_price:
                total += account.remaining_revenue
            account.total_remaining = total

    @api.multi
    @api.depends('timesheet_invoice', 'fixed_price', 'uninvoiced_amount',
                 'invoice_fix_price')
    def _compute_total_to_invoice(self):
        total = 0.0
        for account in self:
            if account.timesheet_invoice:
                total = account.uninvoiced_amount
            if account.fixed_price:
                total += account.invoice_fix_price
            account.total_to_invoice = total

    @api.multi
    def unlink(self):
        for account in self:
            project_ids = self.env['project.project'].search([
                ('analytic_account_id', '=', account.id)
            ])
            if project_ids:
                raise Warning(_("Please delete the linked Project first!"))
            analytic_line_ids = self.env['account.analytic.line'].search([
                ('account_id', '=', account.id)
            ])
            if analytic_line_ids:
                raise Warning(
                    _("Please delete the linked Analytic Line(s) first!"))
            return super(AccountAnalyticAccount, account).unlink()

    total_worked_time = fields.Float(
        compute=_calculate_hours_quantity, string='Total Worked Time')
    invoiced_time = fields.Float(
        compute=_calculate_invoiced_time, string='Invoiced Time')
    account_cost = fields.Float(
        compute=_calculate_cost, string='Total Costs',
        digits=dp.get_precision('Account'))
    uninvoiced_amount = fields.Float(
        compute=_calculate_ca_to_invoice,
        string='Uninvoiced Amount',
        digits=dp.get_precision('Account'))
    cust_inv_amt = fields.Float(
        compute=_calculate_cust_inv_amt, string='Invoiced Amount',
        digits=dp.get_precision('Account'))
    theoretical_revenue = fields.Float(
        compute=_calculate_ca_theorical,
        string='Theoretical Revenue',
        digits=dp.get_precision('Account'))
    uninvoiced_time = fields.Float(
        compute=_calculate_uninvoiced_time,
        string='Uninvoiced Time')
    is_overdue_qty = fields.Boolean(
        compute=_get_overdue_quantity, string='Overdue Quantity', store=True)
    left_hours = fields.Float(
        compute=_calculate_left_hours, string='Remaining Time')
    left_hours_to_invoice = fields.Float(
        compute=_calculate_left_hours_to_invoice, string='Remaining Time')
    previous_bill_date = fields.Date(
        compute=_calculate_previous_bill_date,
        string='Last Invoice Date ')
    invoice_fix_price = fields.Float(
        compute=_calculate_invoice_fix_price, string='Remaining Time')
    timesheet_cust_inv_amt = fields.Float(
        compute=_calculate_timesheet_cust_inv_amt, string='Remaining Time')
    previous_worked_date = fields.Date(
        compute=_calculate_previous_worked_date,
        string='Date of Last Cost/Work')
    remaining_revenue = fields.Float(
        compute=_calculate_remaining_revenue, string='Remaining Revenue',
        digits=dp.get_precision('Account'))
    previous_worked_bill_date = fields.Date(
        compute=_get_previous_worked_bill_date,
        string='Date of Last Invoiced Cost')
    revenue_by_hour = fields.Float(
        compute=_calculate_revenue_by_hour, string='Revenue per Time (real)',
        digits=dp.get_precision('Account'))
    theorical_revenue_margin = fields.Float(
        compute=_calculate_theorical_revenue_margin,
        string='Theoretical Margin',
        digits=dp.get_precision('Account'))
    real_margin_per = fields.Float(
        compute=_calculate_real_margin_per, string='Real Margin Rate (%)',
        digits=dp.get_precision('Account'))
    fixed_price = fields.Boolean('Fixed Price')
    real_revenue_margin = fields.Float(
        compute=_calculate_real_revenue_margin, string='Real Margin ',
        digits=dp.get_precision('Account'))
    timesheet_invoice = fields.Boolean("On Timesheets")
    month_ids = fields.Many2many(
        "analytic.summary.month", string='Months', compute=_months_all)
    user_ids = fields.Many2many(
        "analytic.summary.user", string='Users', compute=_users_all)
    estimation_hours_invoice = fields.Float('Estimation of Hours to Invoice')
    estimation_total = fields.Float(
        compute=_compute_estimation_total, string="Total Estimation")
    rec_invoice_line_ids = fields.One2many(
        'analytic.invoice.line', 'account_id',
        string='Invoice Lines', copy=True)
    total_remaining = fields.Float(
        compute=_compute_total_remaining, string="Total Remaining")
    rec_invoices = fields.Boolean(
        'Generate recurring invoices automatically', default=True)
    rec_rule_type = fields.Selection([
        ('daily', 'Day(s)'),
        ('weekly', 'Week(s)'),
        ('monthly', 'Month(s)'),
        ('yearly', 'Year(s)')], string='Recurrency', default="monthly")
    rec_interval = fields.Integer('Repeat Every', default=1)
    total_invoiced = fields.Float(
        compute=_compute_total_invoiced, string="Total Invoiced")
    nex_rec_date = fields.Date(
        string='Date of Next Invoice', default=datetime.date.today())
    total_to_invoice = fields.Float(
        compute=_compute_total_to_invoice, string="Total to Invoice")
    template_id = fields.Many2one(
        'account.analytic.account', string='Template of Contract')
    parent_id = fields.Many2one(
        'account.analytic.account', string='Parent Analytic Account')
    child_ids = fields.One2many(
        'account.analytic.account', 'parent_id', string='Child Accounts')
    manager_id = fields.Many2one('res.users', string='Account Manager')
    type = fields.Selection([
        ('view', 'Analytic View'),
        ('normal', 'Analytic Account'),
        ('contract', 'Contract or Project'),
        ('template', 'Template of Contract')],
        string='Type of Account')
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        if self.filtered(lambda c: c.date_end and c.date_start > c.date_end):
            raise ValidationError(
                _('Start date must be less than End date.'))

    @api.multi
    def open_so_lines(self):
        self.ensure_one()
        partner_id = self.env.context.get('search_default_partner_id', False)
        order_ids = self.env['sale.order'].search([
            ('partner_id', 'in', partner_id),
            ('analytic_account_id', 'in', self.ids)])
        return {
            'name': _('Lines to Invoice of %s') % (self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('order_id', 'in', order_ids and order_ids.ids)],
        }

    @api.onchange('template_id')
    def onchange_template_id(self):
        template = self.template_id

        self.fixed_price = template.fixed_price
        self.amt_max = template.amt_max
        self.timesheet_invoice = template.timesheet_invoice
        self.estimation_hours_invoice = template.estimation_hours_invoice

        if template and template.to_invoice and template.to_invoice.id:
            self.to_invoice = template.to_invoice.id
        if template and template.pricelist_id and template.pricelist_id.id:
            self.pricelist_id = template.pricelist_id.id
        if not self.ids:
            invoice_line_vals = []
            for line in template.rec_invoice_line_ids:
                invoice_line_vals.append((0, 0, {
                    'product_id': line.product_id and
                    line.product_id.id or False,
                    'description': line.description,
                    'qty': line.qty,
                    'unit_price': line.unit_price,
                    'uom_id': line.uom_id and line.uom_id.id or False,
                    'account_id':
                        line.account_id and
                        line.account_id.id or False,
                }))
            self.rec_invoices = template.rec_invoices
            self.rec_interval = template.rec_interval
            self.rec_rule_type = template.rec_rule_type
            self.rec_invoice_line_ids = invoice_line_vals

    @api.onchange('rec_invoices')
    def onchange_rec_invoices(self):
        self.rec_interval = 1
        self.rec_rule_type = "monthly"
        if self.date_start and self.rec_invoices:
            self.nex_rec_date = self.date_start

    @api.onchange('timesheet_invoice')
    def onchange_timesheet_invoice(self):
        self.use_timesheets = True
        to_invoice = self.env.ref('hr_activity_invoice.activity_factor_1')
        self.to_invoice = \
            not self.timesheet_invoice and False or to_invoice.id

    @api.multi
    def invoice_timesheets(self):
        self.ensure_one()
        return {
            'name': _('Pending Timesheets to bill of %s') % (self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [
                ('invoice_id', '=', False),
                ('to_invoice', '!=', False),
                ('journal_id.type', '=', 'sale'),
                ('product_id.type', '=', 'service'),
                ('account_id', 'in', self.ids)
            ],
        }

    def _generate_inv_values(self, contract):
        if not contract.partner_id:
            raise UserError(
                _("Please select customer for Contract %s!") % contract.name)

        fpos_id = self.env['account.fiscal.position'].get_fiscal_position(
            self.env.context.get('force_company') or contract.partner_id.company_id.id, contract.partner_id.id)
        journal_ids = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', contract.company_id.id or False)], limit=1)
        if not journal_ids:
            raise UserError(_(
                'You need to define a sale journal for the company "%s".') %
                (contract.company_id.name or ''))

        currency_id = False
        if contract.pricelist_id:
            currency_id = contract.pricelist_id.currency_id and \
                contract.pricelist_id.currency_id.id
        elif contract.partner_id.property_product_pricelist:
            currency_id = contract.partner_id.property_product_pricelist.currency_id and \
                contract.partner_id.property_product_pricelist.currency_id.id
        elif contract.company_id:
            currency_id = contract.company_id.currency_id and \
                contract.company_id.currency_id.id

        return {
            'company_id': contract.company_id.id or False,
            'currency_id': currency_id,
            'journal_id': journal_ids and journal_ids.id or False,
            'type': 'out_invoice',
            'payment_term_id':
                contract.partner_id.property_payment_term_id and
                contract.partner_id.property_payment_term_id.id or False,
            'partner_id': contract.partner_id.id,
            'fiscal_position_id': fpos_id,
            'origin': contract.code,
            'date_invoice': contract.nex_rec_date,
            'user_id': contract.manager_id.id or self.env.uid,
            'comment': '',
            'account_id': contract.partner_id.property_account_receivable_id.id,
        }

    def _generate_invoice_line(self, line):
        fpos = self.partner_id and \
            self.partner_id.property_account_position_id and \
            self.partner_id.property_account_position_id.id or False
        account_id = \
            line.product_id.property_account_income_id and \
            line.product_id.property_account_income_id.id or False
        if not account_id:
            category = line.product_id.categ_id
            account_id = \
                category and category.property_account_income_categ_id and \
                category.property_account_income_categ_id.id or False
        account_id = fpos and fpos.map_account(account_id) or account_id

        taxes = line.product_id.taxes_id or line.taxes_ids or False
        tax_ids = fpos and fpos.map_tax(
            taxes, line.product_id.id, self.partner_id.id) or taxes
        if not tax_ids:
            tax_ids = line.taxes_ids.ids or []

        return {
            'name': line.description,
            'account_id': account_id,
            'product_id': line.product_id.id or False,
            'account_analytic_id':
                line.account_id and
                line.account_id.id or False,
            'uom_id': line.uom_id and line.uom_id.id or False,
            'quantity': line.qty,
            'price_unit': line.unit_price or 0.0,
            'invoice_line_tax_ids': [(6, 0, tax_ids.ids)],
        }

    def _generate_invoice_lines(self, contract_obj):
        invoice_lines = []
        for line in contract_obj.rec_invoice_line_ids:
            vals = self._generate_invoice_line(line)
            invoice_lines.append((0, 0, vals))
        return invoice_lines

    def _cron_contract_exp_reminder(self):
        context = dict(self.env.context or {})
        res = {}

        def add_domain(key, domain, is_pending=False):
            initial_domain = [
                ('type', '=', 'contract'),
                ('manager_id', '!=', False),
                ('manager_id.email', '!=', False),
                ('partner_id', '!=', False),
            ]
            initial_domain.extend(domain)

            for account in self.search(initial_domain, order='name asc'):
                if is_pending:
                    account.write({'state': 'pending'})
                dom_user = res.setdefault(
                    account.manager_id and account.manager_id.id, {})
                dom_type = dom_user.setdefault(key, {})
                dom_type.setdefault(
                    account.partner_id, []).append(account)

        add_domain("old", [('state', 'in', ['pending'])])

        add_domain("new", [
            ('state', 'in', ['draft', 'open']),
            '|', '&', ('date', '!=', False),
            ('date', '<=', time.strftime('%Y-%m-%d')),
            ('is_overdue_qty', '=', True)
        ], True)

        add_domain("future", [
            ('state', 'in', ['draft', 'open']),
            ('date', '!=', False),
            ('date', '<', (datetime.datetime.now() + datetime.timedelta(
                30)).strftime("%Y-%m-%d"))
        ])
        action = self.env.ref(
            "account_costing_analysis.account_analytic_overdue_all_form_view")
        context.update({
            'base_url': self.env['ir.config_parameter'].get_param(
                'web.base.url'),
            'action_id': action and action.id
        })
        template_id = self.env.ref(
            'account_costing_analysis.email_template_expiration_reminder')
        for user_id, data in res.items():
            context.update({'data': data})
            template_id.with_context(context).send_mail(
                user_id, force_send=True)

        return True

    @api.model
    def _cron_contract_invoice_recurring(self):
        return self.contract_invoice_recurring(auto=True)

    def contract_invoice_recurring(self, auto=True):
        context = self.env.context or {}
        inv_ids = []
        curr_date = time.strftime('%Y-%m-%d')
        contract_search_ids = self.search([
            ('type', '=', 'contract'),
            ('rec_invoices', '=', True),
            ('nex_rec_date', '<=', curr_date),
            ('state', '=', 'open'),
        ]).ids
        con_ids = self.ids or contract_search_ids
        if con_ids:
            query = """
                SELECT company_id, array_agg(id) as ids FROM
                account_analytic_account WHERE id IN (%s) GROUP BY company_id
            """ % tuple(con_ids)
            self._cr.execute(query)
            for company_id, ids in self._cr.fetchall():
                ctx = dict(
                    context, company_id=company_id, force_company=company_id)
                for con in self.with_context(ctx).browse(ids):
                    try:
                        invoice = self._generate_inv_values(con)
                        invoice['invoice_line_ids'] = \
                            self._generate_invoice_lines(con)
                        created_invoice = self.env['account.invoice'].create(
                            invoice)
                        inv_ids.append(created_invoice)
                        date_next = datetime.datetime.strptime(
                            con.nex_rec_date or curr_date,
                            "%Y-%m-%d")
                        interval = con.rec_interval
                        if con.rec_rule_type == 'daily':
                            date_new = date_next + relativedelta(
                                days=+interval)
                        elif con.rec_rule_type == 'weekly':
                            date_new = date_next + relativedelta(
                                weeks=+interval)
                        elif con.rec_rule_type == 'monthly':
                            date_new = date_next + relativedelta(
                                months=+interval)
                        else:
                            date_new += relativedelta(years=+interval)
                        self.write({
                            'nex_rec_date': date_new.strftime(
                                '%Y-%m-%d')
                        })
                        if auto:
                            self._cr.commit()
                    except Exception:
                        if auto:
                            self._cr.rollback()
                            _logger.exception(
                                'Failed to create recurring invoice '
                                'for contract %s', con.code)
                        else:
                            pass

        return inv_ids
