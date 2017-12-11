# Part of Odoo S.A.,Flectra See LICENSE file for full copyright and
# licensing details.

from functools import reduce

from flectra import api, models


class AccountAnalyticRevenue(models.AbstractModel):
    _name = "report.hr_activity_invoice.report_analyticrevenue"

    def _get_journals(self, form, user_id):
        if isinstance(user_id, (int)):
            user_id = [user_id]

        account_analytic_line_ids = self.env['account.analytic.line'].search([
            ('date', '>=', form.get('date_from')),
            ('journal_id', 'in', form.get('journal_ids')),
            ('date', '<=', form.get('date_to')), ('user_id', 'in', user_id),
        ])

        ids = []
        for record in account_analytic_line_ids:
            ids.append(list(set([record.journal_id and record.journal_id.id])))
        return self.env['account.journal'].browse(ids)

    def _line(self, form, journal_ids, user_ids):
        account_analytic_line_ids = self.env['account.analytic.line'].search([
            ('journal_id', 'in', journal_ids),
            ('date', '>=', form.get('date_from')),
            ('user_id', 'in', user_ids),
            ('date', '<=', form.get('date_to')),
        ])
        res = {}
        for line in account_analytic_line_ids:
            if line.account_id.pricelist_id:
                if line.account_id.to_invoice:
                    if line.to_invoice:
                        id = line.to_invoice.id
                        discount = line.to_invoice.factor
                        name = line.to_invoice.name
                    else:
                        discount = 1.0
                        id = -1
                        name = "/"
                else:
                    discount = 0.0
                    name = "Fixed"
                    id = 0
                price_list = line.account_id.pricelist_id.id
                product_id = line.product_id
                if not product_id:
                    product_id = line.product_id.search([
                        ('name', 'like', 'Support')], limit=1)
                price = self.env['product.pricelist'].price_get(
                    product_id.id, line.unit_amount or 1.0,
                    line.account_id.partner_id.id)[price_list]
            else:
                name = "/"
                discount = 1.0
                id = -1
                price = 0.0
            if id not in res:
                res[id] = dict({
                    'name': name,
                    'amount': 0,
                    'cost': 0,
                    'unit_amount': 0,
                    'amount_th': 0
                })
            amount = round(price * line.unit_amount * (
                1 - (discount or 0.0)), 2)
            res[id]['amount_th'] += amount
            if line.invoice_id:
                self._cr.execute('select id from account_analytic_line \
                    where invoice_id=%s' % (line.invoice_id.id))
                total = 0
                for lid in self._cr.fetchall():
                    lid2 = self.env['account.analytic.line'].browse(lid[0])
                    pl = lid2.account_id.pricelist_id and \
                        lid2.account_id.pricelist_id.id or False
                    price = self.env['product.pricelist'].price_get(
                        lid2.product_id.id, lid2.unit_amount or 1.0,
                        lid2.account_id.partner_id.id)[pl]
                    total += price * lid2.unit_amount * (1 - (discount or 0.0))
                if total:
                    procent = line.invoice_id.amount_untaxed / total
                    res[id]['amount'] += amount * procent
                else:
                    res[id]['amount'] += amount
            else:
                res[id]['amount'] += amount

            res[id]['cost'] += line.amount
            res[id]['unit_amount'] += line.unit_amount

        for record in res:
            res[record]['profit'] = res[record]['amount'] + res[record]['cost']
            res[record]['eff'] = res[record]['cost'] and \
                '%d' % (-res[record]['amount'] /
                        res[record]['cost'] * 100) or 0.0
        return res.values()

    def _get_users(self, lines):
        ids = list(set([line.user_id and line.user_id.id for line in lines]))
        return self.env['res.users'].browse(ids)

    @api.model
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        form = data['form']
        journal_ids = form and form['journal_ids'] or []
        user_ids = form and form['employee_ids'] or []

        line = self._line(form, journal_ids, user_ids)
        unit_amount = reduce(lambda x, y: x + y['unit_amount'], line, 0)
        amount = reduce(lambda x, y: x + y['amount'], line, 0)
        cost = reduce(lambda x, y: x + y['cost'], line, 0)
        profit = reduce(lambda x, y: x + y['profit'], line, 0)
        total = reduce(lambda x, y: x + y['cost'], line, 0) and \
            round(reduce(lambda x, y: x + y['amount'], line, 0) / reduce(
                lambda x, y: x + y['cost'], line, 0) * -100, 2)
        dict_total = {
            'unit_amount': unit_amount,
            'amount': amount,
            'cost': cost,
            'profit': profit,
            'total': total,
        }
        j_unit_amount = reduce(lambda x, y: x + y['unit_amount'], line, 0)
        j_amount_th = reduce(lambda x, y: x + y['amount_th'], line, 0)
        j_amount = reduce(lambda x, y: x + y['amount'], line, 0)
        j_cost = reduce(lambda x, y: x + y['cost'], line, 0)
        j_profit = reduce(lambda x, y: x + y['profit'], line, 0)
        j_total = reduce(lambda x, y: x + y['amount'], line, 0) / reduce(
            lambda x, y: x + y['cost'], line, 0) * -100.0
        dict_journal = {
            'j_unit_amount': j_unit_amount,
            'j_amount_th': j_amount_th,
            'j_amount': j_amount,
            'j_cost': j_cost,
            'j_profit': j_profit,
            'j_total': j_total,
        }

        lines = self.env['account.analytic.line'].search([
            ('date', '<=', form.get('date_to')),
            ('date', '>=', form.get('date_from')),
            ('user_id', 'in', form.get('employee_ids')),
            ('journal_id', 'in', form.get('journal_ids')),
        ])

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': form,
            'docs': docs,
            'line': line,
            'lines': lines,
            'user_ids': self._get_users(lines),
            'journal_ids': self._get_journals(form, user_ids),
            'dict_total': dict_total,
            'dict_journal': dict_journal,
        }
