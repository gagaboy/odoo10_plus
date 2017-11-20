# Part of Flectra See LICENSE file for full copyright and licensing details.
import datetime

from dateutil.relativedelta import relativedelta
from flectra import fields
from flectra.tests.common import TransactionCase
from flectra.tools import DEFAULT_SERVER_DATE_FORMAT


class TestPaymentFollowup(TransactionCase):
    def setUp(self):
        super(TestPaymentFollowup, self).setUp()

        self.partner = self.env['res.partner']

        self.wizard = self.env['partner.followup.mails']
        self.fup = self.env['payment.followup']
        self.main_company = self.env.ref('base.main_company')

        self.account_user_type = self.env.ref(
            'account.data_account_type_receivable')
        self.account_id = self.env['account.account'].create(
            {'code': 'X1012', 'name': 'Debtors - (test)',
             'reconcile': True, 'company_id': self.main_company.id,
             'user_type_id': self.account_user_type.id})

        self.partner_id = self.partner.create(
            {'name': 'Test Company',
             'email': 'test@localhost',
             'is_company': True,
             'property_account_receivable_id': self.account_id.id,
             'property_account_payable_id': self.account_id.id,
             })

        self.payment_followup_id = self.env.ref("payment_followup.payment_followup_demo")

        self.current_date = datetime.datetime.strptime(
            fields.Date.today(), DEFAULT_SERVER_DATE_FORMAT)

    def test_00_send_followup_after_3_days(self):
        result = self.current_date + relativedelta(days=3)
        self.wizard_id = self.wizard.with_context(
            {"payment_followup_id": self.payment_followup_id.id}).create(
            {'date': result.strftime(DEFAULT_SERVER_DATE_FORMAT),
             'payment_followup_id': self.payment_followup_id.id
             })
        self.wizard_id.with_context(
            {"payment_followup_id": self.payment_followup_id.id}).generate_and_send_mail_process()
        self.assertFalse(
            self.partner_id.followup_line_id,
            "Updated to the follow-up level which should not be done")
