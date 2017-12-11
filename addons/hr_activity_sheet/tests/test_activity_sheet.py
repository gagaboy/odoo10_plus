# Part of Flectra See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from flectra.tests.common import TransactionCase
from datetime import datetime, timedelta
from flectra import tools, fields


class TestActivitySheet(TransactionCase):
    def setUp(self):
        super(TestActivitySheet, self).setUp()
        self.analytic_line = self.env['account.analytic.line']
        self.employee = self.env.ref('hr.employee_root')
        self.user = self.env.ref('base.user_root')
        self.template_user = self.env.ref('auth_signup.default_template_user')
        self.project = self.env.ref('project.project_project_2')
        self.activity_sheet = self.env['hr.activity.sheet']
        start_date = datetime.now() + relativedelta(weeks=-1, weekday=0)
        end_date = start_date + timedelta(days=6)
        self.activity_sheet.create(
            {'employee_id': self.employee.id,
             'start_date': start_date,
             'end_date': end_date})

    def test_01_activity_sheet_without_user_in_employee(self):
        '''
        test activity creation without defining user in employee
        :return:
        '''

        start_date = datetime.now() + relativedelta(weeks=-1, weekday=0)
        end_date = start_date + timedelta(days=6)
        try:
            self.employee.user_id = False
            self.activity_sheet.create(
                {'employee_id': self.employee.id,
                 'start_date': start_date,
                 'end_date': end_date})
        except Exception as e:
            self.assertEqual(
                tools.ustr(e),
                'Activity will be created only if employee '
                'contains its related user.\n')

    def test_02_check_overlap_activity(self):
        '''
        Test overlap of activity
        :return:
        '''
        start_date = datetime.now() + relativedelta(weeks=-1, weekday=0)
        end_date = start_date + timedelta(days=6)
        self.employee.write({'user_id': self.user.id})
        try:
            self.activity_sheet.create(
                {'employee_id': self.employee.id,
                 'start_date': start_date,
                 'end_date': end_date})
            self.activity_sheet.create(
                {'employee_id': self.employee.id,
                 'start_date': start_date,
                 'end_date': end_date})
        except Exception as e:
            self.assertEqual(
                tools.ustr(e),
                "Activity sheet cannot be duplicated!.\nNone")

    def test_03_onchange_employee_id(self):
        '''
            Test onchange employee
            :return:
        '''
        self.employee.write({'user_id': self.user.id})
        activity = self.activity_sheet.search(
            [('employee_id', '=', self.employee.id)], limit=1)
        activity.on_employee_id_change()
        self.assertEqual(activity.department_id.id,
                         activity.employee_id.department_id.id)
        self.assertEqual(activity.user_id.id,
                         activity.employee_id.user_id.id)

    def test_04_activity_sheet_open_to_approved(self):
        '''
        Test activity state update from open to approved
        directly without confirm
        :return:
        '''
        self.employee.write({'user_id': self.user.id})
        activity = self.activity_sheet.search(
            [('employee_id', '=', self.employee.id)], limit=1)
        try:
            activity.set_activity_approved()
        except Exception as e:
            self.assertEqual(
                tools.ustr(e),
                "Kindly submit your activity first!.\n")

    def test_05_check_activity_sheet_entry_in_unapproved_state(self):
        '''
        Test activities entry updation in unapproved
         activity sheet should not be possible
        '''
        analytic_line = self.analytic_line.create(
            {'project_id': self.project.id,
             'date': fields.Date.today(),
             'name': 'Test Activity Line',
             'unit_amount': 2,
             'user_id': self.user.id})
        activity = analytic_line.activity_sheet_id
        activity.set_activity_unapproved()
        try:
            analytic_line.write({'name': 'Test Activity Line Update'})
        except Exception as e:
            self.assertEqual(
                tools.ustr(e),
                "Confirmed activities’ entries cannot be updated.\n")

    def test_06_check_activity_sheet_entry_deletion_in_unapproved_state(self):
        '''
        Test activities entry deletion in unapproved
         activity should not be possible
        '''
        analytic_line = self.analytic_line.create(
            {'project_id': self.project.id,
             'date': fields.Date.today(),
             'name': 'Test Activity Line',
             'unit_amount': 2,
             'user_id': self.user.id})
        activity = analytic_line.activity_sheet_id
        activity.set_activity_unapproved()
        try:
            analytic_line.unlink()
        except Exception as e:
            self.assertEqual(
                tools.ustr(e),
                "Confirmed activities’ entries cannot be updated.\n")

    def test_07_update_activity_sheet_state_to_draft(self):
        '''
        Update activity status to draft by user not having
        HR Officer or Manager group access
        '''
        activity = self.activity_sheet.search(
            [('employee_id', '=', self.employee.id)], limit=1)
        try:
            activity.sudo(self.template_user.id).set_activity_draft()
        except Exception as e:
            self.assertEqual(
                tools.ustr(e),
                "Activities can only be Approved or Refused by Managers\n")

    def test_08_update_activity_sheet_state_approved(self):
        '''
        Update activity status to approved by user not having
        HR Officer or Manager group access
        '''
        activity = self.activity_sheet.search(
            [('employee_id', '=', self.employee.id)], limit=1)
        activity.set_activity_unapproved()
        try:
            activity.sudo(self.template_user.id).set_activity_approved()
        except Exception as e:
            self.assertEqual(
                tools.ustr(e),
                "Activities can only be Approved by Managers.\n")

    def test_09_create_activity_sheet__in_draft_state(self):
        '''
        New activity created should be in draft state
        '''
        start_date = datetime.now() + relativedelta(weeks=-1, weekday=0)
        end_date = start_date + timedelta(days=6)
        employee = self.env.ref("hr.employee_stw")
        user = self.env['res.users'].create(
            {'name': employee.name,
             'login': employee.work_email,
             'email': employee.work_email,
             'groups_id': [
                 (4, self.ref('hr_timesheet.group_hr_timesheet_user'))],
             })
        employee.write({'user_id': user.id})
        activity = self.activity_sheet.create(
            {'employee_id': employee.id,
             'start_date': start_date,
             'end_date': end_date})
        self.assertEqual(activity.state, "draft")
