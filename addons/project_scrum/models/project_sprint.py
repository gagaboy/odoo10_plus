# -*- coding: utf-8 -*-

from flectra import models, fields, api, _
from flectra.exceptions import ValidationError
from datetime import datetime, timedelta


class ProjectSprint(models.Model):
    _name = "project.sprint"
    _inherit = ['ir.branch.company.mixin', 'mail.thread']
    _description = "Sprint of the Project"
    _rec_name = 'sprint_seq'

    sprint_seq = fields.Char(
        string="Reference", readonly=True)
    name = fields.Char("Sprint Name", required=True,
                       track_visibility="onchange")
    goal_of_sprint = fields.Char("Goal of Sprint", track_visibility="onchange")

    meeting_date = fields.Datetime("Planning Meeting Date", required=True,
                                   track_visibility="onchange")
    hour = fields.Float(string="Hour", track_visibility="onchange")
    time_zone = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM'),
    ], track_visibility="onchange")
    estimated_velocity = fields.Integer(
        compute="calculate_estimated_velocity", string="Estimated Velocity",
        store=True, track_visibility="onchange")
    actual_velocity = fields.Integer(
        compute="calculate_actual_velocity", string="Actual Velocity",
        store=True, track_visibility="onchange")
    sprint_planning_line = fields.One2many(
        'sprint.planning.line', 'sprint_id', string="Sprint Planning Lines")
    project_id = fields.Many2one('project.project', string="Project",
                                 track_visibility="onchange")
    start_date = fields.Date(string="Start Date", track_visibility="onchange")
    end_date = fields.Date(string="End Date", track_visibility="onchange")
    working_days = fields.Integer(
        compute="calculate_business_days", string="Business Days",
        store=True, track_visibility="onchange")
    productivity_hours = fields.Float(string="Productivity Hours",
                                      track_visibility="onchange")
    productivity_per = fields.Float(
        compute="calculate_productivity_per", string="Productivity (%)",
        store=True, track_visibility="onchange")
    holiday_type = fields.Selection(
        [('hours', 'Hours'), ('days', 'Days')],
        string="Holiday (Hours / Days)", default='hours',
        track_visibility="onchange")
    holiday_count = fields.Float(string="Holiday Count",
                                 track_visibility="onchange")
    holiday_days = fields.Float(
        compute="calculate_holiday_days", string="Holiday Days", store=True,
        track_visibility="onchange")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('cancel', 'Cancel')], string="State", default='draft',
        track_visibility="onchange")
    team_id = fields.Many2one('project.team', string="Team",
                              track_visibility="onchange", required=True)
    task_line = fields.One2many('project.task', 'sprint_id', string='Tasks')
    color = fields.Integer('Color Index')

    @api.depends('start_date', 'end_date')
    def days_calculate(self):
        if self.start_date and self.end_date:
            diff = datetime.strptime(
                self.end_date, '%Y-%m-%d').date() - datetime.strptime(
                self.start_date, '%Y-%m-%d').date()
            self.duration = diff.days

    duration = fields.Integer(
        "Duration (In Days)", compute='days_calculate', store=True,
        track_visibility="onchange")

    @api.one
    def _get_task_count(self):
        self.number_of_tasks = self.env['project.task'].search_count([
            ('sprint_id', '=', self.id)])

    number_of_tasks = fields.Integer(
        string="# of tasks", compute="_get_task_count")

    @api.one
    def _get_story_count(self):
        self.number_of_stories = self.env['project.story'].search_count([
            ('sprint_id', '=', self.id)])

    number_of_stories = fields.Integer(
        string="# of stories", compute="_get_story_count")

    @api.one
    def _get_retrospective_count(self):
        self.number_of_retrospectives = self.env['retrospective'].search_count(
            [('sprint_id', '=', self.id)])

    number_of_retrospectives = fields.Integer(
        string="# of Retrospectives", compute="_get_retrospective_count")

    @api.multi
    @api.depends('task_line', 'task_line.stage_id', 'task_line.sprint_id',
                 'estimated_velocity', 'start_date', 'end_date', 'project_id',
                 'team_id')
    def calculate_tasks_json(self):
        data = []
        for record in self:
            task_ids = self.env['project.task'].search([
                ('sprint_id', '=', record.id)])
            for task in task_ids:
                data.append({
                    'task': task.task_seq or '/',
                    'velocity': task.velocity or 0,
                    'per': round(((float(task.velocity) * 100) / float(
                        record.estimated_velocity)), 2)
                })
            record.tasks_json = data

    tasks_json = fields.Char(
        string="Tasks", compute="calculate_tasks_json", store=True)

    @api.multi
    def get_data(self):
        task_dict_list = []
        for record in self:
            task_pool = self.env['project.task'].search([
                ('sprint_id', '=', record.id)])
            for task in task_pool:
                task_dict = {
                    'reference': task.task_seq,
                    'name': task.name,
                    'velocity': task.velocity,
                    'start_date': task.start_date,
                    'end_date': task.end_date,
                    'actual_end_date': task.actual_end_date,
                    'assigned_to': task.user_id.name,
                    'state': task.stage_id.name,
                }
                task_dict_list.append(task_dict)
        return task_dict_list

    @api.multi
    def set_state_open(self):
        self.state = 'in_progress'

    @api.multi
    def set_state_cancel(self):
        self.state = 'cancel'

    @api.multi
    def set_state_pending(self):
        self.state = 'pending'

    @api.multi
    def redirect_to_view(self, model, caption):
        return {
            'name': (_(caption)),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': model,
            'domain': [
                ('sprint_id', '=', self.id),
            ]
        }

    @api.multi
    def action_view_tasks(self):
        return self.redirect_to_view("project.task", "Tasks")

    @api.multi
    def action_view_stories(self):
        return self.redirect_to_view("project.story", "Stories")

    @api.multi
    def action_view_release_planning(self):
        return self.redirect_to_view("release.planning", "Release Planning")

    @api.multi
    def action_view_retrospective(self):
        return self.redirect_to_view("retrospective", "Retrospective")

    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        if self.start_date > self.end_date:
            raise ValidationError(
                "Start Date can not be greater than End date, Dude!")

    @api.onchange('holiday_type')
    def onchange_holiday_type(self):
        self.holiday_count = 0.0
        self.holiday_days = 0.0

    @api.one
    @api.depends('project_id', 'project_id.no_of_days', 'start_date',
                 'end_date')
    def calculate_business_days(self):
        if self.start_date and self.end_date:
            days_dict = {
                0: (1, 2, 3, 4, 5, 6, 7),
                1: (2, 3, 4, 5, 6, 7),
                2: (3, 4, 5, 6, 7),
                3: (4, 5, 6, 7),
                4: (5, 6, 7),
                5: (6, 7),
                6: (7,),
                7: (),
            }
            start = datetime.strptime(self.start_date, "%Y-%m-%d").date()
            end = datetime.strptime(self.end_date, "%Y-%m-%d").date()
            delta = timedelta(days=1)
            days = 0

            if self.project_id and end > start:
                working_days = self.project_id.no_of_days
                non_working_days = days_dict[working_days]

                while end != start:
                    end -= delta
                    if end.isoweekday() not in non_working_days:
                        days += 1

                self.working_days = days

    @api.one
    @api.depends('project_id', 'project_id.no_of_hours', 'productivity_hours')
    def calculate_productivity_per(self):
        if self.productivity_hours and self.project_id \
                and self.project_id.no_of_hours > 0:
            per = (
                self.productivity_hours / self.project_id.no_of_hours) * 100
            self.productivity_per = per

    @api.one
    @api.depends('project_id', 'project_id.no_of_hours', 'holiday_count')
    def calculate_holiday_days(self):
        if self.holiday_type == 'days' and self.project_id:
            hours = self.holiday_count * self.project_id.no_of_hours
            self.holiday_days = hours

    @api.one
    @api.depends('project_id', 'task_line', 'task_line.velocity')
    def calculate_estimated_velocity(self):
        task_ids = self.env['project.task'].search([
            ('sprint_id', '=', self.id)
        ])
        total_velocity = sum([
            task.velocity for task in task_ids if task.velocity])
        self.estimated_velocity = total_velocity

    @api.one
    @api.depends('project_id', 'end_date', 'task_line', 'task_line.velocity',
                 'task_line.stage_id')
    def calculate_actual_velocity(self):
        task_ids = self.env['project.task'].search([
            ('sprint_id', '=', self.id),
            ('actual_end_date', '<=', self.end_date),
        ])
        total_velocity = sum([
            task.velocity for task in task_ids if task.velocity])
        self.actual_velocity = total_velocity

    @api.onchange('duration')
    def onchange_start_date(self):
        if self.start_date:
            end_date = datetime.strptime(
                self.start_date, '%Y-%m-%d') + timedelta(days=self.duration)
            self.end_date = end_date

    @api.onchange('project_id')
    def onchange_project(self):
        if self.project_id and self.project_id.branch_id:
            self.branch_id = self.project_id.branch_id

    @api.multi
    def check_sprint_state(self):
        next_call = datetime.today()
        for record in self.search([('state', '!=', 'done')]):
            if record.end_date:
                end_date = datetime.strptime(
                    record.end_date, '%Y-%m-%d').date()
                if end_date < next_call:
                    record.state = 'done'

    @api.constrains('sprint_planning_line')
    def check_users_in_planning_line(self):
        user_list = []
        for user in self.sprint_planning_line:
            if user.user_id.id not in user_list:
                user_list.append(user.user_id.id)
            else:
                raise ValidationError(
                    "You can't add the same user twice in Sprint Planning!")

    @api.model
    def create(self, vals):
        vals['sprint_seq'] = self.env[
            'ir.sequence'].next_by_code('project.sprint')

        res = super(ProjectSprint, self).create(vals)
        partner_list = []

        mail_channel_id = self.env['mail.channel'].sudo().search([
            ('name', '=', 'Project Sprint')
        ])
        if mail_channel_id:
            mail_channel_ids = self.env['mail.followers'].sudo().search([
                ('channel_id', '=', mail_channel_id.id),
                ('res_model', '=', res._name),
                ('res_id', '=', res.id),
            ])
            if not mail_channel_ids:
                self.env['mail.followers'].sudo().create({
                    'channel_id': mail_channel_id.id,
                    'res_model': res._name,
                    'res_id': res.id,
                })

        if 'team_id' in vals:
            team_id = self.env['project.team'].browse(vals['team_id'])
            partner_list += [member.partner_id.id
                             for member in team_id.member_ids]

        for follower in partner_list:
            if follower:
                mail_follower_ids = self.env['mail.followers'].sudo().search([
                    ('res_id', '=', res.id),
                    ('partner_id', '=', follower),
                    ('res_model', '=', res._name),
                ])
                if not mail_follower_ids:
                    self.env['mail.followers'].sudo().create({
                        'res_id': res.id,
                        'res_model': res._name,
                        'partner_id': follower,
                        'team_id': team_id.id,
                    })
        return res

    @api.multi
    def write(self, vals):
        res = super(ProjectSprint, self).write(vals)
        partner_list = []

        if 'team_id' in vals:
            team_id = self.env['project.team'].browse(vals['team_id'])
        else:
            team_id = self.team_id

        delete_team_id = self.env['mail.followers'].sudo().search([
            ('team_id', '!=', team_id.id),
            ('res_id', '=', self.id),
        ])
        delete_team_id.unlink()

        partner_list += [member.partner_id.id for member in team_id.member_ids]
        for follower in partner_list:
            if follower:
                mail_follower_ids = self.env['mail.followers'].sudo().search([
                    ('res_id', '=', self.id),
                    ('partner_id', '=', follower),
                    ('res_model', '=', self._name),
                ])
                if not mail_follower_ids:
                    self.env['mail.followers'].sudo().create({
                        'res_id': self.id,
                        'res_model': self._name,
                        'partner_id': follower,
                        'team_id': team_id.id,
                    })
        return res

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'draft':
            return 'project_scrum.state_sprint_draft'
        elif 'state' in init_values and self.state == 'in_progress':
            return 'project_scrum.state_sprint_in_progress'
        elif 'state' in init_values and self.state == 'pending':
            return 'project_scrum.state_sprint_pending'
        elif 'state' in init_values and self.state == 'done':
            return 'project_scrum.state_sprint_done'
        elif 'state' in init_values and self.state == 'cancel':
            return 'project_scrum.state_sprint_cancel'
        return super(ProjectSprint, self)._track_subtype(init_values)


