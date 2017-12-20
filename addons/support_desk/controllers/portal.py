# -*- coding: utf-8 -*-
# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import http
from flectra.http import request
from flectra.tools.translate import _
from flectra.addons.portal.controllers.portal import get_records_pager, \
    pager as portal_pager, CustomerPortal
from flectra.osv.expression import OR


class CustomerPortal(CustomerPortal):

    def _get_tickets_domain(self, partner):
        return ['|', ('responsible_user_id', '=', request.env.user.id),
                     ('partner_id', 'child_of', request.env.user.partner_id.
                      commercial_partner_id.id)]

    def _prepare_portal_layout_values(self):
        result = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        result['support_ticket_count'] = request.env[
            'supportdesk.ticket'].search_count(
            self._get_tickets_domain(partner))
        return result

    @http.route(['/my/support_tickets', '/my/support_tickets/page/<int:page>'],
                type='http',
                auth="user", website=True)
    def my_tickets(self, page=1, start_date=None, end_date=None,
                   sort=None, search=None, in_search='content',
                   **kw):
        result = self._prepare_portal_layout_values()
        domain = self._get_tickets_domain(request.env.user.partner_id)

        sortings = {
            'name': {'label': _('Subject'), 'order': 'name'},
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'stage': {'label': _('Stage'), 'order': 'stage_id'},
        }

        if not sort:
            sort = 'date'
        order = sortings[sort]['order']

        archive_groups = self._get_archive_groups('supportdesk.ticket', domain)
        if start_date and end_date:
            domain += [('create_date', '>', start_date),
                       ('create_date', '<=', end_date)]

        if search and in_search:
            in_search_filter = []
            if in_search in ('customer', 'all'):
                in_search_filter = OR(
                    [in_search_filter, [('partner_id', 'ilike', search)]])
            if in_search in ('content', 'all'):
                in_search_filter = OR([in_search_filter,
                                       ['|', ('name', 'ilike', search),
                                        ('description', 'ilike', search)]])
                if in_search in ('stage', 'all'):
                    in_search_filter = OR(
                        [in_search_filter, [('stage_id', 'ilike', search)]])
            if in_search in ('message', 'all'):
                in_search_filter = OR([in_search_filter, [
                    ('message_ids.body', 'ilike', search)]])
            domain += in_search_filter

        support_tickets_count = request.env['supportdesk.ticket'].search_count(
            domain)
        pager = portal_pager(
            url="/my/support_tickets",
            url_args={'start_date': start_date,
                      'end_date': end_date,
                      'sortby': sort},
            total=support_tickets_count,
            page=page,
            step=self._items_per_page
        )

        support_tickets = request.env['supportdesk.ticket'].sudo().search(
            domain, order=order, limit=self._items_per_page, offset=pager[
                'offset'])
        request.session['my_tickets_history'] = support_tickets.ids[:50]

        result.update({
            'page_name': 'ticket',
            'pager': pager,
            'date': start_date,
            'tickets': support_tickets,
            'default_url': '/my/support_tickets',
            'sortby': sort,
            'search_in': in_search,
            'search': search,
            'searchbar_sortings': sortings,
            'archive_groups': archive_groups,
        })
        return request.render("support_desk.portal_support_ticket", result)

    @http.route([
        "/supportdesk/ticket/<int:ticket_id>",
        "/supportdesk/ticket/<int:ticket_id>/<token>"
    ], type='http', auth="public", website=True)
    def my_support_tickets_followup(self, support_ticket, access_token=None):
        ticket_obj = request.env['supportdesk.ticket']
        if access_token:
            support_ticket = ticket_obj.sudo().search([
                ('id', '=', support_ticket),
                ('access_token', '=', access_token)])
        elif support_ticket:
            support_ticket = ticket_obj.browse(
                support_ticket)
        else:
            return request.redirect('/my')
        ticket_history = request.session.get('my_tickets_history', [])
        values = {'support_ticket': support_ticket}
        values.update(get_records_pager(ticket_history, access_token))
        return request.render("support_desk.support_tickets_followup", values)
