# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_available = fields.Boolean("Available for supportdesk Support")

    team_count = fields.Integer("supportdesk Teams",
                                compute='_compute_service_team_count')
    support_ticket_count = fields.Integer("Tickets",
                                          compute='_compute_service_support_'
                                                  'ticket_count')

    @api.multi
    def _compute_service_team_count(self):
        user_obj = self.env["res.users"]
        team_obj = self.env["supportdesk.team"]
        for partner in self:
            related_user = user_obj.search([('partner_id', '=', partner.id)])
            team_count = len([team.id for team in team_obj.search([]) if
                              related_user in team.agent_ids])
            partner.team_count = team_count

    @api.multi
    def _compute_service_support_ticket_count(self):
        raw_data = self.env['supportdesk.ticket'].read_group(
            [('partner_id', 'child_of', self.ids)], ['partner_id'],
            ['partner_id'])

        support_ticket_count = len([ticket for ticket in raw_data if
                                   ticket["partner_id"][0] in self.ids])
        for partner in self:
            partner.support_ticket_count = support_ticket_count

    @api.multi
    def action_open_support_desk_ticket(self):
        action = self.env.ref(
            'support_desk.support_desk_ticket_action_tree').read()[0]
        my_tickets = self.env["supportdesk.ticket"].search([
            ('partner_id', 'child_of', self.ids)]).ids
        if len(my_tickets) > 1:
            action['domain'] = [('id', 'in', my_tickets)]
        elif len(my_tickets) == 1:
            action['views'] = [
                (self.env.ref('support_desk.support_desk_ticket_view_form').id,
                 'form')]
            action['res_id'] = my_tickets[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_open_support_desk_team(self):
        team_obj = self.env["supportdesk.team"]
        action = self.env.ref(
            'support_desk.support_desk_team_action').read()[0]
        related_user = self.env["res.users"].search(
            [('partner_id', '=', self.id)])
        team_ids = [team.id for team in team_obj.search([]) if
                    related_user in team.agent_ids]
        action['domain'] = [('id', 'in', team_ids)]
        return action
