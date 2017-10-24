from flectra.tests.common import TransactionCase


class TestCurrencyRates(TransactionCase):

    def setUp(self):
        super(TestCurrencyRates, self).setUp()
        self.company = self.env['res.company']

    def test_currency_rate(self):
        '''
            Create config companies and test currencies.
        '''
        company_ecb = self.company.create({
            'name': 'Test Company for Currency ECB',
            'provider': 'ecb'
        })
        company_yahoo = self.company.create({
            'name': 'Test Company for Currency YAHOO',
            'provider': 'yahoo'
        })
        company_fta = self.company.create({
            'name': 'Test Company for Currency FTA',
            'provider': 'fta'
        })
        company_nbp = self.company.create({
            'name': 'Test Company for Currency NBP',
            'provider': 'nbp'
        })

        company_ecb._update_currency_ecb()
        company_yahoo._get_updated_currency_yahoo()
        company_fta.currencyConverterfta()
        company_nbp.get_updated_currency_nbp()
