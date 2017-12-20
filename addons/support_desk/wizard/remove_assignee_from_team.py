# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models
from flectra.exceptions import UserError


class RemoveAssignee(models.TransientModel):
    _name = 'remove.assignee.team'
    _Description = 'Remove Assignee from Team'

    operation_type = fields.Selection([('add', 'Add'), ('remove', 'Remove')],
                                      'Operation Type')
    user_ids = fields.Many2many("res.users", 'res_remove_user_team',
                                'team_id', 'user_id',
                                "Add/Remove Agents from Team")
    unassign_users = fields.Boolean("Unassign agent",
                                    help="Unassign Agent form every open "
                                         "ticket")
    escalation_user_id = fields.Many2one("res.users", "Escalation Agent")
    team_id = fields.Many2one("supportdesk.team", "Team",
                              default=lambda self: self.env.context.get(
                                  'active_id'))

    @api.onchange("escalation_user_id")
    def onchange_escalation_user_id(self):
        if self.escalation_user_id and self.unassign_users and \
                self.operation_type == 'remove':
            self.unassign_users = False
            raise UserError("You can only select one option!")

    @api.multi
    def escalate_user(self):
        if self.operation_type == 'remove' and not self.unassign_users and \
                not self.escalation_user_id:
            raise UserError("You have to select at least one option from "
                            "given.")
        team_id = self._context.get("active_id") and self._context[
            "active_id"] or False
        # todo: remove and add agents at the last of agents list
        if self.user_ids and team_id:
            team = self.env["supportdesk.team"].browse(team_id)
            if self.operation_type == 'remove':
                user_id = False
                team.with_context({'write_from_wizard': True}).write({
                    'agent_ids': [(3, user) for user in
                                  self.user_ids.ids]})

                agent_tickets = self.env["supportdesk.ticket"].search([
                    ('user_id', 'in', self.user_ids.ids),
                    ('stage_id.set_done', '=', False),
                    ('team_id', '=', team_id)])
                if not self.unassign_users:

                    user_id = user_id
                agent_tickets.write({'user_id': user_id})
            elif self.operation_type == 'add':
                team.with_context({'write_from_wizard': True}).write({
                    'agent_ids': [(4, user_id) for user_id in
                                  self.user_ids.ids]
                })
