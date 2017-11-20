# Part of Flectra See LICENSE file for full copyright and licensing details.

import time
import datetime
import flectra.tools as tools
from flectra import api, fields, models, _


class PartnerFollowupStatistics(models.Model):
    _name = "partner.followup.statistics"
    _description = "Partner Follow-up Statistics"
    _rec_name = 'partner_id'
    _auto = False

    _depends = {
        'account.move.line': [
            'account_id', 'company_id', 'credit', 'date', 'debit',
            'date_payment_followup', 'payment_followup_line_id', 'partner_id',
            'full_reconcile_id',
        ],
        'account.account': ['user_type_id'],
    }

    @api.multi
    def _compute_invoice_partner_id(self):
        for obj in self:
            obj.invoice_partner_id = obj.partner_id.address_get(
                adr_pref=['invoice']).get('invoice', obj.partner_id.id)

    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    first_move_date = fields.Date('First move Date', readonly=True)
    last_move_date = fields.Date('Last move Date', readonly=True)
    date_payment_followup = fields.Date('Follow-up Date', readonly=True)
    max_fup_id = fields.Many2one('payment.followup.line',
                                 'Max Follow Up Level', readonly=True,
                                 ondelete="cascade")
    amount_balance = fields.Float('Balance', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    invoice_partner_id = fields.Many2one('res.partner',
                                         compute='_compute_invoice_partner_id',
                                         string='Invoice Address')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'partner_followup_statistics')
        self._cr.execute("""
            create view partner_followup_statistics as (
                SELECT
                    l.partner_id * 10000::bigint + l.company_id as id,
                    l.partner_id AS partner_id,
                    min(l.date) AS first_move_date,
                    max(l.date) AS last_move_date,
                    max(l.date_payment_followup) AS date_payment_followup,
                    max(l.payment_followup_line_id) AS max_fup_id,
                    sum(l.debit - l.credit) AS amount_balance,
                    l.company_id as company_id
                FROM
                    account_move_line l
                    LEFT JOIN account_account a ON (l.account_id = a.id)
                WHERE
                    a.user_type_id IN (SELECT id FROM account_account_type
                    WHERE type = 'receivable') AND
                    l.full_reconcile_id is NULL AND
                    l.partner_id IS NOT NULL
                    GROUP BY
                    l.partner_id, l.company_id
            )""")


class SendingFollowupResults(models.TransientModel):
    _name = 'sending.followup.results'
    _description = 'Sending Followup Results'

    def download_report(self):
        return self.env.context.get('report_data')

    def process_done(self):
        return {}

    @api.multi
    def _compute_get_description(self):
        self.get_description = self.env.context.get('get_description')

    @api.multi
    def _compute_get_printing(self):
        self.get_printing = self.env.context.get('get_printing')

    get_description = fields.Text(
        "Description", readonly=True, compute='_compute_get_description',
        default=lambda self: self.env.context.get('get_description'))
    get_printing = fields.Boolean(
        "Printing Needed", compute='_compute_get_printing',
        default=lambda self: self.env.context.get('get_printing'))


