# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import fields, models


class PlmReason(models.Model):
    _name = 'plm.reason'
    _decription = "PLM Reason"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reason ", required=True, translate=True,
                       track_visibility='always')
    action = fields.Selection([('review', 'Review'), ('approve', 'Approve'),
                               ('reject', 'Reject')], string="Action ")
