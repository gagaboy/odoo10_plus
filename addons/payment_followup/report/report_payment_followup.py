# Part of Flectra See LICENSE file for full copyright and licensing details.

import time
from collections import defaultdict
from flectra import api, fields, models, _
from flectra.exceptions import UserError


class ReportRappel(models.AbstractModel):
    _name = 'report.payment_followup.report_payment_followup'

    def get_details(self, stat_by_partner_line):
        partner = []
        company = []
        for partner_line in stat_by_partner_line:
            partner.append(partner_line.partner_id.id)
            company.append(partner_line.company_id.id)
        return self._get_related_move_lines(partner, company)

    def _get_related_move_lines(self, partner, company_id):
        moveline_obj = self.env['account.move.line']
        moveline_ids = False
        total = 0
        if isinstance(partner, list):
            moveline_ids = moveline_obj.search([
                ('partner_id', 'in', partner),
                ('company_id', 'in', company_id),
                ('full_reconcile_id', '=', False),
                ('account_id.user_type_id.type', '=', 'receivable'),
                '|', ('date_maturity', '=', False),
                ('date_maturity', '<', fields.Date.today()),
            ])
        else:
            moveline_ids = moveline_obj.search([
                ('partner_id', '=', partner.id),
                ('company_id', '=', company_id),
                ('account_id.user_type_id.type', '=', 'receivable'),
                ('full_reconcile_id', '=', False),
                '|', ('date_maturity', '=', False),
                ('date_maturity', '<', fields.Date.today()),
            ])

        lines_per_currency = defaultdict(list)
        for line in moveline_ids:
            currency = line.currency_id or line.company_id.currency_id
            line_data = {
                'ref': line.ref,
                'name': line.move_id.name,
                'date': line.date,
                'currency_id': currency,
                'date_maturity': line.date_maturity,
                'blocked': line.blocked,
                'amount_balance':
                    line.amount_currency if currency !=
                    line.company_id.currency_id else
                    line.debit - line.credit,
            }
            total = total + line_data['amount_balance']
            lines_per_currency[currency].append(line_data)

        return [{'total': total,
                 'line': lines,
                 'currency': currency} for currency, lines in
                lines_per_currency.items()]

    def _get_partner_details(self, stat_line, payment_followup_id):
        fup_obj = self.env['payment.followup']
        fup_line = fup_obj.browse(payment_followup_id).payment_followup_line
        if not fup_line:
            raise UserError(_('Error! \n '
                              'The followup plan defined for the current '
                              'company does not have any followup action.'))
        default_message = ''
        delay_list = []
        for line in fup_line:
            if not default_message and line.communication:
                default_message = line.communication
            delay_list.append(line.waiting_period)
        delay_list.sort(reverse=True)
        partner_line_ids = self.env['account.move.line'].search(
            [('partner_id', '=', stat_line.partner_id.id),
             ('debit', '!=', False),
             ('blocked', '=', False),
             ('full_reconcile_id', '=', False),
             ('payment_followup_line_id', '!=', False),
             ('company_id', '=', stat_line.company_id.id),
             ('account_id.user_type_id.type', '=', 'receivable'), ])
        partner_max_delay = 0
        partner_max_text = ''
        for i in partner_line_ids:
            if i.payment_followup_line_id.waiting_period > partner_max_delay and \
                    i.payment_followup_line_id.communication:
                partner_max_delay = i.payment_followup_line_id.waiting_period
                partner_max_text = i.payment_followup_line_id.communication
        communication = partner_max_delay and partner_max_text or default_message
        if communication:
            lang_obj = self.env['res.lang']
            lang_ids = lang_obj.search(
                [('code', '=', stat_line.partner_id.lang)], limit=1)
            date_format = lang_ids and lang_ids.date_format or '%Y-%m-%d'
            communication = communication % {
                'date': time.strftime(date_format),
                'partner_name': stat_line.partner_id.name,
                'company_name': stat_line.company_id.name,
                'user_signature': self.env.user.signature or '',
            }
        return communication

    def _get_object(self, ids):
        all_lines = []
        for line in self.env['partner.followup.statistics'].browse(ids):
            if line not in all_lines:
                all_lines.append(line)
        return all_lines

    @api.model
    def get_report_values(self, docids, data=None):
        model = self.env['sending.followup.results']
        ids = self.env.context.get('active_ids') or False
        docs = model.browse(ids)
        return {
            'docs': docs,
            'doc_ids': docids,
            'doc_model': model,
            '_get_partner_details': self._get_partner_details,
            'get_details': self.get_details,
            '_get_object': self._get_object,
            'time': time,
            'data': data and data['form'] or {}}
