# Part of Flectra See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, tools


class PaymentFollowupStatistics(models.AbstractModel):
    _name = "payment.followup.statistics"
    _description = "Follow-up Statistics"
    _rec_name = 'partner_id'
    _order = 'first_move_date'
    _auto = False

    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    first_move_date = fields.Date('First move', readonly=True)
    last_move_date = fields.Date('Last move', readonly=True)
    date_payment_followup = fields.Date('Follow-up Date', readonly=True)
    payment_followup_id = fields.Many2one('payment.followup.line',
                             'Follow Ups', readonly=True,
                             ondelete="cascade")
    amount_balance = fields.Float('Balance', readonly=True)
    debit = fields.Float('Debit', readonly=True)
    credit = fields.Float('Credit', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    blocked = fields.Boolean('Blocked', readonly=True)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0,
                   limit=None, orderby=False, lazy=True):
        for value in domain:
            if value[0] == 'period_id' and value[2] == 'current_year':
                current_year = self.env['account.fiscalyear'].find()
                ids = current_year.read(['period_ids'])[0]['period_ids']
                domain.append(['period_id', 'in', ids])
                domain.remove(value)
        return super(PaymentFollowupStatistics, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit,
            orderby=orderby, lazy=lazy)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        for arg in args:
            if arg[0] == 'period_id' and arg[2] == 'current_year':
                current_year = self.env['account.fiscalyear'].find()
                ids = current_year.read(['period_ids'])[0]['period_ids']
                args.append(['period_id', 'in', ids])
                args.remove(arg)
        return super(PaymentFollowupStatistics, self).search(
            args, offset=0, limit=None, order=None, count=False)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'payment_followup_statistics')
        self._cr.execute("""
            create or replace view payment_followup_statistics as (
                SELECT
                    l.id as id,
                    l.partner_id AS partner_id,
                    min(l.date) AS first_move_date,
                    max(l.date) AS last_move_date,
                    max(l.date_payment_followup) AS date_payment_followup,
                    max(l.payment_followup_line_id) AS payment_followup_id,
                    sum(l.debit) AS debit,
                    sum(l.credit) AS credit,
                    sum(l.debit - l.credit) AS amount_balance,
                    l.company_id AS company_id,
                    l.blocked as blocked
                FROM
                    account_move_line l
                    LEFT JOIN account_account a ON (l.account_id = a.id)
                WHERE
                    a.user_type_id IN (SELECT id FROM account_account_type
                    WHERE type = 'receivable') AND
                    l.full_reconcile_id is NULL AND
                    l.partner_id IS NOT NULL
                GROUP BY
                    l.id, l.partner_id, l.company_id, l.blocked
            )""")
