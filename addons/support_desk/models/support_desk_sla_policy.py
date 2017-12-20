# Part of Flectra. See LICENSE file for full copyright and licensing details.


from flectra import api, fields, models


class SupportdeskSLA(models.Model):
    _name = "supportdesk.sla"
    _order = "name"
    _description = "supportdesk SLA Policies"

    name = fields.Char('SLA Policy', required=True, index=True)
    description = fields.Html('SLA Policy Description')
    company_id = fields.Many2one('res.company', 'Company',
                                 related='team_id.company_id', readonly=True,
                                 store=True)
    team_id = fields.Many2one('supportdesk.team', 'Team', required=True)
    stage_id = fields.Many2one('supportdesk.stage', 'Target Stage',
                               required=True, help='conditional based stage.')
    priority = fields.Selection(
        [('0', 'Normal'), ('1', 'Low Priority'), ('2', 'High Priority'),
         ('3', 'Critical')], string='Priority', default='0',
        required=True,
        help='Set maximum priority, min from this priority will not be taken '
             'into account.')
    ticket_type_id = fields.Many2one('supportdesk.ticket.type', "Ticket Type",
                                     help="Apply only on same type of "
                                          "ticket. If not set apply on all "
                                          "type of tickets.")
    active = fields.Boolean('Active', default=True)

    respond_time_days = fields.Integer('Days', default=0, required=True,
                                       help="Response Time taken to reach the "
                                            "selected stage in days")
    respond_time_hours = fields.Integer('Hours', default=0, required=True,
                                        help="Response Time taken to reach the "
                                            "selected stage in hours")
    resolve_time_days = fields.Integer('Days', default=0, required=True,
                                       help="Resolve Time taken to reach the "
                                            "selected stage in days")
    resolve_time_hours = fields.Integer('Hours', default=0, required=True,
                                        help="Resolve Time taken to reach the "
                                            "selected stage in hours")

    def add_hours_into_days(self):
        if self.resolve_time_hours >= 24:
            self.resolve_time_days += self.resolve_time_hours / 24
            self.resolve_time_hours %= 24
        if self.respond_time_hours >= 24:
            self.respond_time_days += self.respond_time_hours / 24
            self.respond_time_hours %= 24

    @api.model
    def create(self, vals):
        res = super(SupportdeskSLA, self).create(vals)
        res.add_hours_into_days()
        return res

    @api.multi
    def write(self, vals):
        res = super(SupportdeskSLA, self).write(vals)
        self.add_hours_into_days()
        return res
