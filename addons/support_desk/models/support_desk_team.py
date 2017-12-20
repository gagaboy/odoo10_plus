# Part of Flectra. See LICENSE file for full copyright and licensing details.

import datetime
import json
from datetime import datetime, timedelta
from babel.dates import format_date, format_datetime
from flectra import api, fields, models, _
from flectra.exceptions import UserError
from flectra.release import version
from flectra.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class SupportdeskStage(models.Model):
    _name = 'supportdesk.stage'
    _description = 'Stage'
    _order = 'id, sequence'

    def _get_team_ids(self):
        if self.env.context.get('default_team_id'):
            return [(4, self.env.context.get('default_team_id'), 0)]

    name = fields.Char(required=True)
    fold = fields.Boolean('Folded', help='Folded in kanban view')
    sequence = fields.Integer(default=1)
    set_done = fields.Boolean('Done Tickets Kanban Stage',
                              help='Tickets are set as done in this stage. '
                                   'Generally used to calculate KPIs and '
                                   'performance.')
    template_id = fields.Many2one('mail.template', 'Automated Answer Email '
                                                   'Template',
                                  domain="[('model', '=', "
                                         "'supportdesk.ticket')]")
    team_ids = fields.Many2many('supportdesk.team',
                                relation='supportteam_stage_rel',
                                string='Team', default=_get_team_ids,
                                help='Team specific stages are assigned to '
                                     'each stage. Dymic stages can be added'
                                     ' from team.')


