from flectra import api, models


def fine_model_name(name):
    return name.replace(" ", "_").lower() \
        .replace('(', '').replace(')', '').replace('/', '_').replace('\\', '_')


class IrModel(models.Model):
    _name = "ir.model"
    _inherit = ["ir.model"]

    @api.model
    def model_create(self, name):
        model_name = fine_model_name('x_' + name)
        return self.create({'name': name,
                            'model': model_name})
