# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    contact_status_id = fields.Many2one(
        'crm.contacts.status', 'Contact Status')
    contact_type_id = fields.Many2one('crm.contacts.type', 'Contact Type')
