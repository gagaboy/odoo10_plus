# Part of Flectra. See LICENSE file for full copyright and licensing details.

{
    'name': 'Manufacturing - Product Lifecycle Management',
    'version': "1.0",
    'category': 'Manufacturing',
    'summary': 'Product Lifecycle Management for Flectra',
    'description': '''
    Manage Product Lifecycle (PLM) along with following features:
    - Engineering change requests
    - Engineering change orders
    - BoM versioning
    - Routing versioning
    ''',
    "author": "Flectra",
    'website': 'https://flectrahq.com',
    'depends': ['sale_management', 'mrp', 'document'],
    'data': [
        'security/plm_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ecr_eco_data.xml',
        'data/ecr_category_data.xml',
        'data/mrp_bom_data.xml',
        'wizard/process_wizard_views.xml',
        'views/engineering_change_request_views.xml',
        'views/engineering_change_order_views.xml',
        'views/bom_views.xml',
        'views/production_views.xml',
        'views/routing_views.xml',
        'views/plm_category_views.xml',
        'views/plm_team_views.xml',
        'views/res_users_views.xml',
    ],
    'demo': [
        'demo/plm_so_mo_demo.xml',
        'demo/plm_users_demo.xml'
    ],
    'installable': True,
    'auto_install': False,
}
