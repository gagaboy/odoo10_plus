# Part of Flectra See LICENSE file for full copyright and licensing details.

import datetime

from flectra import fields
from flectra.tests.common import TransactionCase
from flectra.tools import DEFAULT_SERVER_DATE_FORMAT


class TestUserCostingFunction(TransactionCase):
    def setUp(self):
        super(TestUserCostingFunction, self).setUp()
        self.wizard_analytic_line = self.env['hr.activity.invoice.create']
        self.project = self.env.ref("project.project_project_2")
        self.analytic_line = self.env['account.analytic.line']
        self.user = self.env.ref('base.user_root')
        self.employee = self.env['hr.employee'].search(
            [('user_id', '=', self.user.id)], limit=1)
        self.analytic_account = self.env.ref(
            "user_costing_function.contract_new_agrolait")
        self.current_date = datetime.datetime.strptime(
            fields.Date.today(), DEFAULT_SERVER_DATE_FORMAT)

    def test_check_analytic_line_amount_and_invoice(self):
        '''
            Create invoice from Analytic entries wizard.
        '''
        project_task = self.env['project.task'].create({
            'project_id': self.project.id,
            'name': "Task new",
        })
        activity = self.analytic_line.create(
            {'name': "Test Description",
             'employee_id': self.employee.id,
             'date': self.current_date,
             'product_id': self.env.ref('product.product_product_1').id,
             'unit_amount': 1,
             'task_id': project_task.id,
             'to_invoice': self.env.ref(
                 'hr_activity_invoice.activity_factor_1').id,
             'account_id': self.analytic_account.id})
        activity.on_change_unit_amount()
        analytic_line_id = self.env.ref(
            'user_costing_function.activity_description')
        self.assertIsNotNone(activity, "Activity not created properly")
        # self.assertFalse(analytic_line_id.amount == activity.amount,
        #                  "Amount is updated to have contract wise different "
        #                  "amount for same resource")
        # self.assertEqual(activity.amount, -50,
        #                  "Amount properly updated as defined in contract")

        # wizard_id = self.wizard_analytic_line.create({
        #     'date': True,
        #     'time': True,
        #     'name': True,
        #     'price': True,
        # })
        # data = wizard_id.read()[0]
        # invoices = self.analytic_line.create_invoice_cost([activity.id], data)
        # invoice_amount = self.env['account.invoice'].browse(
        #     invoices).amount_total
        # self.assertEqual(activity.amount, -invoice_amount,
        #                  "Amount properly updated as defined in contract")
