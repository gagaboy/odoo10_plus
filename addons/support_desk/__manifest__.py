# Part of Flectra. See LICENSE file for full copyright and licensing details.

{
    'name': 'Help and Support Desk',
    'version': '1.0',
    'category': 'Support Desk',
    'sequence': 20,
    'summary': 'Support Request, Support Query',
    "author": "Flectra",
    'website': 'https://flectrahq.com',
    'depends': ['mail', 'base_setup', 'utm', 'resource', 'portal', ],
    'description': """ Support Desk is a web based ticketing and support
        platform that can be used by service providers to manage user support
        requests. End users can raise support queries by creating tickets
        in the Support desk portal
    """,
    'data': [
        'data/support_desk_data.xml',
        'security/support_desk_security.xml',
        'security/ir.model.access.csv',
        'wizard/remove_assignee_from_team_view.xml',
        'views/support_desk_sla_policy_view.xml',
        'views/support_desk_team_view.xml',
        'views/support_desk_ticket_view.xml',
        'views/support_desk_team_dashboard_view.xml',
        'views/res_partner_view.xml',
        'views/res_config_settings_view.xml',
        'views/support_desk_templates.xml',
        'views/res_users_view.xml',
        'views/assets.xml'
    ],
    'qweb': ['static/src/xml/support_desk_team_dashboard.xml'],
    'demo': ['demo/support_desk_demo.xml'],
    'installable': True,
    'auto_install': False,
}