class Project(models.Model):
    _inherit = "project.project"

    @api.constrains('no_of_hours', 'no_of_days')
    def check_days(self):
        if self.no_of_hours < 1 or self.no_of_hours > 24:
            raise ValidationError(
                'No. of hours per day should be in range 1 - 24.')

        if self.no_of_days < 1 or self.no_of_days > 7:
            raise ValidationError(
                'No. of days per week should be in range 1 - 7.')

    no_of_hours = fields.Float(string="Working Hour(s) per Day")
    no_of_days = fields.Integer(string="Working Day(s) per Week")


class SprintPlanningLine(models.Model):
    _name = "sprint.planning.line"

    @api.one
    @api.depends('available_per', 'sprint_id.project_id',
                 'sprint_id.project_id.no_of_hours',
                 'sprint_id', 'sprint_id.working_days')
    def calculate_hours(self):
        project_id = self.sprint_id.project_id
        no_of_hours = project_id and project_id.no_of_hours or 0.0
        calc = (
            self.available_per *
            self.sprint_id.working_days * no_of_hours) / 100
        self.productivity_hours = float(calc)

    @api.one
    @api.depends('sprint_id', 'available_per', 'sprint_id.working_days',
                 'sprint_id.productivity_hours')
    def calculate_sprint_hours(self):
        hours = (self.available_per * self.sprint_id.working_days *
                 self.sprint_id.productivity_hours) / 100
        self.sprint_hours = hours

    @api.one
    @api.depends('sprint_id', 'sprint_id.holiday_count',
                 'sprint_id.holiday_days', 'sprint_hours', 'off_hours')
    def calculate_total_hours(self):
        if self.sprint_id.holiday_type == 'hours':
            hours = (
                self.sprint_hours - self.sprint_id.holiday_count -
                self.off_hours)
        else:
            hours = (
                self.sprint_hours - self.sprint_id.holiday_days -
                self.off_hours)
        self.total_hours = hours

    sprint_id = fields.Many2one('project.sprint', string="Sprint")
    user_id = fields.Many2one('res.users', string="User")
    role_id = fields.Many2one(
        related="user_id.role_id", string="Role", store=True)
    available_per = fields.Integer(string="Available (%)")
    productivity_hours = fields.Float(
        compute="calculate_hours", string="Productivity Hour(s)", store=True)
    sprint_hours = fields.Float(
        compute="calculate_sprint_hours", string="Sprint Hour(s)", store=True)
    off_hours = fields.Float(string="Off Hour(s)")
    total_hours = fields.Float(
        compute="calculate_total_hours", string="Total Hour(s)", store=True)


