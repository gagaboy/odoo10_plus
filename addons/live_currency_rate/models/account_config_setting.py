# Part of Flectra. See LICENSE file for full copyright and licensing details.

import datetime
from lxml import etree
import json
from dateutil.relativedelta import relativedelta
import requests
from flectra import api, fields, models, _
from flectra.exceptions import UserError



class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    interval_unit = fields.Selection(related="company_id.interval_unit",)
    provider = fields.Selection(related="company_id.provider",)
    execution_date = fields.Date(related="company_id.execution_date")

    @api.onchange('interval_unit')
    def onupdate_interval_unit_provider(self):
        dict = {'daily': relativedelta(days=+1),
                'weekly': relativedelta(weeks=+1),
                'manually': False,
                'monthly': relativedelta(months=+1)}
        if self.interval_unit:
            next_update = dict[self.interval_unit]
        else:
            self.execution_date = False
            return
        if next_update:
            self.execution_date = datetime.datetime.now() + next_update

    @api.multi
    def live_currency_rates_update(self):
        companies = \
            self.env['res.company'].browse(
                [record.company_id.id for record in self])
        companies.currency_getter_factory()

class ResCompany(models.Model):
    _inherit = 'res.company'

    interval_unit = fields.Selection([
        ('monthly', 'Monthly'),
        ('weekly', 'Weekly'),
        ('daily', 'Daily'),
        ('manually', 'Manually')],
        default='manually', string='Interval Unit')
    provider = fields.Selection([('yahoo', 'Yahoo'),
                                 ('ecb', 'European Central Bank'),
                                 ('fta',
                                  'Federal Tax Administration (Switzerland)'),
                                 ('nbp', 'Narodowy Bank Polski')],
                                default='yahoo', string='Service Provider')
    execution_date = fields.Date(string="Next Execution Date")

    @api.multi
    def currency_getter_factory(self):
        result = True
        for obj in self:
            provider = obj.provider
            dict = {
                'yahoo': '_get_updated_currency_yahoo',
                'ecb': '_ecb_live_currency_rate',
                'fta': 'currencyConverterfta',
                'nbp': 'get_updated_currency_nbp',
            }
            if provider:
                result = dict[provider]
                if hasattr(obj, result):
                    result = getattr(obj, result)()
            if not result:
                raise UserError(_("There is problems with web service today \
                but it will be resolved. We're sorry for any inconvenience \
                this may have caused."))

    def currencyConverteryahoo(self, currency_from, currency_to):
        currency_pairs = currency_from + currency_to
        yql_base_url = "https://query.yahooapis.com/v1/public/yql"
        yql_query = 'select%20*%20from%20yahoo.finance.xchange' \
                    + '%20where%20pair%20in%20("' + currency_pairs + '")'
        yql_query_url = \
            yql_base_url + \
            "?q=" + yql_query + \
            "&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys"
        try:
            url = requests.get(yql_query_url)
            response = url.content
            currency_data = json.loads(response)
            if not currency_data.get('query') or \
                    not currency_data['query'].get('results'):
                return False
            rates = currency_data['query']['results']['rate']['Rate']
            return rates

        except Exception as e:
            if hasattr(e, 'code'):
                return False
            elif hasattr(e, 'reason'):
                return False

    def _get_updated_currency_yahoo(self):
        currency_obj = self.env['res.currency']
        rate_obj = self.env['res.currency.rate']
        currencies = currency_obj.search([])
        currency_from = self.currency_id.name
        currency_to_list = \
            [currency.name for currency in currencies if currency_from != currency.name]
        for currency_to in currency_to_list:
            currency_output = \
                self.currencyConverteryahoo(currency_from, currency_to)
            currency = currency_obj.search([('name', '=', currency_to)],
                                           limit=1)
            if currency:
                rate_obj.create(
                    {'currency_id': currency.id, 'rate': currency_output,
                     'name': fields.Date.today(), 'company_id': self.id})
        return True

    def get_url(self, url):
        try:
            objfile = requests.get(url)
            rawfile = objfile.content
            objfile.close()
            return rawfile

        except IOError:
            raise UserError(_('Web Service does not exist !'))

    def rate_retrieve(self, dom, ns, curr):
        res = {}
        xpath_curr_rate = "/gesmes:Envelope/def:Cube/def:Cube/" + \
                          "def:Cube[@currency='%s']/@rate" % (curr.upper())
        if dom.xpath(xpath_curr_rate, namespaces=ns):
            res['rate_currency'] = float(
                dom.xpath(xpath_curr_rate, namespaces=ns)[0])
        return res

    def _ecb_live_currency_rate(self):
        currency_obj = self.env['res.currency']
        rate_obj = self.env['res.currency.rate']
        main_currency = self.currency_id.name
        currencies = currency_obj.search([])
        currencies = [currency.name for currency in currencies]
        url = "http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
        try:
            rawfile = self.get_url(url)
        except:
            return False
        dom = etree.fromstring(rawfile)
        ecb_ns = {'gesmes': 'http://www.gesmes.org/xml/2002-08-01',
                  'def': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}
        if main_currency in currencies:
            currencies.remove(main_currency)
        if main_currency != 'EUR':
            main_curr_data = self.rate_retrieve(dom, ecb_ns, main_currency)
        for currency in currencies:
            if currency == 'EUR':
                rate = 1 / main_curr_data['rate_currency']
            else:
                curr_data = self.rate_retrieve(dom, ecb_ns, currency)
                rate = curr_data['rate_currency']
            currency = currency_obj.search([('name', '=', currency)],
                                           limit=1)
            if currency:
                rate_obj.create(
                    {'currency_id': currency.id, 'rate': rate,
                     'name': fields.Date.today(), 'company_id': self.id})
        return True

    def rate_retrieve_fta(self, dom, ns, curr):
        res = {}
        xpath_rate_currency = \
            "/def:wechselkurse/def:devise[@code='%s']/def:kurs/text()" % (
                curr.lower())
        xpath_rate_ref = \
            "/def:wechselkurse/def:devise[@code='%s']/def:waehrung/text()" % (
                curr.lower())
        res['rate_currency'] = float(
            dom.xpath(xpath_rate_currency, namespaces=ns)[0])
        res['rate_ref'] = float(
            (dom.xpath(xpath_rate_ref, namespaces=ns)[0]).split(' ')[0])
        return res

    def currencyConverterfta(self):
        currency_obj = self.env['res.currency']
        rate_obj = self.env['res.currency.rate']
        main_currency = self.currency_id.name
        currencies = currency_obj.search([])
        currencies = [currency.name for currency in currencies]
        url = "http://www.afd.admin.ch/" + \
              "publicdb/newdb/mwst_kurse/wechselkurse.php"
        try:
            rawfile = self.get_url(url)
        except:
            return False
        dom = etree.fromstring(rawfile)
        adminch_ns = {
            'def': 'http://www.afd.admin.ch/publicdb/newdb/mwst_kurse'}
        if main_currency in currencies:
            currencies.remove(main_currency)
        if main_currency != 'CHF':
            main_curr_data = \
                self.rate_retrieve_fta(dom, adminch_ns, main_currency)
            main_rate = main_curr_data['rate_currency'] / main_curr_data[
                'rate_ref']
        for currency in currencies:
            if currency == 'CHF':
                rate = main_rate
            else:
                curr_data = self.rate_retrieve_fta(dom, adminch_ns, currency)
                # 1 MAIN_CURRENCY = rate CURR
                if main_currency == 'CHF':
                    rate = curr_data['rate_ref'] / curr_data['rate_currency']
                else:
                    rate = main_rate * curr_data['rate_ref'] / curr_data[
                        'rate_currency']
            currency = currency_obj.search([('name', '=', currency)],
                                           limit=1)
            if currency:
                rate_obj.create(
                    {'currency_id': currency.id, 'rate': rate,
                     'name': fields.Date.today(), 'company_id': self.id})
        return True

    def rate_retrieve_nbp(self, dom, ns, curr):
        res = {}
        xpath_rate_currency = \
            "/tabela_kursow/pozycja[kod_waluty='%s']/kurs_sredni/text()" % (
                curr.upper())
        xpath_rate_ref = \
            "/tabela_kursow/pozycja[kod_waluty='%s']/przelicznik/text()" % (
                curr.upper())
        res['rate_currency'] = \
            float(dom.xpath(xpath_rate_currency,
                            namespaces=ns)[0].replace(',', '.'))
        res['rate_ref'] = float(dom.xpath(xpath_rate_ref, namespaces=ns)[0])
        return res

    def get_updated_currency_nbp(self):
        currency_obj = self.env['res.currency']
        rate_obj = self.env['res.currency.rate']
        main_currency = self.currency_id.name
        currencies = currency_obj.search([])
        currencies = [currency.name for currency in currencies]
        url = 'http://www.nbp.pl/kursy/xml/LastA.xml'
        if main_currency in currencies:
            currencies.remove(main_currency)
        from lxml import etree
        rawfile = self.get_url(url)
        dom = etree.fromstring(rawfile)
        ns = {}
        if main_currency != 'PLN':
            main_curr_data = self.rate_retrieve_nbp(dom, ns, main_currency)
            main_rate = \
                main_curr_data['rate_currency'] / main_curr_data['rate_ref']
        for curr in currencies:
            if curr == 'PLN':
                rate = main_rate
            else:
                curr_data = self.rate_retrieve_nbp(dom, ns, curr)
                if main_currency == 'PLN':
                    rate = curr_data['rate_ref'] / curr_data['rate_currency']
                else:
                    rate = \
                        main_rate * \
                        curr_data['rate_ref'] / curr_data['rate_currency']
            currency = currency_obj.search([('name', '=', curr)],
                                           limit=1)
            if currency and rate:
                rate_obj.create({'currency_id': currency.id, 'rate': rate,
                                 'name': fields.Date.today(),
                                 'company_id': self.id})
        return True

    @api.model
    def run_update_currency_cron(self):
        records = self.search([('execution_date', '<=', fields.Date.today())])
        if records:
            dict = {'daily': relativedelta(days=+1),
                    'weekly': relativedelta(weeks=+1),
                    'monthly': relativedelta(months=+1)}
            to_update = self.env['res.company']
            for record in records:
                if record.interval_unit:
                    next_update = dict[record.interval_unit]
                else:
                    record.execution_date = False
                    continue
                record.execution_date = datetime.datetime.now() + next_update
                to_update += record
            to_update.currency_getter_factory()
