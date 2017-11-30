# Part of Flectra. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from flectra import api, fields, models, _
from flectra.exceptions import ValidationError


class ProcessWizard(models.TransientModel):
    _name = 'process.wizard'

    category_id = fields.Many2one('plm.category', string="Category")
    user_id = fields.Many2one('res.users', string="User")
    notes = fields.Text(string="Notes ")
    reason_id = fields.Many2one('plm.reason', string="Reason")
    reason = fields.Text(string="Remarks")
    process_date = fields.Datetime(string="Date")
    action = fields.Selection([('review', 'Review'), ('approve', 'Approve'),
                               ('reject', 'Reject')])

    @api.constrains('category_id')
    def ecr_category_id(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        ecr_id = self.env['engineering.change.request'].browse(active_ids)
        approve_line = self.env['engineering.change.request.acceptance'].search(
            [('ecr_id', '=', ecr_id.id), ('action', '=', 'approve')])
        review_line = self.env['engineering.change.request.acceptance'].search(
            [('ecr_id', '=', ecr_id.id), ('action', '=', 'review')])
        if self.action in ['review', 'approve']:
            if self.category_id:
                for line in approve_line:
                    if line.active_approver and line.category_ids in \
                            self.category_id:
                        raise ValidationError(_("Approved. Please select "
                                                "different category."))
                for line in review_line:
                    if line.active_reviewer and line.category_ids in \
                            self.category_id:
                        raise ValidationError(_("Reviewed. Please select "
                                                "different category."))

    @api.model
    def default_get(self, fields):
        context = dict(self._context)
        result = super(ProcessWizard, self).default_get(fields)
        if context.get('review'):
            result.update({'action': 'review'})
        elif context.get('approve'):
            result.update({'action': 'approve'})
        elif context.get('reject'):
            result.update({'action': 'reject'})
        result.update({
            'user_id': self.env.user.id or False})
        return result

    @api.multi
    def action_send_for_process(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        ecr_id = self.env['engineering.change.request'].browse(active_ids)
        approval_obj = self.env['engineering.change.request.acceptance']
        approval_line = approval_obj.search([('ecr_id', '=', ecr_id.id),
                                             ('category_ids', 'in',
                                              self.category_id.id)])
        for line in approval_line:
            if line.active_reviewer:
                line.write({'action': self.action,
                            'date': datetime.today(),
                            'reason_id': self.reason_id.id,
                            'reason': self.reason})
            ecr_id.change_state_review()
            if line.active_approver:
                line.write({'action': self.action,
                            'date': datetime.today(),
                            'reason_id': self.reason_id.id,
                            'reason': self.reason})

            ecr_id.change_state_approve()
        if self.action == 'reject':
            self.action_ecr_reject()

    @api.multi
    def action_ecr_reject(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        ecr_id = self.env['engineering.change.request'].browse(active_ids)
        approval_obj = self.env['engineering.change.request.acceptance']
        approval_line = approval_obj.search([('ecr_id', '=', ecr_id.id),
                                             ('category_ids', 'in',
                                              self.category_id.id)])
        for line in approval_line:
            if line.active_reviewer:
                line.write({'action': self.action,
                            'date': datetime.today(),
                            'reason_id': self.reason_id.id,
                            'reason': self.reason})
            if line.active_approver:
                line.write({'action': self.action,
                            'date': datetime.today(),
                            'reason_id': self.reason_id.id,
                            'reason': self.reason})
        ecr_id.change_state_reject()
