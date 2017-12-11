# Part of Odoo S.A.,Flectra See LICENSE file for full copyright and
# licensing details.

import datetime

from flectra import fields, models
from flectra.exceptions import UserError
from flectra.tools.translate import _


class AccountAnalyticRevenue(models.TransientModel):
    _name = 'account.analytic.revenue'
    _description = 'Timesheet Revenue Report'

    journal_ids = fields.Many2many(
        'account.journal', string="Journal", required=True)
    employee_ids = fields.Many2many(
        'res.users', string="User", required=True)
    date_to = fields.Date(
        string='To', required=True,
        default=datetime.date.today().strftime('%Y-%m-%d'))
    date_from = fields.Date(
        string='From', required=True,
        default=datetime.date.today().replace(day=1).strftime('%Y-%m-%d'))

    def print_report(self, data):
        data['form'] = {}
        data['form'].update(self.read(
            ['date_from', 'date_to', 'journal_ids', 'employee_ids'])[0])

        analytic_ids = self.env['account.analytic.line'].search([
            ('date', '>=', data['form']['date_from']),
            ('journal_id', 'in', data['form']['journal_ids']),
            ('date', '<=', data['form']['date_to']),
            ('user_id', 'in', data['form']['employee_ids'])
        ])

        if not analytic_ids.ids:
            raise UserError(_('No record(s) found for this report.'))

        return self.env.ref(
            'hr_activity_invoice.action_analytic_revenue_report'
        ).report_action(self, data=data)
