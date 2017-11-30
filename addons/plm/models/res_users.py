# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _
from flectra.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    type_of_user = fields.Selection([('requester', 'Requester'),
                                     ('reviewer', 'Reviewer'),
                                     ('approver', 'Approver'),
                                     ('member', 'Member'),
                                     ('manager', 'Manager')], string="Type",
                                    compute='_get_type_of_user', store=True)
    color = fields.Integer('Color Index', default=12)

    @api.depends('groups_id')
    def _get_type_of_user(self):
        for user in self:
            res = {'requester': user.has_group('plm.group_engineering_change_request_requester'),
                   'reviewer': user.has_group('plm.group_engineering_change_request_reviewer'),
                   'approver': user.has_group('plm.group_engineering_change_request_approver')
                   }
            for key in res:
                if res[key]:
                    user.type_of_user = key
            member = [res[i] for i in res]
            user_member = user.has_group('plm.group_engineering_change_request_member')
            user_manager = user.has_group('plm.group_engineering_change_request_manager')
            if not any(member) and user_member:
                user.type_of_user = 'member'
            if user_manager:
                user.type_of_user = 'manager'

    @api.model
    def create(self, values):
        result = super(ResUsers, self).create(values)
        res = {'reviewer': result.has_group('plm.group_engineering_change_request_reviewer'),
               'approver': result.has_group('plm.group_engineering_change_request_approver'),
               'requester': result.has_group('plm.group_engineering_change_request_requester'),
               'manager': result.has_group('plm.group_engineering_change_request_manager'),
               }
        if not res['manager']:
            if res['reviewer'] and res['approver'] or res['requester'] and \
                    res['approver'] or res['reviewer'] and res['requester']:
                raise ValidationError(
                    _("Select either Approver or Reviewer"))
        return result

    @api.multi
    def write(self, values):
        result = super(ResUsers, self).write(values)
        for user in self:
            res = {'reviewer': user.has_group('plm.group_engineering_change_request_reviewer'),
                   'approver': user.has_group('plm.group_engineering_change_request_approver'),
                   'requester': user.has_group('plm.group_engineering_change_request_requester'),
                   'manager': user.has_group('plm.group_engineering_change_request_manager'),
                   }
            if not res['manager']:
                if res['reviewer'] and res['approver'] or \
                        res['requester'] and res['approver'] or \
                        res['reviewer'] and res['requester']:
                    raise ValidationError(
                        _("Select either Approver or Reviewer"))
            return result