class SupportdeskTeam(models.Model):
    _name = "supportdesk.team"
    _inherit = ['mail.alias.mixin', 'mail.thread']
    _description = "supportdesk Team"
    _order = 'sequence,name'

    name = fields.Char('Supportdesk Team', required=True, translate=True)
    working_hour_ids = fields.Many2one('resource.calendar', 'Working Hour(s)')
    sequence = fields.Integer(default=1)
    team_color = fields.Integer('Index Color', default=1)

    stage_count = fields.Integer('Stages', compute='_compute_stage_count')
    enable_set_agent_availability = fields.Boolean("Allow Agent's to change "
                                                   "their availability")
    ticket_assignation = fields.Selection(
        [('manual', 'Manual'),
         ('round_robin', 'Round Robbin'),
         ('equitable', 'Equitabely')], string='Assignment Type',
        default='manual', required=True,
        help='Ticket Assignment Policies for new tickets:\n'
             '\tManual: Assign tickets manually to assignees by Support Desk '
             'Managers\n'
             '\tRound Robin: Auto-assign tickets to agent in round robin '
             'fashion\n'
             '\tEquitabely: Auto-assign ticket equally between all agents, '
             'skip assignment if highest threshold limit is crossed')
    stage_ids = fields.Many2many('supportdesk.stage',
                                 relation='supportteam_stage_rel',
                                 string='Stages', default=[(0, 0, {
            'name': 'New', 'sequence': 0
        })], help="Stages track the tickets by support "
                  "teams.")
    agent_ids = fields.Many2many(
        'res.users', string='Agents',
        domain=lambda self: [
            ('groups_id', 'in', self.env.ref(
                'support_desk.group_support_desk_user').id)])
    ticket_ids = fields.One2many('supportdesk.ticket', 'support_team_id',
                                 string='Tickets')
    description = fields.Text(translate=True)
    highest_support_ticket_count = fields.Integer('Maximum ticket per agent')
    apply_domain = fields.Boolean('Mail Domain', default=True)
    apply_sla = fields.Boolean('SLA Policies')
    unassigned_tickets = fields.Integer("Unassigned Tickets",
                                        compute='_get_unassigned_tickets',
                                        store=False)
    dashboard_graph_data = fields.Text(compute='_compute_dashboard_graph')
    dashboard_graph_type = fields.Selection(
        [('line', 'Line'), ('bar', 'Bar'), ], string='Type',
        compute='_compute_dashboard_graph',
        help='The type of graph this team will display in the dashboard.')
    dashboard_graph_group = fields.Selection(
        [('day', 'Day'), ('week', 'Week'), ('month', 'Month'),
         ('user', 'Salesperson'), ], string='Group by', default='week',
        help="How this team's dashboard graph will group the results.")
    dashboard_graph_period = fields.Selection(
        [('week', 'Last Week'), ('month', 'Last Month'),
         ('year', 'Last Year'), ], string='Scale', default='month',
        help="The time period this team's dashboard graph will consider.")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env[
                                     'res.company']._company_default_get(
                                     'supportdesk.team'))

    @api.depends('stage_ids')
    def _compute_stage_count(self):
        for support_team in self:
            support_team.stage_count = len(support_team.stage_ids.ids)

    @api.depends('dashboard_graph_group', 'dashboard_graph_period')
    def _compute_dashboard_graph(self):
        for support_team in self:
            if support_team.dashboard_graph_group in (False, 'user') or \
                    support_team.dashboard_graph_period == 'week' \
                    and support_team.dashboard_graph_group != 'day' \
                    or support_team.dashboard_graph_period == 'month' \
                    and support_team.dashboard_graph_group != 'day':
                support_team.dashboard_graph_type = 'bar'
                support_team.dashboard_graph_data = json.dumps(
                    support_team.get_bar_graph_datas())
            else:
                support_team.dashboard_graph_type = 'line'
                support_team.dashboard_graph_data = json.dumps(
                    support_team.get_line_graph_datas())

    @api.multi
    def _get_unassigned_tickets(self):
        ticket_data = self.env['supportdesk.ticket'].read_group(
            [('responsible_user_id', '=', False),
             ('support_team_id', 'in', self.ids),
             ('stage_id.set_done', '=', False)], ['support_team_id'],
            ['support_team_id'])
        mapped_data = dict(
            (data['support_team_id'][0], data['support_team_id_count']) for
            data in
            ticket_data)
        for support_team in self:
            support_team.unassigned_tickets = mapped_data.get(
                support_team.id, 0)

    @api.multi
    def get_bar_graph_datas(self):
        data = []
        today = datetime.strptime(fields.Date.context_today(self), DF)
        data.append({'label': _('Past'), 'value': 0.0, 'type': 'past'})
        day_of_week = int(format_datetime(today, 'e', locale=self._context.get(
            'lang') or 'en_US'))
        first_day_of_week = today + timedelta(days=-day_of_week + 1)
        for i in range(-1, 4):
            if i == 0:
                label = _('This Week')
            elif i == 3:
                label = _('Future')
            else:
                start_week = first_day_of_week + timedelta(days=i * 7)
                end_week = start_week + timedelta(days=6)
                if start_week.month == end_week.month:
                    label = str(start_week.day) + '-' + str(
                        end_week.day) + ' ' + format_date(
                        end_week, 'MMM', locale=self._context.get('lang') or
                        'en_US')
                else:
                    label = format_date(start_week, 'd MMM',
                                        locale=self._context.get('lang') or
                                        'en_US') + '-' + \
                        format_date(end_week, 'd MMM',
                                    locale=self._context.get('lang') or
                                    'en_US')
            data.append({'label': label, 'value': 0.0,
                        'type': 'past' if i < 0 else 'future'})

        # Build SQL query to find amount aggregated by week
        (select_sql_clause, query_args) = self._get_bar_graph_select_query()
        query = ''
        start_date = (first_day_of_week + timedelta(days=-7))
        for i in range(0, 6):
            if i == 0:
                query += select_sql_clause + " and t.create_date < '" + \
                    start_date.strftime(DF) + "'"

            elif i == 5:
                query += " UNION ALL (" + select_sql_clause + " and " \
                                                              "t.create_date" \
                                                              " >= " \
                                                              "'" + \
                         start_date.strftime(DF) + "')"
            else:
                next_date = start_date + timedelta(days=7)
                query += " UNION ALL (" + select_sql_clause + " and " \
                                                              "t.create_date" \
                                                              " >= " \
                                                              "'" + \
                         start_date.strftime(DF) + \
                         "' and t.create_date < '" + next_date.strftime(DF) \
                         + "')"
                start_date = next_date
        self.env.cr.execute(query, query_args)
        query_results = self.env.cr.dictfetchall()
        for index in range(0, len(query_results)):
            if query_results[index].get('create_date') is not None:
                data[index]['value'] = query_results[index].get('total')

        [graph_title, graph_key] = self._graph_title_and_key()
        return [{'values': data, 'title': graph_title, 'key': graph_key}]

    def _graph_title_and_key(self):
        return ['', _('open Tickets')]

    def _get_bar_graph_select_query(self):
        """
        Returns a tuple containing the base SELECT SQL query used to gather
        the bar graph's data as its first element, and the arguments dictionary
        for it as its second.
        """
        return ("""SELECT
        count(t.id) as total, min(t.create_date) as create_date
        FROM
        supportdesk_ticket
        t, supportdesk_stage
        s
        WHERE
        t.support_team_id = %(support_team_id)s and t.stage_id = s.id and
        s.set_done = 'f'
        """, {'support_team_id': self.id})

    @api.multi
    def get_line_graph_datas(self):
        data = []
        today = datetime.today()
        last_month = today + timedelta(days=-30)

        query = """SELECT
                count(t.id) as total, min(t.create_date) as create_date
                FROM
                supportdesk_ticket
                t, supportdesk_stage
                s
                WHERE
                t.support_team_id = %s and t.stage_id = s.id and
                s.set_done = 'f'
                AND t.create_date > %s
                AND t.create_date <= %s
                """

        self.env.cr.execute(query, (self.id, last_month, today))
        tickets = self.env.cr.dictfetchall()

        locale = self._context.get('lang') or 'en_US'
        show_date = last_month
        # get date in locale format
        name = format_date(show_date, 'd LLLL Y', locale=locale)
        short_name = format_date(show_date, 'd MMM', locale=locale)
        data.append({'x': short_name, 'y': 0, 'name': name})

        for ticket in tickets:
            # fill the gap between last data and the new one
            number_day_to_add = (datetime.strptime(
                ticket.get('create_date'), "%Y-%m-%d %H:%M:%S.%f") -
                show_date).days
            last_balance = data[len(data) - 1]['y']
            for day in range(0, number_day_to_add + 1):
                show_date = show_date + timedelta(days=1)
                # get date in locale format
                name = format_date(show_date, 'd LLLL Y', locale=locale)
                short_name = format_date(show_date, 'd MMM', locale=locale)
                data.append({'x': short_name, 'y': last_balance, 'name': name})
            # add new ticket value
            data[len(data) - 1]['y'] = ticket.get('total')

        # continue the graph if the last statement isn't today
        if show_date != today:
            number_day_to_add = (today - show_date).days
            last_balance = data[len(data) - 1]['y']
            for day in range(0, number_day_to_add):
                show_date = show_date + timedelta(days=1)
                # get date in locale format
                name = format_date(show_date, 'd LLLL Y', locale=locale)
                short_name = format_date(show_date, 'd MMM', locale=locale)
                data.append({'x': short_name, 'y': last_balance, 'name': name})

        [graph_title, graph_key] = self._graph_title_and_key()
        color = '#875A7B' if '+e' in version else '#7c7bad'
        return [{'values': data, 'title': graph_title, 'key': graph_key,
                 'area': True, 'color': color}]

    @api.onchange('ticket_assignation')
    def onchange_ticket_assignment(self):
        if self.ticket_assignation != 'manual' and not self.agent_ids:
            raise UserError("Please add agents for this team before "
                            "changing the assignation method!")

    @api.onchange('agent_ids', 'apply_domain', 'name')
    def _onchange_agent_ids_domain(self):
        if not self.agent_ids:
            self.ticket_assignation = 'manual'
        if not self.alias_name and self.name and self.apply_domain:
            self.alias_name = self.env['mail.alias']._clean_and_make_unique(
                self.name)
        if not self.apply_domain:
            self.alias_name = False

    def get_alias_model_name(self, vals):
        return vals.get('alias_model', 'supportdesk.team')

    def get_alias_values(self):
        values = super(SupportdeskTeam, self).get_alias_values()
        values['alias_defaults'] = {'team_id': self.id}
        return values

    @api.model
    def action_open_all_teams(self):
        teams = self.search([]).ids
        action = self.env.ref(
            'support_desk.support_desk_team_action').read()[0]

        if len(teams) <= 1:
            action.update({
                'view_mode': 'form',
                'res_id': teams and teams[0] or False,
            })
        return action

    @api.multi
    def assign_user_to_tickets(self):
        self.ensure_one()
        user_obj = self.env['res.users']
        available_user_id = False
        agent_ids = sorted(self.agent_ids.ids)
        if agent_ids:
            if self.ticket_assignation == 'equitable':
                ticket_group = self.env['supportdesk.ticket'].read_group(
                    [('stage_id.set_done', '=', False),
                     ('responsible_user_id', 'in', agent_ids)],
                    ['responsible_user_id'], ['responsible_user_id'])
                agent_tkt_count = dict((ag_id, 0) for ag_id in agent_ids)
                agent_tkt_count.update(
                    (data['responsible_user_id'][0], data[
                        'responsible_user_id_count']) for data in
                    ticket_group)
                available_user_id = min(agent_tkt_count,
                                        key=agent_tkt_count.get)
                check_threshold = agent_tkt_count[available_user_id]
                if self.highest_support_ticket_count and check_threshold and \
                        self.highest_support_ticket_count < check_threshold:
                    return False

            elif self.ticket_assignation == 'round_robin':
                available_user_id = agent_ids[0]
                last_assigned_user = self.env['supportdesk.ticket'].search(
                    [('support_team_id', '=', self.id),
                     ('responsible_user_id', '!=', False)],
                    order='create_date desc', limit=1).responsible_user_id.id

                if last_assigned_user in agent_ids:
                    available_user_id = agent_ids[
                        (agent_ids.index(last_assigned_user) + 1) % len(
                            agent_ids)]

        return available_user_id and user_obj.browse(
            available_user_id) or False

    @api.multi
    def unlink(self):
        stages = self.mapped('stage_ids').filtered(
            lambda stage: stage.team_ids <= self)
        stages.unlink()
        return super(SupportdeskTeam, self).unlink()

    @api.model
    def get_data_for_dashboard(self):
        ticket_obj = self.env['supportdesk.ticket']
        result = {'all_tickets': 0,
                  'sla_policy_failed_tickets': 0,
                  'high_priority': 0,
                  'critical': 0,
                  'unassigned_tickets': 0,
                  'closed_today': 0,
                  'show_demo': not bool(ticket_obj.search([], limit=1))}

        open_tickets_domain = [('stage_id.set_done', '=', False)]
        group_fields = ['priority', 'create_date', 'stage_id']
        open_tickets = ticket_obj.read_group(open_tickets_domain, group_fields,
                                             group_fields, lazy=False)

        for ticket in open_tickets:
            result['all_tickets'] += ticket['__count']
            if ticket['priority'] == '2':
                result['high_priority'] += ticket['__count']
            if ticket['priority'] == '3':
                result['critical'] += ticket['__count']

        closed_today_tickets = ticket_obj.search_count(
            [('stage_id.set_done', '=', True),
             ('resolved_date', '>=', fields.Date.today())])
        result['closed_today'] += closed_today_tickets

        sla_policy_failed_tickets = ticket_obj.search_count(
            [('stage_id.set_done', '=', False),
             ('sla_policy_id', '!=', False)])
        result['sla_policy_failed_tickets'] += sla_policy_failed_tickets

        unassigned_tickets = ticket_obj.search_count(
            open_tickets_domain + [('responsible_user_id', '=', False)])
        result['unassigned_tickets'] += unassigned_tickets
        return result
