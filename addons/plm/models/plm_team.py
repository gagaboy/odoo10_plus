# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _
from flectra.exceptions import ValidationError
from flectra.tools.safe_eval import safe_eval


class PlmTeam(models.Model):
    _name = 'plm.team'
    _decription = "PLM Team"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'mail.alias.mixin']

    name = fields.Char('PLM Team', required=True, translate=True,
                       track_visibility='always')
    active = fields.Boolean(default=True, track_visibility='always',
                            help="If the active field is set to false,"
                                 "it will allow you to hide the plm team"
                                 "without removing it.")
    member_ids = fields.Many2many('res.users', string='PLM Team Members',
                                  track_visibility='always')
    alias_id = fields.Many2one('mail.alias', 'Alias', ondelete='restrict',
                               required=True)

    @api.multi
    def get_alias_model_name(self, vals):
        return vals.get('alias_model', 'engineering.change.request')

    @api.multi
    def get_alias_values(self):
        self.ensure_one()
        values = super(PlmTeam, self).get_alias_values()
        values['alias_defaults'] = defaults = safe_eval(
            self.alias_defaults or "{}")
        defaults['team_id'] = self.id
        return values

    @api.constrains('member_ids')
    def _check_member_ids(self):
        reivewers = self.member_ids.filtered(
            lambda user: user.type_of_user == 'reviewer').ids
        approvers = self.member_ids.filtered(
            lambda user: user.type_of_user == 'approver').ids
        if len(reivewers) > 1:
            raise ValidationError(
                _("More than one Reviewer is not allowed for Review"))
        if len(approvers) > 1:
            raise ValidationError(
                _("More than one Approver is not allowed for Approve"))

    @api.multi
    def write(self, vals):
        result = super(PlmTeam, self).write(vals)
        if 'alias_defaults' in vals:
            for team in self:
                team.alias_id.write(team.get_alias_values())
        return result
