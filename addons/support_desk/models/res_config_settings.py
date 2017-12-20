# Part of flectra. See LICENSE file for full copyright and licensing details.

from flectra import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_support_desk_timesheet = fields.Boolean('Integrate Timesheet on '
                                                   'support desk '
                                                   'Tickets')
    module_website_support_desk_form = fields.Boolean('Integrate support desk '
                                                      'with Website Form')
    module_website_support_desk_forum = fields.Boolean('Integrate support desk'
                                                       ' with Website Forum')
