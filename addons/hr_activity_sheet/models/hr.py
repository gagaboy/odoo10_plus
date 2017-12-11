# Part of Flectra See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    activities_count = fields.Integer('Total Activities',
                                      compute='_compute_activities_count')

    @api.multi
    def _compute_activities_count(self):
        for obj in self:
            obj.activities_count = obj.env['hr.activity.sheet'].search_count(
                [('employee_id', '=', obj.id)])


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    total_unapprove = fields.Integer('Unapproved Activities',
                                     compute='_compute_total_unapprove')

    @api.multi
    def _compute_total_unapprove(self):
        result = self.env['hr.activity.sheet'].read_group([
            ('state', '=', 'unapproved'), ('department_id', 'in', self.ids)
        ], ['department_id'], ['department_id'])
        dictonary = dict((res['department_id'][0],
                          res['department_id_count']) for res in result)
        for obj in self:
            obj.total_unapprove = dictonary.get(obj.id, 0)
