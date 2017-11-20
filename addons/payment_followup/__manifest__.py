# Part of Flectra. See LICENSE file for full copyright and licensing details.
# Inspired by Odoo version 8 Community module account_followup.

{
    'name': 'Payment Follow-up',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Payment Follow-up',
    'description': """
 Payment Follow is a simplified automated payment follow up tool, designed and
 developed based on market scenarios and user experiences. The tool is a boon
 for any businesses to regularly and automatically follow up payments from
 their customers or just anyone.
""",
    'author': 'Flectra',
    'website': 'https://flectrahq.com',
    'depends': ['account_invoicing', 'mail', 'sales_team'],
    'data': [
        'security/payment_followup_security.xml',
        'security/ir.model.access.csv',
        'data/payment_followup_data.xml',
        'report/payment_followup_report.xml',
        'views/payment_followup_view.xml',
        'views/account_view.xml',
        'views/res_partner_view.xml',
        'wizard/payment_followup_mail_view.xml',
        'views/report_payment_followup.xml',
        'views/payment_followup_reports_action.xml',
    ],
    'demo': ['demo/payment_followup_demo.xml'],
    'installable': True,
    'auto_install': False,
}
