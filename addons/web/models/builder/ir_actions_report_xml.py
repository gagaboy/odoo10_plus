from flectra import api, models


class ir_actions_report(models.Model):
    _name = 'ir.actions.report'
    _inherit = ['ir.actions.report']

    @api.multi
    def report_edit_data(self):
        self.ensure_one()
        report_data = {}
        report_data['id'] = self.id
        report_data['name'] = self.name
        report_data['display_name'] = self.display_name
        report_data['report_name'] = self.report_name
        report_data['report_file'] = self.report_file
        report_data['view_id'] = self.env['ir.ui.view'].search(
            [('name', 'ilike', self.report_name), ('type', '=', 'qweb')
             ], limit=1).id
        report_data['active_ids'] = \
            self.env[self.model].search([], limit=1).mapped('id')
        report_data['tag'] = 'app_builder_report_editor'
        report_data['type'] = 'ir.actions.client'
        return report_data

    @api.one
    def get_report_data(self):
        report_data = {}
        if self.id:
            report_data['id'] = self.id
            report_data['name'] = self.name
            report_data['report_type'] = self.report_type
            report_data['model'] = self.model
        if self['paperformat_id']:
            xv = []
            for x in self['paperformat_id']:
                xv.append(x.id)
            report_data['paperformat_id'] = xv
        if self['groups_id']:
            xv = []
            for x in self['groups_id']:
                xv.append(x.id)
            report_data['groups_id'] = xv
        return report_data
