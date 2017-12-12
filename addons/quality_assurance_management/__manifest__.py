# Part of Flectra. See LICENSE file for full copyright and licensing details.

{
    'name': 'Quality Assurance Management',
    'version': "1.0",
    'category': 'Manufacturing',
    'summary': 'Inspection of Products at different stages i.e.Purchase, '
               'Sale and Manufacturing Order',
    'description': """
    Quality Inspection helps management to 'Pass' or
    'Fail' the product on the
    base of set parameters.
        """,
    "author": "Flectra",
    'website': 'https://www.flectrahq.com/',
    'depends': ['mrp', 'purchase', 'sale_management'],
    'data': [
        'security/inspection.xml',
        'security/ir.model.access.csv',
        'data/inspection_data.xml',
        'views/qc_test_views.xml',
        'views/qc_team_views.xml',
        'views/purchase_views.xml',
        'views/sale_views.xml',
        'views/picking_views.xml',
        'wizard/process_wizard_views.xml',
        'views/qc_inspection_views.xml',
        'views/production_views.xml',
        'views/sale_views.xml',
        'views/inspection_reason_views.xml',
        'views/incident_report_views.xml',
        'views/qc_team_dashboard.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
