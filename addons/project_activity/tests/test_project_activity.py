# Part of Flectra See LICENSE file for full copyright and licensing details.

from flectra import fields
from flectra.tests.common import TransactionCase
from flectra.exceptions import UserError
import logging

logger = logging.getLogger(__name__)


class TestProjectActivity(TransactionCase):
    def setUp(self):
        """ setUp ***"""
        super(TestProjectActivity, self).setUp()

        self.partner = self.env['res.partner']
        self.project = self.env['project.project']
        self.user_id = self.env.ref('base.user_demo')
        self.root_user = self.env.ref('base.user_root')
        self.partner_id = self.env.ref('base.res_partner_4')
        self.partner2_id = self.user_id.partner_id
        self.project_id = self.env.ref('project.project_project_5')
        self.task_id = self.env.ref('project.project_task_22')
        self.default_invoice_factor = self.env.ref(
            'hr_activity_invoice.activity_factor_1')

    def test_00_check_partner_onchange(self):
        '''
        Onchange of partner(customer) of projects its to_invoice
         should be set to 100%
        '''
        self.project_id.partner_id = self.partner2_id.id
        self.project_id.on_partner_id_change()
        self.assertEqual(self.project_id.to_invoice.id,
                         self.default_invoice_factor.id,
                         'Onchange Partner not working properly')

    def test_01_check_partner_unlink(self):
        '''
        If in partner, partner is project customer than unlink
         should not be allowed
        '''
        try:
            curr_partner = self.partner_id.id
            self.partner_id.unlink()
            partner_ids = self.env['res.partner'].search([]).ids
            partner_avail = curr_partner in partner_ids
            self.assertFalse(partner_avail,
                             "Unlink process not working properly")
        except UserError:
            logger.info('Unlinks process works successfully')

    def test_02_check_task_unlink(self):
        '''
        In task, on unlink of task its related analytic lines should
         also be unlinked
        '''
        self.task_id.timesheet_ids = [
            (0, 0,
             {'account_id': self.task_id.project_id.analytic_account_id.id,
              'date': fields.Date.today(),
              'user_id': self.root_user,
              'name': 'Test Activity Line',
              'unit_amount': 2})]
        activity_id = self.task_id.timesheet_ids.id
        self.task_id.unlink()
        analytic_ids = self.env['account.analytic.line'].search([]).ids
        analytic_avail = activity_id in analytic_ids
        self.assertFalse(analytic_avail, "Unlink not working properly")

    def check_account_type_state(self):
        if not self.task_id.project_id.analytic_account_id.type:
            self.task_id.project_id.analytic_account_id.type = 'contract'
        if self.task_id.project_id.analytic_account_id.state in \
                ['draft', 'cancelled', 'close']:
            self.task_id.project_id.analytic_account_id.set_open()
        return self.task_id.project_id.analytic_account_id

    def test_03_check_analytic_line_creation_with_state_cancel(self):
        '''
        In account.analytic.line, if related account is in
        cancelled state than assignment should not be allowed else
        assign its related to_invoice value
        '''
        try:
            # Check with Cancel state
            acc = self.check_account_type_state()
            acc.set_cancel()
            self.task_id.timesheet_ids = [
                (0, 0,
                 {'date': fields.Date.today(),
                  'user_id': self.root_user,
                  'name': 'Test Activity Line1',
                  'unit_amount': 2})]
        except UserError:
            logger.info('Analytic line creation works properly')

    def test_04_check_analytic_line_creation_with_state_closed(self):
        '''
        In account.analytic.line, if related account is in closed
        state than assignment should not be allowed else
        assign its related to_invoice value
        '''
        try:
            # Check with Close state
            acc = self.check_account_type_state()
            acc.set_close()
            self.task_id.timesheet_ids = [
                (0, 0,
                 {'date': fields.Date.today(),
                  'user_id': self.root_user,
                  'name': 'Test Activity Line2',
                  'unit_amount': 2})]
        except UserError:
            logger.info('Analytic line creation works properly')

    def test_05_check_onchange_account_id(self):
        '''
        Onchange of account_id in account.analytic.line, its to_invoice
         field value should be set as its relative active
         task -> project -> analytic_account -> field: to_invoice
        '''
        self.project_id.on_partner_id_change()
        self.task_id.timesheet_ids = [
            (0, 0,
             {'date': fields.Date.today(),
              'user_id': self.root_user,
              'name': 'Test Activity Line1',
              'unit_amount': 2})]
        # Check to_invoice assignment
        self.assertEqual(
            self.task_id.timesheet_ids.to_invoice.id,
            self.task_id.project_id.analytic_account_id.to_invoice.id,
            "Onchange account_id not working properly")
