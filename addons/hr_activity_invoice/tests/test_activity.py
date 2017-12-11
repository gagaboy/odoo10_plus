# Part of Odoo S.A.,Flectra See LICENSE file for full copyright and
# licensing details.

from datetime import datetime, timedelta
from flectra.tests.common import TransactionCase


class TestActivityCases(TransactionCase):

    def setUp(self):
        super(TestActivityCases, self).setUp()
        self.wizard = self.env['account.analytic.revenue']
        self.journal = self.env['account.journal']
        self.analytic_line = self.env['account.analytic.line']
        self.employee = self.env['hr.employee']
        self.user = self.env['res.users'].create({
            'name': 'John Doe',
            'login': 'john@doe.com'
        })

    def test_timesheet_revenue_wizard(self):
        '''
            Timesheet Revenue report wizard
        '''
        journal_id = self.journal.create({
            'name': 'Custom_Journal',
            'type': 'sale',
            'company_id':
                self.env.user.company_id and
                self.env.user.company_id.id or False,
            'code': 'JOURNAL_CST',
        })
        account_id = self.env.ref('analytic.analytic_agrolait')

        self.employee.create({
            'name': self.user.name or '',
            'journal_id': journal_id and journal_id.id or False,
            'user_id': self.user and self.user.id or False,
            'company_id':
                self.user.company_id and
                self.user.company_id.id or False,
        })

        self.analytic_line.create({
            'name': 'This is gonna be the task description of the line',
            'journal_id': journal_id and journal_id.id or False,
            'account_id': account_id and account_id.id or False,
            'amount': 500,
            'date': (datetime.today()).strftime("%Y-%m-%d"),
            'user_id': self.user.id or False
        })

        wizard_id = self.wizard.create({
            'date_from': (datetime.today() - timedelta(
                days=30)).strftime("%Y-%m-%d"),
            'date_to': datetime.today().strftime("%Y-%m-%d"),
            'journal_ids': [(6, 0, [journal_id and journal_id.id])],
            'employee_ids': [(6, 0, [self.user.id])],
        })
        data = wizard_id.read()[0]
        wizard_id.print_report(data)
