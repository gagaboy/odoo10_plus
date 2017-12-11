# Part of Flectra See LICENSE file for full copyright and licensing details.

from flectra import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    sheet_generaton_period = fields.Selection(
        [('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
        default='weekly', string='Sheet Generation Period',
        help="Activities Generation Range")
