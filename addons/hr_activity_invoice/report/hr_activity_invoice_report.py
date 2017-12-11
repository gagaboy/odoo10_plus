# Part of Odoo S.A.,Flectra See LICENSE file for full copyright and
# licensing details.

from flectra import api, fields, models
from flectra.tools.sql import drop_view_if_exists


class ReportTimesheetInvoice(models.Model):
    _name = "report_timesheet.invoice"
    _rec_name = 'user_id'
    _description = "Costs to invoice"
    _order = 'user_id desc'
    _auto = False

    user_id = fields.Many2one('res.users', string='User', readonly=True)
    qty = fields.Float('Time', readonly=True)
    account_id = fields.Many2one(
        'account.analytic.account', string="Analytic Account", readonly=True)
    manager_id = fields.Many2one(
        'res.users', string='Manager', readonly=True)
    invoice_amount = fields.Float('To invoice', readonly=True)

    @api.model_cr
    def init(self):
        drop_view_if_exists(self._cr, 'report_timesheet_invoice')
        self._cr.execute("""
            create or replace view report_timesheet_invoice as (
                select
                    min(l.id) as id, l.user_id as user_id,
                    l.account_id as account_id, l.user_id as manager_id,
                    sum(l.unit_amount) as qty,
                    sum(l.unit_amount * t.list_price) as invoice_amount
                from account_analytic_line l
                    left join hr_activity_invoice_factor f on
                    (l.to_invoice=f.id)
                    left join account_analytic_account a on (l.account_id=a.id)
                    left join product_product p on (l.to_invoice=f.id)
                    left join product_template t on (l.to_invoice=f.id)
                where
                    l.to_invoice is not null and l.invoice_id is null
                group by
                    l.user_id, l.account_id, l.user_id
            )
        """)


class HrActivityUser(models.Model):
    _name = "hr.activity.user"
    _order = 'year desc,user_id desc'

    year = fields.Char('Year', readonly=True)
    qty = fields.Float('Time', readonly=True)
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'), ('07', 'July'),
        ('08', 'August'), ('09', 'September'), ('10', 'October'),
        ('11', 'November'), ('12', 'December')], string='Month ',
        readonly=True)
    cost = fields.Float('Cost ', readonly=True)

    @api.model_cr
    def init(self):
        drop_view_if_exists(self._cr, 'report_timesheet_user')
        self._cr.execute("""
            create or replace view report_timesheet_user as (
                select
                    min(l.id) as id, to_char(l.date,'YYYY') as year,
                    to_char(l.date,'MM') as month,
                    l.user_id, sum(l.unit_amount) as qty, sum(l.amount) as cost
                from
                    account_analytic_line l
                where
                    user_id is not null
                group by l.date, to_char(l.date,'YYYY'), to_char(l.date,'MM'),
                l.user_id
            )
        """)


class ReportTimesheetAccount(models.Model):
    _name = "report_timesheet.account"
    _order = 'year desc,account_id desc,user_id desc'
    _auto = False

    year = fields.Char('Year', readonly=True)
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    qty = fields.Float('Time', readonly=True)
    account_id = fields.Many2one(
        'account.analytic.account', string="Analytic Account", readonly=True)
    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'), ('07', 'July'),
        ('08', 'August'), ('09', 'September'), ('10', 'October'),
        ('11', 'November'), ('12', 'December')], string='Month ',
        readonly=True)

    @api.model_cr
    def init(self):
        drop_view_if_exists(self._cr, 'report_timesheet_account')
        self._cr.execute("""
            create or replace view report_timesheet_account as (
                select
                    min(id) as id,
                    to_char(create_date, 'YYYY') as year,
                    to_char(create_date,'MM') as month,
                    user_id,
                    account_id,
                    sum(unit_amount) as qty
                from
                    account_analytic_line
                group by
                    to_char(create_date, 'YYYY'),to_char(create_date, 'MM'),
                    user_id, account_id
            )
        """)


class ReportTimesheetAccountDate(models.Model):
    _name = "report_timesheet.account.date"
    _description = "Daily timesheet per account"
    _order = 'year desc,account_id desc,user_id desc'
    _auto = False

    year = fields.Char('Year', readonly=True)
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    qty = fields.Float('Time', readonly=True)
    account_id = fields.Many2one(
        'account.analytic.account', string="Analytic Account", readonly=True)
    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'), ('07', 'July'),
        ('08', 'August'), ('09', 'September'), ('10', 'October'),
        ('11', 'November'), ('12', 'December')], string='Month ',
        readonly=True)

    @api.model_cr
    def init(self):
        cr = self._cr
        drop_view_if_exists(cr, 'report_timesheet_account_date')
        cr.execute("""
            create or replace view report_timesheet_account_date as (
                select
                    min(id) as id,
                    to_char(date,'YYYY') as year,
                    to_char(date,'MM') as month,
                    user_id,
                    account_id,
                    sum(unit_amount) as qty
                from
                    account_analytic_line
                group by
                    to_char(date,'YYYY'),to_char(date,'MM'), user_id,
                    account_id
            )
        """)


class ReportActivityLine(models.Model):
    _name = "report.activity.line"
    _order = 'year desc, user_id desc'

    year = fields.Char('Year', readonly=True)
    day = fields.Char('Day ', size=128, readonly=True)
    qty = fields.Float('Time', readonly=True)
    cost = fields.Float('Cost ', readonly=True)

    account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account', readonly=True)
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    product_id = fields.Many2one(
        'product.product', string='Product', readonly=True)
    invoice_id = fields.Many2one(
        'account.invoice', string='Invoiced', readonly=True)
    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'), ('07', 'July'),
        ('08', 'August'), ('09', 'September'), ('10', 'October'),
        ('11', 'November'), ('12', 'December')], string='Month ',
        readonly=True)
    date = fields.Date('Date ', readonly=True)
    general_account_id = fields.Many2one(
        'account.account', string='General Account', readonly=True)

    @api.model_cr
    def init(self):
        drop_view_if_exists(self._cr, 'report_timesheet_line')
        self._cr.execute("""
            create or replace view report_timesheet_line as (
                select
                    min(l.id) as id, l.date as date,
                    to_char(l.date,'YYYY') as year,
                    to_char(l.date,'MM') as month, l.user_id,
                    to_char(l.date, 'YYYY-MM-DD') as day,
                    l.invoice_id, l.product_id, l.account_id,
                    l.general_account_id, sum(l.unit_amount) as qty,
                    sum(l.amount) as cost
                from
                    account_analytic_line l
                where
                    l.user_id is not null
                group by
                    l.date, l.user_id, l.product_id, l.account_id,
                    l.general_account_id, l.invoice_id
            )
        """)
