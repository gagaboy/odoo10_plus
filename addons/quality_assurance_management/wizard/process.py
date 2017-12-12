# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, _
from flectra.exceptions import UserError


class ProcessWizard(models.TransientModel):
    _name = 'process.wizard'

    reason_id = fields.Many2one('inspection.reason', string="Reason")
    remarks = fields.Text(string="Remarks")

    @api.multi
    def action_fail(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        inspection_id = self.env['qc.inspection'].browse(active_ids)
        quantitative_ids = [line for line in inspection_id.quantitative_ids if
                            not
                            line.dimension_status]
        qualitative_ids = [line for line in inspection_id.qualitative_ids if
                           not
                           line.dimension_status]
        if quantitative_ids or qualitative_ids:
            raise UserError(_('Please fill the %s field value for all '
                              'lines') % ((quantitative_ids and
                                           'Inspected Value') or
                                          (qualitative_ids and 'Results')))
        else:
            inspection_id.write({'quality_state': 'fail',
                        'reason_id': inspection_id.reason_id.id,
                        'remarks': inspection_id.remarks})
        return True
