# Part of Odoo S.A.,Flectra See LICENSE file for full copyright and
# licensing details.

from flectra import api, fields, models
import flectra.addons.decimal_precision as dp
from flectra.tools.sql import drop_view_if_exists


class ReportAnalyticAccountClose(models.Model):
    _name = "report.analytic.account.close"
    _auto = False

    year = fields.Many2one(
        'account.analytic.account', string='Analytic account', readonly=True)
    partner_id = fields.Many2one(
        'res.partner', string='Partner', readonly=True)
    balance = fields.Float(string='Balance ', readonly=True)
    quantity = fields.Float(string='Quantity ', readonly=True)
    date_deadline = fields.Date(string='Deadline', readonly=True)
    quantity_max = fields.Float(string='Max. Quantity', readonly=True)
    state = fields.Char(string='Status', readonly=True)

    @api.model_cr
    def init(self):
        drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute("""
            create or replace view report_analytic_account_close as (
                select
                    a.id as id, a.id as year, a.state as state,
                    sum(l.unit_amount) as quantity, sum(l.amount) as balance,
                    a.partner_id as partner_id, a.quantity_max as quantity_max,
                    a.date as date_deadline
                from account_analytic_line l right join
                    account_analytic_account a on (l.account_id=a.id)
                group by
                    a.id,a.state,a.quantity_max,a.date,a.partner_id
                having (a.quantity_max>0 and (
                sum(l.unit_amount)>=a.quantity_max)) or a.date <= current_date
            )""")


class ReportAccountAnalyticLineToInvoice(models.Model):
    _name = "report.account.analytic.line.to.invoice"
    _order = 'year desc, product_id asc, account_id asc'
    _auto = False

    year = fields.Char(string='Year', readonly=True)
    product_id = fields.Many2one(
        'product.product', string='Product', readonly=True)

    product_uom_id = fields.Many2one(
        'product.uom', string='Unit of Measure', readonly=True)
    unit_amount = fields.Float(string='Units', readonly=True)
    account_id = fields.Many2one(
        'account.analytic.account', string='Analytic account', readonly=True)
    sale_price = fields.Float(
        string='Sale price ', readonly=True,
        digits=dp.get_precision('Product Price'))
    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'), ('07', 'July'),
        ('08', 'August'), ('09', 'September'), ('10', 'October'),
        ('11', 'November'), ('12', 'December')], string='Month ',
        readonly=True)
    amount = fields.Float(
        string='Amount ', readonly=True,
        digits=dp.get_precision('Account'))

    @api.model_cr
    def init(self):
        drop_view_if_exists(
            self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW report_account_analytic_line_to_invoice AS (
                SELECT
                    DISTINCT(to_char(l.date,'MM')) as month,
                    to_char(l.date, 'YYYY') as year,
                    MIN(l.id) AS id,
                    l.product_id,
                    l.account_id,
                    SUM(l.amount) AS amount,
                    SUM(l.unit_amount*t.list_price) AS sale_price,
                    SUM(l.unit_amount) AS unit_amount,
                    l.product_uom_id
                FROM
                    account_analytic_line l
                left join
                    product_product p on (l.product_id=p.id)
                left join
                    product_template t on (p.product_tmpl_id=t.id)
                WHERE
                    (invoice_id IS NULL) and (to_invoice IS NOT NULL)
                GROUP BY
                    to_char(l.date, 'YYYY'), to_char(
                    l.date,'MM'), l.product_id, l.product_uom_id, l.account_id
            )
        """)
