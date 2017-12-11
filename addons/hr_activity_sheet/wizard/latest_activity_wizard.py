# Part of Flectra See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _


class LatestActivity(models.TransientModel):
    _name = 'latest.activity'
    _description = 'latest.activity'

    @api.model
    def get_latest_activity(self):
        activities = self.env['hr.activity.sheet']
        action = {
            'name': _('Get Activities'),
            'view_mode': 'form,tree',
            'view_type': 'form',
            'res_model': 'hr.activity.sheet',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('user_id', '=', uid)]",
        }
        activity_sheets = activities.search(
            [('start_date', '<=', fields.Date.today()),
             ('end_date', '>=', fields.Date.today()),
             ('state', 'in', ('draft', 'new')),
             ('user_id', '=', self._uid)])
        if len(activity_sheets) > 1:
            domain = "[('id', 'in', " + str(
                activity_sheets.ids) + "),('user_id', '=', uid)]"
            action.update({'domain': domain, 'view_mode': 'tree,form'})
        if len(activity_sheets) == 1:
            action.update({'res_id': activity_sheets.ids[0]})
        return action
