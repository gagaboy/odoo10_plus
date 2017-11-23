# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class CRMLead(models.Model):
    _inherit = "crm.lead"

    @api.multi
    @api.depends(
        'title', 'team_id', 'country_id', 'contact_type_id',
        'contact_status_id')
    def _compute_lead_score(self):
        no_of_types = 0
        final_score = 0

        for lead in self:
            res = {
                lead.title: (
                    lead.env['partner.title.scoring'], 'partner_title_id'),
                lead.team_id: (
                    lead.env['crm.team.scoring'], 'team_id'),
                lead.country_id: (
                    lead.env['country.scoring'], 'country_id'),
                lead.contact_type_id: (
                    lead.env['contacts.type.scoring'], 'type_id'),
                lead.contact_status_id: (
                    lead.env['contacts.status.scoring'], 'status_id'),
            }
            for value_obj, env in list(res.items()):
                if value_obj:
                    score_id = env[0].search([(env[1], '=', value_obj.id)])
                    if score_id:
                        if isinstance(score_id, int):
                            final_score += score_id
                        else:
                            scores = [score.score for score in score_id]
                            final_score += sum(scores) / len(scores)
                        no_of_types += 1

            count = no_of_types if no_of_types > 0.0 else 1.0
            lead.lead_score = final_score / count

    lead_score = fields.Float(
        compute="_compute_lead_score", string="Score", store=True)
    contact_type_id = fields.Many2one(
        "crm.contacts.type", string="Contact Type")
    contact_status_id = fields.Many2one(
        "crm.contacts.status", string="Contact Status")
    is_prospective_lead = fields.Boolean(string="Prospective Lead?")
    scoring_rule_id = fields.Many2one("crm.lead.score", string="Scoring Rule")
