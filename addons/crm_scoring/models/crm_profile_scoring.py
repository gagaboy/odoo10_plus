# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import fields, models


class CRMContactsType(models.Model):
    _name = 'crm.contacts.type'
    _inherit = ['mail.thread']

    name = fields.Char(
        'Name', required=True, track_visibility='onchange')


class CRMContactStatus(models.Model):
    _name = 'crm.contacts.status'
    _inherit = ['mail.thread']

    name = fields.Char(
        'Name', required=True, track_visibility='onchange')


class ContactsTypeScoring(models.Model):
    _name = 'contacts.type.scoring'
    _rec_name = 'type_id'
    _order = "score desc"

    score = fields.Float(
        'Score', default=0, required=True, track_visibility='onchange')
    score_id = fields.Many2one('crm.lead.score', 'Lead Score')
    type_id = fields.Many2one('crm.contacts.type', 'Type')


class ContactStatusScoring(models.Model):
    _name = 'contacts.status.scoring'
    _rec_name = 'score_id'
    _order = "score desc"

    score = fields.Float(
        'Score', default=0, required=True, track_visibility='onchange')
    score_id = fields.Many2one('crm.lead.score', 'Lead Score')
    status_id = fields.Many2one('crm.contacts.status', 'Scoring')


class CountryScoring(models.Model):
    _name = 'country.scoring'
    _rec_name = 'country_id'
    _order = "score desc"

    score = fields.Float(
        'Score', default=0, required=True, track_visibility='onchange')
    score_id = fields.Many2one('crm.lead.score', 'Lead Score')
    country_id = fields.Many2one('res.country', 'Country')


class CrmTeamScoring(models.Model):
    _name = 'crm.team.scoring'
    _rec_name = 'team_id'
    _order = "score desc"

    score = fields.Float(
        'Score', default=0, required=True, track_visibility='onchange')
    score_id = fields.Many2one('crm.lead.score', 'Lead Score')
    team_id = fields.Many2one('crm.team', 'Team')


class PartnerTitleScoring(models.Model):
    _name = 'partner.title.scoring'
    _rec_name = 'partner_title_id'
    _order = "score desc"

    score = fields.Float(
        'Score', default=0, required=True, track_visibility='onchange')
    score_id = fields.Many2one('crm.lead.score', 'Lead Score')
    partner_title_id = fields.Many2one('res.partner.title', 'Partner Title')
