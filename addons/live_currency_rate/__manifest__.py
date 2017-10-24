# -*- coding: utf-8 -*-
# Part of Flectra. See LICENSE file for full copyright and licensing details.
{
    'name': 'Live Currency Rate Update',
    'version': '1.0',
    'category': 'Accounting',
    'author': 'Flectra',
    'description': """
    Import exchange rates from three different sources on the internet :

        1. Federal Tax Administration (Switzerland)

        2. European Central Bank (ported by Grzegorz Grzelak)

        3. Yahoo Finance

        4. Polish National Bank (Narodowy Bank Polski)

        In the roadmap : Google Finance.
""",
    'depends': [
        'account_invoicing',
    ],
    'data': [
        'views/account_config_setting_view.xml',
        'views/currency_rate_cron_data.xml',
    ],
    'installable': True,
    'auto_install': True,
}
