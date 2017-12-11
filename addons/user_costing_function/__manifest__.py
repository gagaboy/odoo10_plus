# Part of Flectra See LICENSE file for full copyright and licensing details.
#  Inspired by Odoo version 8 Community module analytic_user_function.


{
    'name': 'User Costing Function',
    'version': '1.0',
    'category': 'Sales Management',
    'summary': 'Employee wise amount on Contract Management',
    'description': """Define employee cost for project and when a user put
    in his working time on tasks, based on the same it will be
    added in account. There is a chance to update this entered value and
    if no values entered by employee default value will be fetched
    from employee profile.""",
    'author': 'Flectra',
    'website': 'https://flectrahq.com',
    'depends': ['hr_activity_sheet', 'project_activity'],
    'data': [
        'security/ir.model.access.csv',
        'views/user_costing_function_view.xml',
        ],
    'demo': [
        'demo/costing_user_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
