# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import fields, models


class InspectionReason(models.Model):
    _name = 'inspection.reason'
    _decription = "Inspection Reason"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reason ", required=True, translate=True,
                       track_visibility='always')
    code = fields.Char(string="Code")
