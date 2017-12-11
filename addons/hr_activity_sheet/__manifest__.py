# Part of Flectra See LICENSE file for full copyright and licensing details.
#  Inspired by Odoo version 10 Community module hr_timesheet_sheet.

{
    'name': 'Activity Sheet',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Activity Sheet',
    'description': """
By installing Activity Sheet you will be able to manage your daily
activities periodically.
Employees will add work entries on daily basis and submitting it
as per period defined in company configuration.
Respected managers of employees will than Approve or Refuse activities.
""",
    'author': 'Flectra',
    'website': 'https://flectrahq.com',
    'depends': ['hr_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_activity_sheet_security.xml',
        'data/hr_activity_sheet_data.xml',
        'views/hr_activity_sheet_views.xml',
        'views/hr_views.xml',
    ],
    'demo':[
        'demo/hr_activity_sheet_demo.xml'
    ],
    'installable': True,
    'auto_install': False,
}
