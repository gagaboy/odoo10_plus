# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _
from flectra.exceptions import ValidationError


class PlmCategory(models.Model):
    _name = "plm.category"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'ir.attachment']
    _decription = "PLM Category"

    name = fields.Char(string="Category", track_visibility='always')
    team_id = fields.Many2one('plm.team', string="Team",
                              track_visibility='always', store=True)
    reviewer = fields.Many2one('res.users', string="Reviewer ",
                               compute='_get_reviewer_approver',
                               store=True, track_visibility='always')
    approver = fields.Many2one('res.users', string="Approver ",
                               compute='_get_reviewer_approver',
                               store=True, track_visibility='always')
    color = fields.Integer('Color Index', default=10)

    @api.depends('team_id')
    def _get_reviewer_approver(self):
        for categ in self:
            if categ.team_id:
                reivewers = categ.team_id.member_ids.filtered(
                    lambda user: user.type_of_user == 'reviewer')
                approvers = categ.team_id.member_ids.filtered(
                    lambda user: user.type_of_user == 'approver')
                categ.reviewer = reivewers
                categ.approver = approvers

    @api.constrains('team_id')
    def _check_team_id(self):
        if self.team_id:
            if not self.reviewer:
                raise ValidationError(
                    _("Must be assign Reviewer"))
            if not self.approver:
                raise ValidationError(
                    _("Must be assign Approver"))
