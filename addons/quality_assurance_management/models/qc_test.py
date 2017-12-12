# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _
from flectra.exceptions import ValidationError, UserError


class QcTest(models.Model):
    _name = 'qc.test'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'QC Test'

    reference = fields.Char(string="Name")
    name = fields.Char(string="Reference", copy=False, default=lambda self: _(
        'New'), readonly=True, required=True)
    active = fields.Boolean(string="Active", default=True)
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template', ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', 'Product', ondelete='cascade')
    categ_id = fields.Many2one(
        'product.category', 'Product Category', ondelete='cascade')
    applied_on = fields.Selection([
        ('1_product', 'Product'),
        ('2_product_category', ' Product Category'),
        ('0_product_variant', 'Product Variant')], "Apply On",
        default='1_product', required=True,
        help='QC Inspection applicable on selected option')
    picking_type_ids = fields.Many2many('stock.picking.type',
                                        string="Operation Type")
    quantitative_ids = fields.One2many('quantitative.quality', 'qc_test_id',
                                       string="Quantitative")
    qualitative_ids = fields.One2many('qualitative.quality', 'qc_test_id',
                                      string="Qualitative")
    qc_team_id = fields.Many2one('qc.team', string="QC Team",
                                 track_visibility='onchange')
    responsible_id = fields.Many2one('res.users', string="Responsible")
    state = fields.Selection([('draft', 'Draft'), ('review', 'Reviewed'),
                              ('approve', 'Approved'), ('cancel', 'Cancelled'),
                              ], string='Status', index=True, readonly=True,
                             default='draft', track_visibility='onchange')

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'qc.test') or _('New')
        return super(QcTest, self).create(vals)

    @api.onchange('qc_team_id')
    def get_responsible_id(self):
        return {'domain': {'responsible_id': [
            ('id', 'in', self.qc_team_id.member_ids.ids)]}}

    @api.multi
    def do_review(self):
        self.ensure_one()
        self.write({
            'state': 'review'})

    @api.multi
    def do_approve(self):
        self.ensure_one()
        self.write({
            'state': 'approve'})

    @api.multi
    def unlink(self):
        for qt in self:
            if qt.state not in ('draft', 'review'):
                raise UserError(_('You can not delete a Approved Test'))
        return super(QcTest, self).unlink()


class QuantitativeQuality(models.Model):
    _name = 'quantitative.quality'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Quantitative Quality Set'

    name = fields.Char(string="Name")
    type = fields.Selection([('qualitative', 'Qualitative'),
                             ('quantitative', 'Quantitative')],
                            string='Type', default='quantitative')
    uom_id = fields.Many2one('product.uom', string="Unit of Measure")
    min_dimension = fields.Float(string="Min. Dimension")
    min_value = fields.Float(string="Min. Value")
    max_dimension = fields.Float(string="Max. Dimension")
    max_value = fields.Float(string="Max. Value")
    qc_test_id = fields.Many2one('qc.test', string="QC Test")
    inspection_id = fields.Many2one('qc.inspection', string="QC Inspection")
    value = fields.Float(string="Inspected Value")

    dimension_status = fields.Selection([('optimum', 'Optimum'),
                                         ('acceptable', 'Acceptable'),
                                         ('unacceptable', 'Unacceptable')],
                                        string="Dimension Status",
                                        store=True,
                                        compute='compute_dimension_status')

    @api.constrains('min_value', 'max_value', 'min_dimension', 'max_dimension')
    def dimension_value_check(self):
        self.ensure_one()
        min_value = self.min_value
        max_value = self.max_value
        min_dimension = self.min_dimension
        max_dimension = self.max_dimension
        if min_value and max_value and min_value >= max_value:
            raise ValidationError(
                _("Max. Value should be grater than Min. Value"))
        if min_dimension and max_dimension and \
                min_dimension >= max_dimension:
            raise ValidationError(
                _("Max. Dimension should be grater than Min. Dimension"))
        if min_dimension >= min_value:
            raise ValidationError(
                _("Min. Dimension should be less than Min. Value"))
        if max_dimension <= max_value:
            raise ValidationError(
                _("Max. Dimension should be greater than Max. Value"))

    @api.depends('value')
    def compute_dimension_status(self):
        for line in self:
            line.dimension_status = None
            value = line.value
            min_value = line.min_value
            max_value = line.max_value
            max_dimension = line.max_dimension
            min_dimension = line.min_dimension
            if value:
                if value >= min_value and value <= max_value:
                    line.dimension_status = 'optimum'
                elif value >= max_value and value <= max_dimension \
                    or value <= min_value and value >= min_dimension:
                    line.dimension_status = 'acceptable'
                elif value >= max_dimension or value <= min_dimension:
                    line.dimension_status = 'unacceptable'


class QualitativeQuality(models.Model):
    _name = 'qualitative.quality'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Qualitative Quality Set'

    name = fields.Char(string="Name")
    type = fields.Selection([('qualitative', 'Qualitative'),
                             ('quantitative', 'Quantitative')],
                            string='Type', default='qualitative')

    dimension_status = fields.Selection([('optimum', 'Optimum'),
                                         ('acceptable', 'Acceptable'),
                                         ('unacceptable', 'Unacceptable')],
                                        string="Result")
    qc_test_id = fields.Many2one('qc.test', string="QC Test")
    inspection_id = fields.Many2one('qc.inspection', string="QC Inspection")
    question_ids = fields.One2many('quality.questions', 'quality_id',
                                   string="Questions")


class QualityQuestions(models.Model):
    _name = 'quality.questions'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Quality Questions'

    question = fields.Char(string="Question")
    answer = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Answer")
    quality_id = fields.Many2one('qualitative.quality', string="Qualitative")
