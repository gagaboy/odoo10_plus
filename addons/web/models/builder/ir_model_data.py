from flectra import api, fields, models


class IrModelData(models.Model):
    _inherit = 'ir.model.data'

    is_app_builder = fields.Boolean(
        help='filter"s whether record is created by flectra.'
    )
    app_data_id = fields.Many2one('app.creator.data',
                                  'App Data')

    @api.multi
    def write(self, data):
        if self._context.get('app_builder'):
            data['noupdate'] = True
            data['is_app_builder'] = True
        return super(IrModelData, self).write(data)

    @api.model
    def create(self, data):
        if self._context.get('app_builder'):
            data['is_app_builder'] = True
        return super(IrModelData, self).create(data)
