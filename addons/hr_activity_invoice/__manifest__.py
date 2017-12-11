# Part of Odoo S.A.,Flectra See LICENSE file for full copyright and licensing
# details.
# This module is forward ported from Odoo v8 invoice on timesheets module.


{
    'name': 'Invoice on Timesheets',
    'version': '1.0',
    'category': 'Sales Management',
    'summary': 'Invoice on Timesheets',
    'description': """
        Hr Acivity Error
    """,
    'author': 'Odoo S.A., Flectra',
    'website': 'https://flectrahq.com',
    'depends': ['base', 'hr_timesheet', 'product', 'project', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_activity_invoice_data.xml',
        'views/hr_activity_invoice_view.xml',
        'views/hr_activity_invoice_report.xml',
        'report/report_analytic_view.xml',
        'report/hr_activity_invoice_report_view.xml',
        'wizard/hr_activity_analytic_revenue_view.xml',
        'wizard/hr_activity_invoice_create_view.xml',
        'wizard/hr_activity_invoice_create_final_view.xml',
        'views/report_analyticrevenue.xml',
    ],
    'demo': [
        'demo/hr_activity_invoice_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
