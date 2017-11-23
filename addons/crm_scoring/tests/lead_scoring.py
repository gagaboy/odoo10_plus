# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra.tests.common import TransactionCase


class LeadScoringCases(TransactionCase):

    def setUp(self):
        super(LeadScoringCases, self).setUp()
        self.lead = self.env['crm.lead']
        self.lead_score = self.env['crm.lead.score']
        self.title = self.env.ref('base.res_partner_title_doctor')
        self.country = self.env.ref('base.ar')
        self.channel = self.env.ref('sales_team.team_sales_department')
        self.contact_type = self.env.ref(
            'crm_scoring.crm_score_lead_contact_type1')
        self.contact_status = self.env.ref(
            'crm_scoring.crm_score_lead_profile_contact_status7')

    def test_01_create_lead_scoring(self):
        '''
            Create Lead score
        '''
        line_vals = {
            'name': 'Doctor',
            'partner_title_id': self.title.id,
            'score': 10.0
        }

        scoring_id = self.lead_score.create({
            'name': 'Score Test 1',
            'score_rule_type': 'scoring',
            'profile_scoring_type': 'title',
            'is_event_based': True,
            'is_running': True,
            'title_scoring_ids': [(0, 0, line_vals)]
        })

        scoring_id.write({'profile_scoring_type': 'country'})

    def test_02_create_leads(self):
        '''
            Create Leads
        '''
        self.lead.create({
            'name': 'Lead Test',
            'contact_name': 'Dom Toretto',
            'title': self.title.id,
            'team_id': self.channel.id,
            'contact_type_id': self.contact_type.id,
            'contact_status_id': self.contact_status.id,
            'prospective_lead': True,
            'priority': 2,
        })