class PartnerFollowupMails(models.TransientModel):
    _name = 'partner.followup.mails'
    _description = 'Payment Follow-up Printing & Send Mail to Customers'

    @api.multi
    def _get_fup_id(self):

        if self.env.context.get('active_model', 'ir.ui.menu') == \
                'payment.followup':
            return self.env.context.get('active_id', False)
        company_id = self.env.user.company_id.id
        followp_id = self.env['payment.followup'].search(
            [('company_id', '=', company_id)])
        return followp_id and followp_id[0] or False

    date = fields.Date('Follow-up Sending Date', required=True,
                       default=lambda *a: time.strftime('%Y-%m-%d'))
    payment_followup_id = fields.Many2one('payment.followup', 'Payment Follow-Up',
                             default=_get_fup_id, required=True,
                             readonly=True)
    partner_ids = fields.Many2many('partner.followup.statistics',
                                   string="Partners")
    company_id = fields.Many2one('res.company', store=True, readonly=True,
                                 related='payment_followup_id.company_id')
    mail_confirmation = fields.Boolean('Send E-mail Confirmation')
    mail_subject = fields.Char('E-mail Subject', size=64,
                               default=_('Invoices Reminder'))
    on_partner_lang = fields.Boolean('Send Email in Partner Language',
                                     default=True)
    mail_body = fields.Text('Email Body', default="")
    fup_summary = fields.Text('Follow-up Summary', readonly=True)
    check_print = fields.Boolean('Check Follow-up Print')

    @api.multi
    def get_filtered_partners(self, partner_ids, data):
        partner_obj = self.env['res.partner']
        resulttext = " "
        dict = {}
        count = 0
        count_print = 0
        count_mails = 0
        count_overdue = 0
        partner_ids_to_print = []
        for partner in self.env['partner.followup.statistics'].browse(
                partner_ids):
            name = \
                partner.partner_id.wo_legal_process_followup_line_id.name
            if partner.max_fup_id.manual_activity:
                partner_obj._get_partner_manual_action([partner.partner_id.id])
                count = count + 1
                key = \
                    partner.partner_id.user_id.name or \
                    _("Anybody")
                if key not in dict.keys():
                    dict[key] = 1
                else:
                    dict[key] = dict[key] + 1
            if partner.max_fup_id.reminder_mail:
                count_overdue += partner.partner_id.send_overdue_mail()
                count_mails += 1
            if partner.max_fup_id.reminder_communication:
                partner_ids_to_print.append(partner.id)
                count_print += 1
                message = "%s<I> %s </I>%s" % \
                          (_("Follow-up letter of "),
                           name,
                           _(" will be sent"))
                partner.partner_id.message_post(body=message)
        if count_overdue == 0:
            resulttext += str(count_mails) + _(" email(s) sent")
        else:
            resulttext += str(count_mails) + \
                          _(" email(s) should have been sent, but ") + \
                          str(count_overdue) + _(
                " had unknown email address(es)") + "\n <BR/> "
        resulttext += "<BR/>" + str(count_print) + \
                      _(" letter(s) in report") + " \n <BR/>" + \
                      str(count) + \
                      _(" manual action(s) assigned:")
        get_printing = False
        if count_print > 0:
            get_printing = True
        resulttext += "<p align=\"center\">"
        for item in dict:
            resulttext = resulttext + "<li>" + item + ":" + \
                         str(dict[item]) + "\n </li>"
        resulttext += "</p>"
        final_result = {}
        action = partner_obj.browse(
            partner_ids_to_print)._get_partner_fup_report_print(data)
        final_result['action'] = action or {}
        final_result['resulttext'] = resulttext
        final_result['get_printing'] = get_printing
        return final_result

    def get_updated_followup_level(self, to_update, partner_list, date):
        for value in to_update.keys():
            if to_update[value]['partner_id'] in partner_list:
                self.env['account.move.line'].browse([int(value)]).write(
                    {'payment_followup_line_id': to_update[value]['level'],
                     'date_payment_followup': date})

    def get_manual_action_clear(self, partner_list):
        partner_list_ids = \
            [partner.partner_id.id for partner in
             self.env['partner.followup.statistics'].browse(partner_list)]
        partners_to_clear = []
        for partner in self.env['res.partner'].search(
                ['&', ('id', 'not in', partner_list_ids), '|',
                 ('user_id', '!=', False),
                 ('upcoming_activity_date', '!=', False)]):
            if not partner.move_line_ids:
                partners_to_clear.append(partner.id)
        self.env['res.partner'].browse(partners_to_clear).set_action_done()
        return len(partners_to_clear)

    @api.multi
    def generate_and_send_mail_process(self):
        context = dict(self.env.context or {})
        partner_details = self._get_partner_fup_detail()
        partner_list = partner_details['partner_ids']
        to_update = partner_details['to_update']
        date = self.date
        data = self.read([])[0]
        data['payment_followup_id'] = data['payment_followup_id'][0]
        self.get_updated_followup_level(to_update, partner_list, date)
        new_context = context.copy()
        filtered_partner = self.with_context(
            new_context).get_filtered_partners(partner_list, data)
        context.update(new_context)
        action_clear = self.get_manual_action_clear(partner_list)
        if action_clear > 0:
            filtered_partner['resulttext'] = \
                filtered_partner['resulttext'] + "<li>" + \
                _("%s partners have no credits and as such the action is"
                  " cleared") % (str(action_clear)) + "</li>"
        mod_obj = self.env['ir.model.data']
        model_data_ids = mod_obj.search(
            [('model', '=', 'ir.ui.view'),
             ('name', '=', 'view_payment_followup_sending_results')])
        resource_id = \
            model_data_ids.read(['res_id']) and \
            model_data_ids.read(['res_id'])[0] and \
            model_data_ids.read(['res_id'])[0]['res_id']
        context.update({'get_description': filtered_partner['resulttext'],
                        'get_printing': filtered_partner['get_printing'],
                        'report_data': filtered_partner['action']})
        return {
            'name': _('Send Letters and Emails: Actions Summary'),
            'view_type': 'form',
            'context': context,
            'view_mode': 'tree,form',
            'res_model': 'sending.followup.results',
            'views': [(resource_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def _get_follow_up_msg(self):
        return self.env.user.company_id.follow_up_msg

    def _get_partner_fup_detail(self):
        data = self
        company_id = data.company_id.id
        self._cr.execute(
            "SELECT "
            "   l.partner_id,"
            "   l.payment_followup_line_id,"
            "   l.date_maturity,"
            "   l.date,"
            "   l.id "
            "FROM "
            "   account_move_line AS l"
            "   LEFT JOIN account_account a ON (l.account_id=a.id)"
            "WHERE "
            "   l.full_reconcile_id IS NULL AND "
            "   a.user_type_id IN (SELECT id FROM account_account_type "
            "       WHERE type = 'receivable')"
            "   AND (l.partner_id is NOT NULL)"
            "   AND (l.debit > 0)"
            "   AND (l.company_id = %s)"
            "   AND (l.blocked = False)"
            "ORDER BY l.date" % (company_id))

        move_lines = self._cr.fetchall()
        old = None
        fups = {}
        payment_followup_id = 'payment_followup_id' in self.env.context and \
                 self.env.context['payment_followup_id'] or data.payment_followup_id.id
        date = 'date' in self.env.context and self.env.context['date'] or \
               data.date

        current_date = datetime.date(*time.strptime(date,
                                                    '%Y-%m-%d')[:3])
        self._cr.execute(
            "SELECT * "
            "FROM payment_followup_line "
            "WHERE payment_followup_id=%s "
            "ORDER BY waiting_period", (payment_followup_id,))

        for result in self._cr.dictfetchall():
            delay = datetime.timedelta(days=result['waiting_period'])
            fups[old] = (current_date - delay, result['id'])
            old = result['id']

        partner_list = []
        to_update = {}

        for partner_id, payment_followup_line_id, date_maturity, date, id in \
                move_lines:
            if not partner_id:
                continue
            if payment_followup_line_id not in fups:
                continue
            stat_line_id = partner_id * 10000 + company_id
            if date_maturity:
                if date_maturity <= fups[payment_followup_line_id][0].strftime(
                        '%Y-%m-%d'):
                    if stat_line_id not in partner_list:
                        partner_list.append(stat_line_id)
                    to_update[str(id)] = {
                        'level': fups[payment_followup_line_id][1],
                        'partner_id': stat_line_id}
            elif date and date <= fups[payment_followup_line_id][0].strftime(
                    '%Y-%m-%d'):
                if stat_line_id not in partner_list:
                    partner_list.append(stat_line_id)
                to_update[str(id)] = {'level': fups[payment_followup_line_id][1],
                                      'partner_id': stat_line_id}
        return {'partner_ids': partner_list, 'to_update': to_update}
