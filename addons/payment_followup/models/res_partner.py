# Part of Flectra See LICENSE file for full copyright and licensing details.

from lxml import etree
from flectra import api, fields, models, _
from flectra.exceptions import UserError
from flectra.tools.misc import formatLang
from functools import reduce

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.multi
    def write(self, vals):
        if vals.get("user_id", False):
            for partner in self:
                if partner.user_id != \
                        vals["user_id"]:
                    responsible_partner_id = self.env["res.users"].browse(
                        vals['user_id']).partner_id.id
                    self.env["mail.thread"].message_post(
                        body=_("You became responsible to do the next "
                               "action for the payment follow-up of") +
                        " <b><a href='#id=" + str(partner.id) +
                        "&view_type=form&model=res.partner'> " +
                        partner.name + " </a></b>",
                        type='comment',
                        subtype="mail.mt_comment",
                        model='res.partner', res_id=partner.id,
                        partner_ids=[responsible_partner_id])
        return super(ResPartner, self).write(vals)

    @api.multi
    def _compute_latest_fup_details(self):
        company = False
        for partner in self:
            if not partner.company_id:
                company = self.env.user.company_id.id
            else:
                company = self.env['res.company'].browse(
                    partner.company_id.id).id
            amls = partner.move_line_ids
            latest_date = latest_level = latest_days = False
            latest_level_without_lit = latest_days_without_lit = False
            for aml in amls:
                if (aml.company_id.id == company) and \
                        aml.payment_followup_line_id and \
                        (not latest_days or
                            latest_days < aml.payment_followup_line_id.waiting_period):
                    latest_days = aml.payment_followup_line_id.waiting_period
                    latest_level = aml.payment_followup_line_id.id
                if (aml.company_id.id == company) and \
                        (not latest_date or (aml.date_payment_followup and
                                             latest_date < aml.date_payment_followup)):
                    latest_date = aml.date_payment_followup
                if (aml.company_id.id == company) and \
                        (not aml.blocked) and \
                        (aml.payment_followup_line_id and
                            (not latest_days_without_lit or
                                latest_days_without_lit <
                                aml.payment_followup_line_id.waiting_period)):
                    latest_days_without_lit = \
                        aml.payment_followup_line_id.waiting_period
                    latest_level_without_lit = aml.payment_followup_line_id.id
            partner.followup_date = latest_date
            partner.followup_line_id = latest_level
            partner.wo_legal_process_followup_line_id = \
                latest_level_without_lit

    @api.multi
    def _compute_payment_rel_details(self):
        company = self.env.user.company_id
        current_date = fields.Date.today()
        for partner in self:
            worst_due_date = False
            amt_tobe_paid = overdue_amt = 0.0
            for aml in partner.move_line_ids:
                if (aml.company_id == company):
                    date_maturity = aml.date_maturity or aml.date
                    if not worst_due_date or date_maturity < worst_due_date:
                        worst_due_date = date_maturity
                    amt_tobe_paid += aml.amount_balance
                    if (date_maturity <= current_date):
                        overdue_amt += aml.amount_balance
            partner.amt_tobe_paid = amt_tobe_paid
            partner.overdue_amt = overdue_amt
            partner.expected_payment_date = worst_due_date

    @api.multi
    def _get_partner_manual_action(self, partner_ids):
        for partner in self.browse(partner_ids):
            action_text = ""
            f_level = partner.wo_legal_process_followup_line_id
            todo_activity = f_level.todo_activity
            if partner.upcoming_activity:
                action_text = (partner.upcoming_activity or ''
                               ) + "\n" + (todo_activity or '')
            else:
                action_text = todo_activity or ''
            action_date = \
                partner.upcoming_activity_date or \
                fields.Date.today()
            user_id = False
            if partner.user_id:
                user_id = partner.user_id.id
            else:
                p = f_level.user_id
                user_id = p and p.id or False
            partner.write({'upcoming_activity_date': action_date,
                           'upcoming_activity': action_text,
                           'user_id': user_id})

    @api.multi
    def _get_partner_fup_report_print(self, data):
        data['partner_ids'] = self.ids
        datas = {
            'ids': self.ids,
            'model': 'payment.followup',
            'form': data
        }
        return self.env.ref(
            'payment_followup.action_report_payment_followup').report_action(
            self, data=datas)

    @api.multi
    def print_overdue_payment(self):
        assert (len(self.ids) == 1)
        company_id = self.env.user.company_id.id
        if not self.env['account.move.line'].search([
            ('partner_id', '=', self.ids[0]),
            ('account_id.user_type_id.type', '=', 'receivable'),
            ('full_reconcile_id', '=', False),
            ('company_id', '=', company_id),
            '|', ('date_maturity', '=', False),
            ('date_maturity', '<=', fields.Date.today()),
        ]):
            raise UserError(_('Error! \nThe partner does not have any '
                              'accounting entries to print in the overdue '
                              'report for the current company.'))
        self.message_post(body=_('Printed overdue payments report'))
        wizard_partner_ids = [self.ids[0] * 10000 + company_id]
        followup_ids = self.env['payment.followup'].search(
            [('company_id', '=', company_id)])
        if not followup_ids:
            raise UserError(_('Error! \nThere is no followup plan '
                              'defined for the current company.'))
        data = {
            'date': fields.date.today(),
            'payment_followup_id': followup_ids[0] and followup_ids[0].id,
        }
        return self.env['res.partner'].browse(
            wizard_partner_ids)._get_partner_fup_report_print(data)

    @api.multi
    def send_overdue_mail(self):

        context = self.env.context.copy()
        context['followup'] = True
        mtp = self.env['mail.template']
        unknown_mails = 0
        template = 'payment_followup.email_template_payment_followup_default'
        for partner in self:
            partners_to_email = [child for child in partner.child_ids if
                                 child.type == 'invoice' and child.email]
            if not partners_to_email and partner.email:
                partners_to_email = [partner]
            if partners_to_email:
                level = partner.wo_legal_process_followup_line_id
                for partner_to_email in partners_to_email:
                    if level and level.reminder_mail and \
                            level.template_id and \
                            level.template_id.id:
                        level.template_id.with_context(context).send_mail(
                            partner_to_email.id)
                    else:
                        template_id = self.env.ref(template).id
                        mtp.browse(template_id).send_mail(
                            partner_to_email.id)
                if partner not in partners_to_email:
                    partner.message_post(body=_(
                        'Overdue email sent to %s' % ', '.join(
                            ['%s <%s>' % (partner.name, partner.email)
                             for partner in partners_to_email])))
            else:
                unknown_mails = unknown_mails + 1
                action_text = _("Email not sent because of email address of "
                                "partner not filled in")
                if partner.upcoming_activity_date:
                    payment_action_date = min(
                        fields.Date.today(),
                        partner.upcoming_activity_date)
                else:
                    payment_action_date = fields.Date.today()
                if partner.upcoming_activity:
                    upcoming_activity = \
                        partner.upcoming_activity + \
                        " \n " + action_text
                else:
                    upcoming_activity = action_text
                partner.with_context(context).write({
                    'upcoming_activity_date': payment_action_date,
                    'upcoming_activity': upcoming_activity})
        return unknown_mails

    @api.multi
    def get_followup_details(self):
        self.ensure_one()
        payment_followup_print = \
            self.env['report.payment_followup.report_payment_followup']
        assert len(self.ids) == 1
        partner = self.commercial_partner_id
        followup_table = ''
        if partner.move_line_ids:
            company = self.env.user.company_id
            current_date = fields.Date.today()
            final_res = payment_followup_print._get_related_move_lines(
                partner, company.id)

            for currency_dict in final_res:
                currency = currency_dict.get(
                    'line', [{
                        'currency_id': company.currency_id
                    }])[0]['currency_id']
                followup_table += '''
                <table border="2" width=100%%>
                <tr>
                    <td>''' + _("Invoice Date") + '''</td>
                    <td>''' + _("Description") + '''</td>
                    <td>''' + _("Reference") + '''</td>
                    <td>''' + _("Due Date") + '''</td>
                    <td>''' + _("Amount") + " (%s)" % (
                    currency.symbol) + '''</td>
                    <td>''' + _("Lit.") + '''</td>
                </tr>
                '''
                total = 0
                for aml in currency_dict['line']:
                    block = aml['blocked'] and 'X' or ' '
                    total += aml['amount_balance']
                    strbegin = "<TD>"
                    strend = "</TD>"
                    date = aml['date_maturity'] or aml['date']
                    if date <= current_date and aml['amount_balance'] > 0:
                        strbegin = "<TD><B>"
                        strend = "</B></TD>"
                    followup_table += \
                        "<TR>" + strbegin + str(aml['date']) + \
                        strend + strbegin + aml['name'] + \
                        strend + strbegin + \
                        (aml['ref'] or '') + \
                        strend + strbegin + \
                        str(date) + strend + strbegin + str(aml['amount_balance']) + \
                        strend + strbegin + block + strend + \
                        "</TR>"

                total = reduce(lambda x, y: x + y['amount_balance'],
                               currency_dict['line'], 0.00)

                total = formatLang(self.env, total, dp='Account',
                                   currency_obj=currency)
                followup_table += '''<tr> </tr>
                                </table>
                                <br>
                                <div align="right"> <B>
                                <font style="font-size: 14px;">''' + \
                                  _("Amount due") + ''' : %s
                                  </div>''' % (total)
        return followup_table

    @api.multi
    def set_action_done(self):
        return self.write({
            'upcoming_activity_date': False,
            'upcoming_activity': '',
            'payment_responsible_id': False})

    @api.multi
    def _search_payment_earliest_date(self, operator, operand):
        args = [('expected_payment_date', operator, operand)]
        company_id = self.env.user.company_id.id
        having_where_clause = ' AND '.join(
            map(lambda x: "(MIN(l.date_maturity) %s '%%s')" % (x[1]), args))
        having_values = [x[2] for x in args]
        having_where_clause = having_where_clause % (having_values[0])
        query = 'SELECT partner_id FROM account_move_line l ' \
                'WHERE account_id IN ' \
                '(SELECT id FROM account_account ' \
                'WHERE user_type_id IN ' \
                '(SELECT id FROM account_account_type ' \
                'WHERE type=\'receivable\')) AND l.company_id = %s ' \
                'AND l.full_reconcile_id IS NULL ' \
                'AND partner_id IS NOT NULL GROUP BY partner_id '
        query = query % (company_id)
        if having_where_clause:
            query += ' HAVING %s ' % (having_where_clause)
        self._cr.execute(query)
        res = self._cr.fetchall()
        if not res:
            return [('id', '=', '0')]
        return [('id', 'in', [x[0] for x in res])]

    @api.multi
    def _get_query(self, args, overdue_only=False):
        company_id = self.env.user.company_id.id
        having_where_clause = ' AND '.join(
            map(lambda x: '(SUM(bal2) %s %%s)' % (x[1]), args))
        having_values = [x[2] for x in args]
        having_where_clause = having_where_clause % (having_values[0])
        overdue_only_str = overdue_only and 'AND date_maturity <= NOW()' or ''
        return ('''SELECT pid AS partner_id, SUM(bal2) FROM
                            (SELECT CASE WHEN bal IS NOT NULL THEN bal
                            ELSE 0.0 END AS bal2, p.id as pid FROM
                            (SELECT (debit-credit) AS bal, partner_id
                            FROM account_move_line l
                            WHERE account_id IN
                                    (SELECT id FROM account_account
                                    WHERE user_type_id IN (SELECT id
                                    FROM account_account_type
                                    WHERE type=\'receivable\'
                                    ))
                            %s AND full_reconcile_id IS NULL
                            AND company_id = %s) AS l
                            RIGHT JOIN res_partner p
                            ON p.id = partner_id ) AS pl
                            GROUP BY pid HAVING %s''') % (
            overdue_only_str, company_id, having_where_clause)

    @api.multi
    def _search_amount_due(self, operator, operand):
        args = [('amt_tobe_paid', operator, operand)]
        query = self._get_query(
            args, overdue_only=False)
        self._cr.execute(query)
        res = self._cr.fetchall()
        if not res:
            return [('id', '=', '0')]
        return [('id', 'in', [x[0] for x in res])]

    @api.multi
    def _search_amount_overdue(self, operator, operand):
        args = [('overdue_amt', operator, operand)]
        query = self._get_query(
            args, overdue_only=True)
        self._cr.execute(query)
        res = self._cr.fetchall()
        if not res:
            return [('id', '=', '0')]
        return [('id', 'in', [x[0] for x in res])]

    move_line_ids = fields.One2many(
        'account.move.line', 'partner_id', string='Move Lines',
        domain=[('full_reconcile_id', '=', False),
                ('account_id.user_type_id.type', '=', 'receivable')])
    comment = fields.Text('Comments',
       track_visibility="onchange", copy=False)
    user_id = fields.Many2one(
        'res.users', ondelete='set null', string='User',
        track_visibility="onchange", copy=False)
    upcoming_activity = fields.Text(
        'Schedule Action', copy=False, track_visibility="onchange")
    upcoming_activity_date = fields.Date(
        'Upcoming Activity Date', copy=False)
    followup_line_id = fields.Many2one(
        'payment.followup.line',
        compute='_compute_latest_fup_details',
        string="Follow-up Line")
    followup_date = fields.Date(
        compute='_compute_latest_fup_details',
        string="Latest Payment Follow-up Date")
    wo_legal_process_followup_line_id = fields.Many2one(
        'payment.followup.line',
        compute='_compute_latest_fup_details',
        string="Follow-up Line w/o Legal Process")
    expected_payment_date = fields.Date(
        compute='_compute_payment_rel_details', string="Payment Expected Date",
        search='_search_payment_earliest_date')
    amt_tobe_paid = fields.Float(
        compute='_compute_payment_rel_details', string="Amount to be Paid",
        store=False, search='_search_amount_due')
    overdue_amt = fields.Float(
        compute='_compute_payment_rel_details', string="Overdue Amount",
        search='_search_amount_overdue')

    @api.multi
    def open_follow_ups(self):
        form_view = self.env.ref(
            'payment_followup.view_res_partner_form')
        return {
            'name': _('Follow Ups'),
            'res_model': 'res.partner',
            'res_id': self.id,
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
        }
