# Part of Flectra S.A.,Flectra See LICENSE file for full copyright and
# licensing details.

from flectra import fields, models


class ResConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    required_group_template = fields.Boolean(
        "Templates Required ?",
        implied_group='account_costing_analysis.required_group_template')
