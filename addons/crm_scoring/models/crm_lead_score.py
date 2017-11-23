# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _
from flectra.exceptions import ValidationError


class CRMLeadScore(models.Model):
    _name = "crm.lead.score"
    _inherit = ['mail.thread']
    _description = "Lead Soring Rule"

    TYPES = {
        'contact_type': 'Contact Type',
        'title': 'Title',
        'sales_channels': 'Sales Channels',
        'contact_status': 'Contact Status',
        'country': 'Country',
    }

    @api.model
    def create(self, vals):
        res = super(CRMLeadScore, self).create(vals)
        same_records = res.search([
            ('id', '!=', res.id),
            ('profile_scoring_type', '=', res.profile_scoring_type)
        ])
        if same_records:
            raise ValidationError(_(
                "There's already one rule defined for '%s' type!") %
                str(self.TYPES[res.profile_scoring_type]))
        return res

    @api.multi
    def write(self, vals):
        res = super(CRMLeadScore, self).write(vals)
        if 'profile_scoring_type' in vals:
            same_records = self.search([
                ('id', '!=', self.id),
                ('profile_scoring_type', '=', vals['profile_scoring_type'])
            ])
            if same_records:
                raise ValidationError(_(
                    "There's already one rule defined for '%s' type!") %
                    str(self.TYPES[self.profile_scoring_type]))
        return res

    name = fields.Char('Name', required=True, track_visibility='onchange')
    score_rule_type = fields.Selection([
        ('scoring', 'Scoring'),
        ('archive', 'Archive'),
        ('delete', 'Delete')], default='scoring', required=True)
    profile_scoring_type = fields.Selection([
        ('contact_type', 'Contact Type'), ('title', 'Title'),
        ('sales_channels', 'Sales Channels'),
        ('contact_status', 'Contact Status'),
        ('country', 'Country')], default='contact_type', required=True)
    is_event_based = fields.Boolean(string="Based on Event?")
    is_running = fields.Boolean(string="Currently Running?", default=True)
    type_scoring_ids = fields.One2many(
        'contacts.type.scoring', 'score_id', 'Profile Scoring')
    status_scoring_ids = fields.One2many(
        'contacts.status.scoring', 'score_id', 'Profile Scoring')
    channels_scoring_ids = fields.One2many(
        'crm.team.scoring', 'score_id', 'Profile Scoring')
    title_scoring_ids = fields.One2many(
        'partner.title.scoring', 'score_id', 'Profile Scoring')
    country_scoring_ids = fields.One2many(
        'country.scoring', 'score_id', 'Profile Scoring')

    @api.multi
    def check_duplication(self, line, field_id, ids_list):
        val = getattr(line, field_id).id
        if val not in ids_list:
            ids_list.append(val)
        else:
            raise ValidationError(_("You can not add same type twice!"))

    @api.multi
    @api.constrains(
        'type_scoring_ids', 'status_scoring_ids',
        'channels_scoring_ids', 'title_scoring_ids',
        'country_scoring_ids')
    def _check_score(self):
        ids_list = []
        res = {
            'contact_type': self.type_scoring_ids,
            'title': self.title_scoring_ids,
            'sales_channels': self.channels_scoring_ids,
            'contact_status': self.status_scoring_ids,
            'country': self.country_scoring_ids
        }

        fields = [
            'type_id', 'status_id', 'team_id', 'partner_title_id', 'country_id'
        ]

        for line in res[self.profile_scoring_type]:
            if line.score < 0.0 or line.score > 10.0:
                raise ValidationError(_(
                    "Invalid Score!\n\nScore must be in range 1 - 10."))

            for field in fields:
                if hasattr(line, field):
                    self.check_duplication(line, field, ids_list)
