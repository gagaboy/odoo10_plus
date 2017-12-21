from flectra import fields, models


class AppCreatorData(models.Model):
    _name = "app.creator.data"

    mode_data_id = fields.One2many('ir.model.data', 'app_data_id',
                                   readonly=True)
    app_name = fields.Char('Application Name', required=True)
    author = fields.Char("Author", required=True)
    description = fields.Text('Description', required=True)
    category = fields.Text('Category', required=True)
    version = fields.Float("Version")
    licence = fields.Selection([
        ('GPL-2', 'GPL Version 2'),
        ('GPL-2 or any later version', 'GPL-2 or later version'),
        ('GPL-3', 'GPL Version 3'),
        ('GPL-3 or any later version', 'GPL-3 or later version'),
        ('AGPL-3', 'Affero GPL-3'),
        ('LGPL-3', 'LGPL Version 3'),
        ('Other OSI approved licence', 'Other OSI Approved Licence'),
        ('OEEL-1', 'Flectra Enterprise Edition License v1.0'),
        ('OPL-1', 'Flectra Proprietary License v1.0'),
        ('Other proprietary', 'Other Proprietary')
    ], string='License', default='LGPL-3', readonly=True)
    obj_name = fields.Char('Object Name', required=True)