class UserRole(models.Model):
    _name = "user.role"

    name = fields.Char(string="Role")
    code = fields.Char(string="Code")


class ResUsers(models.Model):
    _inherit = "res.users"

    role_id = fields.Many2one("user.role", string="User Role")


class ProjectTask(models.Model):
    _inherit = "project.task"
    sprint_id = fields.Many2one(
        'project.sprint', string="Sprint", track_visibility="onchange")
    velocity = fields.Integer(string="Velocity", track_visibility="onchange")
    story_id = fields.Many2one(
        'project.story', string="Story", track_visibility="onchange")
    release_planning_id = fields.Many2one(
        "release.planning", string="Release Planning",
        track_visibility="onchange")

    @api.onchange('story_id')
    def onchange_story(self):
        if self.story_id:
            self.description = self.story_id.description

    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        if self.sprint_id:
            start_date = self.sprint_id.start_date
            end_date = self.sprint_id.end_date
            if self.start_date < start_date:
                raise ValidationError(
                    "Start date is not valid according to the Sprint.")

            if self.end_date > end_date:
                raise ValidationError(
                    "End date is not valid according to the Sprint.")

    @api.model
    def create(self, vals):
        res = super(ProjectTask, self).create(vals)
        partner_list = []

        partner_list += [member.partner_id.id
                         for member in res.sprint_id.team_id.member_ids]
        for follower in partner_list:
            if follower:
                mail_follower_ids = self.env['mail.followers'].sudo().search([
                    ('res_id', '=', res.id),
                    ('partner_id', '=', follower),
                    ('res_model', '=', self._name),
                ])
                if not mail_follower_ids:
                    self.env['mail.followers'].sudo().create({
                        'res_id': res.id,
                        'res_model': self._name,
                        'partner_id': follower,
                        'team_id': res.sprint_id.team_id.id,
                    })
        return res

    @api.multi
    def write(self, vals):
        if self.task_seq == '/':
            vals['task_seq'] = self.env['ir.sequence'].next_by_code(
                'project.task')
        res = super(ProjectTask, self).write(vals)
        partner_list = []

        data = []
        for record in self:
            task_ids = self.search([
                ('sprint_id', '=', record.sprint_id.id)])
            for task in task_ids:
                data.append({
                    'task': task.task_seq or '/',
                    'velocity': task.velocity or 0,
                    'per': round(((float(task.velocity) * 100) / float(
                        record.sprint_id.estimated_velocity)), 2)
                    if record.sprint_id.estimated_velocity > 0 else 0
                })

            record.sprint_id.write({'tasks_json': data})

        if 'sprint_id' in vals:
            sprint_id = self.env['project.sprint'].browse(vals['sprint_id'])
            team_id = sprint_id.team_id
        else:
            team_id = self.sprint_id.team_id

        delete_team_id = self.env['mail.followers'].sudo().search([
            ('team_id', '!=', team_id.id),
            ('res_id', '=', self.id),
        ])
        delete_team_id.unlink()

        partner_list += [member.partner_id.id for member in team_id.member_ids]
        for follower in partner_list:
            if follower:
                mail_follower_ids = self.env['mail.followers'].sudo().search([
                    ('res_id', '=', self.id),
                    ('partner_id', '=', follower),
                    ('res_model', '=', self._name),
                ])
                if not mail_follower_ids:
                    self.env['mail.followers'].sudo().create({
                        'res_id': self.id,
                        'res_model': self._name,
                        'partner_id': follower,
                        'team_id': team_id.id,
                    })
        return res


class MailFollowers(models.Model):
    _inherit = "mail.followers"

    team_id = fields.Many2one("project.team", string="Project Team")
