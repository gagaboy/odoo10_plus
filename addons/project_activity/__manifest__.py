# Part of Flectra See LICENSE file for full copyright and licensing details.
# Inspired by Odoo version 8 Community module project_timesheet.

{
    'name': 'Project Activities',
    'version': '1.0',
    'category': 'Project Management',
    'summary': 'Project Activity Management',
    'description': """Using the Activity module in Flectra you can manage
your projects log, the time spent by task or employee and raise an invoice
for the same.""",
    'author': 'Flectra',
    'website': 'https://flectrahq.com',
    'depends': ['resource', 'project', 'hr_activity_sheet',
                'hr_timesheet_attendance', 'hr_activity_invoice',
                'account_costing_analysis'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_activity_view.xml',
    ],
    'demo': ['demo/project_activity_demo.xml'],
    'installable': True,
    'auto_install': True,
}
