# Part of Odoo S.A.,Flectra See LICENSE file for full copyright and licensing details.
# This module is forward ported from Odoo v8 contract management module.

{
    'name': 'Contracts Management',
    'version': '1.0',
    'category': 'Account/Timesheet',
    'summary': 'Contracts Management',
    'description': """
Contract management is the process of managing contract creation, execution
and analysis to maximize operational and financial performance at an
organization, all while reducing financial risk. Organizations encounter an
ever-increasing amount of pressure to reduce costs and improve company
performance. Contract management proves to be a very time-consuming element
of business, which facilitates the need for effective and automated contract
management system.""",
    'author': 'Odoo S.A., Flectra',
    'website': 'https://flectrahq.com',
    'depends': ['sale_stock', 'hr_activity_invoice', 'project',
                'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'security/account_costing_analysis_security.xml',
        'views/account_costing_analysis_view.xml',
        'views/account_costing_analysis_cron.xml',
        'views/res_config_settings_view.xml',
        'views/project_view.xml',
    ],
    'demo': [
        'demo/account_costing_analysis_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
