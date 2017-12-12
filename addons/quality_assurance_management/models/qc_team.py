# Part of Flectra. See LICENSE file for full copyright and licensing details.

import json
from datetime import date
from datetime import datetime, timedelta

from babel.dates import format_date
from dateutil.relativedelta import relativedelta
from flectra import api, fields, models, _
from flectra.release import version
from flectra.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from flectra.tools.safe_eval import safe_eval


class QcTeam(models.Model):
    _name = 'qc.team'
    _decription = "QC Team"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'mail.alias.mixin']

    name = fields.Char(string="QC Team", required=True, translate=True,
                       track_visibility='always')
    active = fields.Boolean(string="Active", default=True,
                            track_visibility='always')
    member_ids = fields.Many2many('res.users', string='QC Team Members',
                                  track_visibility='always', store=True)
    alias_id = fields.Many2one('mail.alias', string="Alias",
                               ondelete='restrict')
    color = fields.Integer(string='Color Index',
                           help="The color of the channel")
    dashboard_button_name = fields.Char(
        string="Dashboard Button", compute='_compute_dashboard_button_name')
    dashboard_graph_data = fields.Text(compute='_compute_dashboard_graph')
    dashboard_graph_type = fields.Selection([
        ('line', 'Line'),
        ('bar', 'Bar'),
    ], string='Type', compute='_compute_dashboard_graph')
    dashboard_graph_group = fields.Selection([('day', 'Day'), ('week', 'Week'),
                                              ('month', 'Month')],
                                             string='Group by',
                                             default='day')
    dashboard_graph_period = fields.Selection([
        ('week', 'Last Week'),
        ('month', 'Last Month'),
        ('year', 'Last Year'),
    ], string='Scale', default='month',
        help="The time period this channel's dashboard graph will consider.")
    fail_inspection = fields.Integer(string="Failed Inspection",
                                     compute='_get_fail_inspection')
    pass_inspection = fields.Integer(string="Passed Inspection",
                                     compute='_get_pass_inspection')
    todo_inspection = fields.Integer(string="Todo Inspection",
                                     compute='_get_todo_inspection')

    @api.multi
    def _get_fail_inspection(self):
        qc_data = self.env['qc.inspection'].read_group(
            [('qc_team_id', 'in', self.ids),
             ('quality_state', '=', 'fail')], ['qc_team_id'], ['qc_team_id'])
        mapped_data = dict(
            (data['qc_team_id'][0], data['qc_team_id_count']) for data in
            qc_data)
        for team in self:
            team.fail_inspection = mapped_data.get(team.id, 0)

    @api.multi
    def _get_pass_inspection(self):
        qc_data = self.env['qc.inspection'].read_group(
            [('qc_team_id', 'in', self.ids),
             ('quality_state', '=', 'pass')], ['qc_team_id'], ['qc_team_id'])
        mapped_data = dict(
            (data['qc_team_id'][0], data['qc_team_id_count']) for data in
            qc_data)
        for team in self:
            team.pass_inspection = mapped_data.get(team.id, 0)

    @api.multi
    def _get_todo_inspection(self):
        qc_data = self.env['qc.inspection'].read_group(
            [('qc_team_id', 'in', self.ids),
             ('quality_state', '=', 'todo')], ['qc_team_id'], ['qc_team_id'])
        mapped_data = dict(
            (data['qc_team_id'][0], data['qc_team_id_count']) for data in
            qc_data)
        for team in self:
            team.todo_inspection = mapped_data.get(team.id, 0)

    @api.multi
    def get_alias_model_name(self, vals):
        return vals.get('alias_model', 'qc.inspection')

    @api.multi
    def get_alias_values(self):
        self.ensure_one()
        values = super(QcTeam, self).get_alias_values()
        values['alias_defaults'] = defaults = safe_eval(
            self.alias_defaults or "{}")
        defaults['qc_team_id'] = self.id
        return values

    @api.multi
    def create_qc_test(self):
        action = self.env.ref(
            'quality_assurance_management.action_qc_test_view').read()[0]
        action.update({
            'views': [[False, 'tree']],
            'context': "{'default_qc_team_id': " + str(self.id) + "}",
        })
        return action

    @api.depends('dashboard_graph_group', 'dashboard_graph_period')
    def _compute_dashboard_graph(self):
        for team in self:
            if team.dashboard_graph_period == 'week' \
                and team.dashboard_graph_group != 'day' \
                or team.dashboard_graph_period == 'month' \
                    and team.dashboard_graph_group != 'day':
                team.dashboard_graph_type = 'bar'
            else:
                team.dashboard_graph_type = 'line'
            team.dashboard_graph_data = json.dumps(team._get_graph())

    def _graph_get_dates(self, today):
        if self.dashboard_graph_period == 'week':
            start_date = today - relativedelta(weeks=1)
        elif self.dashboard_graph_period == 'year':
            start_date = today - relativedelta(years=1)
        else:
            start_date = today - relativedelta(months=1)

        if self.dashboard_graph_group == 'month':
            start_date = date(start_date.year + int(start_date.month / 12),
                              start_date.month % 12 + 1, 1)
            if self.dashboard_graph_period == 'week':
                start_date = today.replace(day=1)
        elif self.dashboard_graph_group == 'week':
            start_date += relativedelta(days=8 - start_date.isocalendar()[2])
            if self.dashboard_graph_period == 'year':
                start_date += relativedelta(weeks=1)
        else:
            start_date += relativedelta(days=1)

        return [start_date, today]

    def _graph_x_query(self):
        if self.dashboard_graph_group == 'week':
            return 'EXTRACT(WEEK FROM %s)' % self.inspection_date
        elif self.dashboard_graph_group == 'month':
            return 'EXTRACT(MONTH FROM %s)' % self.inspection_date
        else:
            return 'DATE(%s)' % self.inspection_date

    def _graph_y_query(self):
        return 'count(id) as total'

    def _extra_sql_conditions(self):
        return ''

    def _graph_title_and_key(self):
        return ['', '']

    def _graph_data(self, start_date, end_date):
        today = datetime.today()
        last_month = today + timedelta(days=-30)
        query = """SELECT count(t.id) as total, min(t.inspection_date) as
                            inspection_date
                            FROM
                            qc_inspection
                            t
                            WHERE
                            t.qc_team_id = %s
                            AND t.inspection_date > %s
                            AND t.inspection_date <= %s;"""
        self.env.cr.execute(query, (self.id, last_month, today))
        return self.env.cr.dictfetchall()

    def _get_graph(self):
        def get_week_name(start_date, locale):
            if (start_date + relativedelta(days=6)).month == start_date.month:
                short_name_from = format_date(start_date, 'd', locale=locale)
            else:
                short_name_from = format_date(start_date, 'd MMM',
                                              locale=locale)
            short_name_to = format_date(start_date + relativedelta(days=6),
                                        'd MMM', locale=locale)
            return short_name_from + '-' + short_name_to

        self.ensure_one()
        values = []
        today = date.today()
        start_date, end_date = self._graph_get_dates(today)
        graph_data = self._graph_data(start_date, end_date)

        if self.dashboard_graph_type == 'line':
            x_field = 'x'
            y_field = 'y'
        else:
            x_field = 'label'
            y_field = 'value'

        locale = self._context.get('lang') or 'en_US'
        if self.dashboard_graph_group == 'day':
            for day in range(0, (end_date - start_date).days + 1):
                short_name = format_date(start_date + relativedelta(days=day),
                                         'd MMM', locale=locale)
                values.append({x_field: short_name, y_field: 0})
            for data_item in graph_data:
                if data_item.get('inspection_date'):
                    index = (
                        datetime.strptime(data_item.get('inspection_date'),
                                          DF).date() - start_date).days
                    values[index][y_field] = data_item.get('total')

        elif self.dashboard_graph_group == 'week':
            weeks_in_start_year = int(
                date(start_date.year, 12, 31).isocalendar()[1])
            for week in range(0, (
                    end_date.isocalendar()[1] - start_date.isocalendar()[
                    1]) % weeks_in_start_year + 1):
                short_name = get_week_name(
                    start_date + relativedelta(days=7 * week), locale)
                values.append({x_field: short_name, y_field: 0})

            for data_item in graph_data:
                if data_item.get('inspection_date'):
                    index = int(((datetime.strptime(
                        data_item.get('inspection_date'),
                        DF).date()).isocalendar()[1]) -
                                start_date.isocalendar()
                                [1] % weeks_in_start_year)
                    values[index][y_field] = data_item.get('total')

        elif self.dashboard_graph_group == 'month':
            for month in range(0,
                               (end_date.month - start_date.month) % 12 + 1):
                short_name = format_date(
                    start_date + relativedelta(months=month), 'MMM',
                    locale=locale)
                values.append({x_field: short_name, y_field: 0})

            for data_item in graph_data:
                index = int((datetime.strptime(data_item.get(
                    'inspection_date'),
                    DF).date().month - start_date.month) % 12)
                values[index][y_field] = data_item.get('total')

        else:
            for data_item in graph_data:
                values.append({x_field: data_item.get('inspection_date'),
                               y_field: data_item.get('total')})

        [graph_title, graph_key] = self._graph_title_and_key()
        color = '#875A7B' if '+e' in version else '#7c7bad'
        return [{'values': values, 'area': True, 'title': graph_title,
                 'key': graph_key, 'color': color}]

    def _compute_dashboard_button_name(self):
        for team in self:
            team.dashboard_button_name = _(
                "QC Inspectiions")

    @api.model
    def get_data_for_dashboard(self):
        qc_obj = self.env['qc.inspection']
        result = {'pass_inspection': 0,
                  'fail_inspection': 0,
                  'all_inspection': 0,
                  'show_domain': not bool(qc_obj.search([], limit=1))}

        pass_inspection = qc_obj.search_count(
            [('quality_state', '=', 'pass')])
        result['pass_inspection'] += pass_inspection

        fail_inspection = qc_obj.search_count(
            [('quality_state', '=', 'fail')])
        result['fail_inspection'] += fail_inspection

        all_inspection = qc_obj.search_count(
            [('quality_state', '!=', 'none')])
        result['all_inspection'] += all_inspection
        return result
