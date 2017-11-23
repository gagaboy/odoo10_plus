# Part of Flectra. See LICENSE file for full copyright and licensing details.

{
    'name': "CRM Lead Scoring",
    'category': "Sales",
    'version': "1.0",
    'author': 'Flectra',
    'website': 'https://flectrahq.com',
    'depends': ['website_crm'],
    'description': """Using CRM Lead Scoring module, we can determine the\
    worthiness of leads by attaching values to them based on their behaviour.
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/view_crm_lead_score.xml',
        'views/view_config_crm_contacts.xml',
        'views/inherit_res_partner_view.xml',
        'views/crm_lead_view.xml',
    ],
    'demo': [
        'demo/contacts_scoring_demo.xml',
    ],
    'installable': True,
}
