# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    not_available_supportdesk = fields.Boolean('Not Available for support '
                                               'desk '
                                               'Tickets')
    have_teams_auto_assignment = fields.Boolean(
        'Have support desk teams with auto assignment',
        compute='_compute_team_count')
    team_count = fields.Integer("Support Desk Teams",
                                compute='_compute_team_count')

    def _compute_team_count(self):
        team_obj = self.env["supportdesk.team"]
        for user in self:
            teams = [team for team in team_obj.search([]) if user in
                     team.agent_ids]
            user.have_teams_auto_assignment = True if all(
                [team.ticket_assignation != 'manual' for team in teams]) else \
                False
            user.team_count = len(teams)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        ctx = dict(self.env.context)
        domain = [('name', operator, name)]
        if ctx.get("team_id", False) and ctx.get("operation_type", False):
            op_type = ctx.get("operation_type")
            team_agent_ids = self.env["supportdesk.team"].browse(
                ctx['team_id']).agent_ids.ids
            agent_ids = team_agent_ids
            if 'remove_user_ids' in ctx:
                removed_users = ctx["remove_user_ids"][0][2]
                agent_ids = list(set(team_agent_ids) - set(removed_users))
            elif op_type == 'add':
                support_desk_user_ids = self.env.ref(
                    'support_desk.group_support_desk_user').users.ids
                agent_ids = list(
                    set(support_desk_user_ids) - set(team_agent_ids))

            domain = [('id', 'in', agent_ids)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()
