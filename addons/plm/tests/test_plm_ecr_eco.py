# Part of Flectra. See LICENSE file for full copyright and licensing details.

from datetime import datetime
import logging

from flectra.tests.common import TransactionCase


class TestEcr(TransactionCase):
    def setUp(self):
        super(TestEcr, self).setUp()
        self.so_model = self.env['sale.order']
        self.so_line_model = self.env['sale.order.line']
        self.res_user_model = self.env['res.users']
        self.main_company = self.env.ref('base.main_company')
        self.mo_model = self.env['mrp.production']
        self.so1 = self.env.ref('plm.sale_order_ecr_to_mo1')
        self.so_line = self.env.ref('plm.sale_order_line_ecr_to_mo1')
        self.product = self.env.ref('product.product_product_3')
        self.routing = self.env.ref('mrp.mrp_routing_0')
        self.temp_routing = self.env.ref('mrp.mrp_routing_1')
        self.ecr = self.env['engineering.change.request']
        self.eco = self.env['engineering.change.order']
        self.plm_team = self.env['plm.team']
        self.plm_category = self.env['plm.category']
        self.plm_reason = self.env['plm.reason']
        self.process_wizard = self.env['process.wizard']
        res_users_plm_requester = self.env.ref('plm.group_engineering_change_request_requester')
        res_users_plm_member = self.env.ref('plm.group_engineering_change_request_member')
        res_users_plm_reviewer = self.env.ref('plm.group_engineering_change_request_reviewer')
        res_users_plm_approver = self.env.ref('plm.group_engineering_change_request_approver')

        self.ecr_requester = self.res_user_model.create(dict(
            name="Julie",
            company_id=self.main_company.id,
            login="julie",
            password='Julie',
            email="julie@test.com",
            groups_id=[(6, 0, [res_users_plm_requester.id])]
        ))
        self.ecr_member = self.res_user_model.create(dict(
            name="Marie",
            company_id=self.main_company.id,
            login="marie",
            password='Marie',
            email="marie@test.com",
            groups_id=[(6, 0, [res_users_plm_member.id])]
        ))
        self.ecr_reviewer1 = self.res_user_model.create(dict(
            name="Alice",
            company_id=self.main_company.id,
            login="alice",
            password='alice',
            email="alice@test.com",
            groups_id=[(6, 0, [res_users_plm_reviewer.id])]
        ))
        self.ecr_reviewer2 = self.res_user_model.create(dict(
            name="Justine",
            company_id=self.main_company.id,
            login="justine",
            password='justine',
            email="justine@test.com",
            groups_id=[(6, 0, [res_users_plm_reviewer.id])]
        ))
        self.ecr_approver1 = self.res_user_model.create(dict(
            name="Elise",
            company_id=self.main_company.id,
            login="elise",
            password='elise',
            email="elise@test.com",
            groups_id=[(6, 0, [res_users_plm_approver.id])]
        ))
        self.ecr_approver2 = self.res_user_model.create(dict(
            name="Lisa",
            company_id=self.main_company.id,
            login="lisa",
            password='lisa',
            email="lisa@test.com",
            groups_id=[(6, 0, [res_users_plm_approver.id])]
        ))

        self.so1.force_quotation_send()
        self.so1.action_confirm()
        self.assertTrue(self.so1.state, 'sale')
        self.assertTrue(self.so1.invoice_status, 'to invoice')
        logging.info('Test Cases for Sale order')
        logging.info('Sale Order - %s' % (self.so1.name))
        logging.info('Sale Order state- %s' % (self.so1.state))
        logging.info('======================================================'
                     '=========================+=====')
        logging.info(' | Product           |  Ordered Qty            '
                     '| Unit Price             |  Subtotal |')
        for line in self.so1.order_line:
            logging.info('| %s       | %d            | %d                     '
                         '| %d ' % (line.product_id.name, line.product_uom_qty,
                                    line.price_unit, line.price_subtotal))
            logging.info('===================================================='
                         '=============================')

        mo_ids = self.mo_model.search([('sale_id', '=', self.so1.id)])
        for mo in mo_ids:
            logging.info("Manufacturing Order.......%s." % mo.name)
            self.assertTrue(mo_ids, 'Manufacture order not created')

            mo.create_ecr()
            self.assertEqual(mo.total_change_order, 1, 'More than one ECR created')
            ecr_id = self.ecr.search([('manufacture_order', '=', mo.id)])
            self.assertTrue(ecr_id, 'ECR not created from Manufacture Order')

    def create_team_members(self):
        self.ecr_team = self.plm_team.create(dict(
            name="Drawing Team",
            member_ids=[(6, 0, [self.ecr_reviewer1.id, self.ecr_approver1.id])]
        ))
        reivewers = self.ecr_team.member_ids.filtered(
            lambda user: user.type_of_user == 'reviewer').ids
        approvers = self.ecr_team.member_ids.filtered(
            lambda user: user.type_of_user == 'approver').ids
        self.assertEqual(len(reivewers), 1,
                         '"More than one Reviewer is not allowed for Review"')
        self.assertEqual(len(approvers), 1,
                         '"More than one Approver is not allowed for Approve"')

    def create_plm_categories(self):
        self.ecr_category = self.plm_category.create(dict(
            name="DRAWING ERROR",
            team_id=self.ecr_team.id
        ))
        self.plm_category._get_reviewer_approver()
        self.assertTrue(not self.plm_category.reviewer,
                        'Must be assign reviewer')
        self.assertTrue(not self.plm_category.approver,
                        'Must be assign approver')

    def create_plm_reasons(self):
        self.ecr_review_reason = self.plm_reason.create(dict(
            name="Test Review",
            action='review'
        ))
        self.ecr_approve_reason = self.plm_reason.create(dict(
            name="Test Approve",
            action='approve'
        ))
        self.ecr_reject_reason = self.plm_reason.create(dict(
            name="Test Reject",
            action='reject'
        ))

    def create_ecr(self):
        self.create_team_members()
        self.create_plm_categories()
        self.create_plm_reasons()
        mo_ids = self.mo_model.search([('sale_id', '=', self.so1.id)])[0]
        self.ecr_permanent_id = self.ecr.create(dict(
            requested_by=self.ecr_requester.id,
            ecr_date=datetime.today(),
            product_id=self.product.id,
            manufacture_order=mo_ids.id,
            type='permanent',
            activation='at_date',
            category_ids=[(6, 0, [self.ecr_category.id])],
            description_request='TEST',
            reason_request='TEST'
        ))
        self.ecr_validation(self.ecr_permanent_id)

        self.ecr_temporary_id = self.ecr.create(dict(
            requested_by=self.ecr_requester.id,
            ecr_date=datetime.today(),
            product_id=self.product.id,
            manufacture_order=mo_ids.id,
            type='temporary',
            activation='at_date',
            category_ids=[(6, 0, [self.ecr_category.id])],
            description_request='TEST',
            reason_request='TEST'
        ))
        self.ecr_validation(self.ecr_temporary_id)

    def ecr_validation(self, ecr_id):
        ecr_id.onchange_manufacture_order()
        ecr_id.onchange_type_id()
        ecr_id.onchange_product_id()
        self.assertTrue(not ecr_id.category_ids.reviewer or
                        ecr_id.category_ids.approver, "Categories must have "
                                                      "Approver and Reviewer.")
        self.assertNotEqual(ecr_id.requested_by, ecr_id.category_ids.reviewer,
                            "Requester and Approver or Reviewer of Categories "
                            "must be different users.")
        self.assertNotEqual(ecr_id.requested_by, ecr_id.category_ids.approver,
                            "Requester and Approver or Reviewer of Categories "
                            "must be different users.")

        ecr_id.action_send_for_confirm()
        self.assertTrue(ecr_id.state == 'confirm', 'Confirm: state after'
                                                   'confirm is wrong')
        self.assertTrue(ecr_id.approval_ids, 'There is no approval lines')

        ecr_id.action_cancel()
        self.assertTrue(ecr_id.state == 'cancel', 'Cancel: state after cancel'
                                                  'is wrong')
        self.assertFalse(ecr_id.approval_ids, 'There is approval lines')

        ecr_id.action_reset_to_draft()
        self.assertTrue(ecr_id.state == 'draft', 'Draft: state after reset to '
                                                 'draft is wrong')

        ecr_id.action_send_for_confirm()
        self.assertTrue(ecr_id.state == 'confirm', 'Confirm: state after'
                                                   'confirm is wrong')
        self.assertTrue(ecr_id.approval_ids, 'There is no approval lines')

        process_wizard = self.process_wizard.create({
            'category_id': self.ecr_category.id,
            'reason_id': self.ecr_review_reason.id,
            'reason': "Test Review Reason"})
        process_wizard.action_send_for_process()

        for approval in ecr_id.approval_ids:
            if approval.active_reviewer:
                approval.write({'action': 'review'})
            if approval.name == 'reviewer' and \
                    approval.user_id.id == self.env.user.id:
                self.assertTrue(approval.active_reviewer,
                                'There is no active Reviewer')
            if approval.name == 'approver' and \
                    approval.user_id.id == self.env.user.id:
                self.assertTrue(approval.active_approver,
                                'There is no active Approver')

        ecr_id.change_state_review()
        self.assertTrue(ecr_id.state == 'reviewed',
                        'reviewed: state after reviewed is wrong.')

        process_wizard = self.process_wizard.create({
            'category_id': self.ecr_category.id,
            'reason_id': self.ecr_approve_reason.id,
            'reason': "Test Approve Reason"})
        process_wizard.action_send_for_process()

        for approval in ecr_id.approval_ids:
            if approval.active_approver:
                approval.write({'action': 'approve'})
            if approval.name == 'reviewer' and \
                    approval.user_id.id == self.env.user.id:
                self.assertTrue(approval.active_reviewer,
                                'There is no active Reviewer')
            if approval.name == 'approver' and \
                    approval.user_id.id == self.env.user.id:
                self.assertTrue(approval.active_approver,
                                'There is no active Approver')

        ecr_id.change_state_approve()
        self.assertTrue(ecr_id.state == 'approved',
                        'approved: state after approved is wrong.')
        process_wizard = self.process_wizard.create({
            'category_id': self.ecr_category.id,
            'reason_id': self.ecr_reject_reason.id,
            'reason': "Test Reject Reason"})
        process_wizard.action_send_for_process()

        for approval in ecr_id.approval_ids:
            if approval.active_reviewer:
                approval.write({'action': 'reject'})
                ecr_id.write({'state': 'rejected'})
            if approval.active_approver:
                approval.write({'action': 'reject'})
                ecr_id.write({'state': 'rejected'})

        self.assertTrue(ecr_id.state == 'rejected',
                        'rejected: state after rejected is wrong.')
        ecr_id.action_reset_to_confirm()
        self.assertTrue(ecr_id.state == 'reviewed',
                        'reviewed: state reject after approved is wrong.')

        process_wizard = self.process_wizard.create({
            'category_id': self.ecr_category.id,
            'reason_id': self.ecr_review_reason.id,
            'reason': "Test Review Reason"})
        process_wizard.action_send_for_process()

        for approval in ecr_id.approval_ids:
            if approval.active_reviewer:
                approval.write({'action': 'review'})
            if approval.name == 'reviewer' and \
                    approval.user_id.id == self.env.user.id:
                self.assertTrue(approval.active_reviewer,
                                'There is no active Reviewer')
            if approval.name == 'approver' and \
                    approval.user_id.id == self.env.user.id:
                self.assertTrue(approval.active_approver,
                                'There is no active Approver')

        ecr_id.change_state_approve()
        self.assertTrue(ecr_id.state == 'approved',
                        'approved: state after approved is wrong.')

    def create_eco(self):
        self.eco_permanent_id = self.eco.create(dict(
            name='Test ECO',
            ecr_id=self.ecr_permanent_id.id,
            applicability='bom',
            type='permanent',
            product_tmpl_id=self.ecr_permanent_id.product_id.product_tmpl_id.id
        ))
        self.eco_validation(self.eco_permanent_id)
        self.eco_temporary_id = self.eco.create(dict(
            name='Test ECO',
            ecr_id=self.ecr_temporary_id.id,
            applicability='bom',
            type='temporary',
            product_tmpl_id=self.ecr_temporary_id.product_id.product_tmpl_id.id
        ))
        self.eco_validation(self.eco_temporary_id)

    def eco_validation(self, eco_id):
        eco_id.onchange_ecr_id()
        eco_id.product_template_change()
        eco_id.bom_applicability_change()

    def test_eco_inprogress_done(self):
        self.create_ecr()
        self.create_eco()

        self.eco_id = self.eco_permanent_id
        self.eco_id.action_in_progress()
        self.assertTrue(self.eco_id.state == 'in_progress',
                        'in_progress: state after In Progress is wrong.')
        self.eco_id.action_done()
        self.assertTrue(self.eco_id.state == 'done', 'state is wrong.')

    def test_permanent_bom_versioning(self):
        self.create_ecr()
        self.create_eco()
        bom_dict = self.eco_permanent_id.action_view_bill_of_materials()
        bom_id = self.env[(bom_dict.get('res_model'))]. \
            browse(bom_dict.get('res_id'))
        bom_id.product_template_change()
        version = bom_id.version
        new_bom_dict = bom_id.button_new_version()
        self.new_bom_id = self.env[(new_bom_dict.get('res_model'))]. \
            browse(new_bom_dict.get('res_id'))

        self.assertEqual(
            self.new_bom_id.state, 'draft', "New BoM must be in state 'draft'")
        self.assertEqual(
            self.new_bom_id.version, version + 1, 'New Version is not created')
        self.assertFalse(
            self.new_bom_id.active, 'New BoMs must be created inactive')
        self.new_bom_id.button_activate()
        self.assertTrue(
            self.new_bom_id.active, 'Incorrect activation, check must be True')
        self.assertEqual(
            self.new_bom_id.state, 'active',
            "Incorrect state, it should be 'active'")
        self.new_bom_id.button_historical()
        self.assertFalse(
            self.new_bom_id.active,
            'Check must be False, after historification')
        self.assertEqual(
            self.new_bom_id.state, 'historical',
            "Incorrect state, it should be 'historical'")

    def test_temporary_bom_versioning(self):
        self.create_ecr()
        self.create_eco()
        bom_dict = self.eco_temporary_id.action_view_bill_of_materials()
        self.new_bom_id = self.env[(bom_dict.get('res_model'))]. \
            browse(bom_dict.get('res_id'))
        self.new_bom_id.product_template_change()
        version = self.eco_temporary_id.bom_id.version

        self.assertEqual(
            self.new_bom_id.state, 'draft', "New BoM must be in state 'draft'")
        self.assertEqual(
            self.new_bom_id.version, version, 'New Version is created')
        self.assertFalse(
            self.new_bom_id.active, 'New BoMs must be created inactive')
        self.new_bom_id.button_activate()
        self.assertTrue(
            self.new_bom_id.active, 'Incorrect activation, check must be True')
        self.assertEqual(
            self.new_bom_id.state, 'active',
            "Incorrect state, it should be 'active'")
        self.new_bom_id.button_historical()
        self.assertFalse(
            self.new_bom_id.active,
            'Check must be False, after historification')
        self.assertEqual(
            self.new_bom_id.state, 'historical',
            "Incorrect state, it should be 'historical'")

    def test_permanent_routing_versioning(self):
        self.create_ecr()
        self.create_eco()
        self.eco_permanent_id.write({'applicability': 'routing',
                                     'latest_routing_id': self.routing.id
                                     })
        routing_dict = self.eco_permanent_id.change_order_routing_details()
        routing_id = self.env[(routing_dict.get('res_model'))]. \
            browse(routing_dict.get('res_id'))
        version = routing_id.version
        new_routing_dict = routing_id.button_new_version()
        self.latest_routing_id = self.env[(new_routing_dict.get('res_model'))]. \
            browse(new_routing_dict.get('res_id'))

        self.assertEqual(
            self.latest_routing_id.state, 'draft',
            "New Routing must be in state 'draft'")
        self.assertEqual(
            self.latest_routing_id.version, version + 1,
            'New Version is not created')
        self.assertFalse(
            self.latest_routing_id.active,
            'New Routings must be created inactive')
        self.latest_routing_id.button_activate()
        self.assertTrue(
            self.latest_routing_id.active,
            'Incorrect activation, check must be True')
        self.assertEqual(
            self.latest_routing_id.state, 'active',
            "Incorrect state, it should be 'active'")
        self.latest_routing_id.button_historical()
        self.assertFalse(
            self.latest_routing_id.active,
            'Check must be False, after historification')
        self.assertEqual(
            self.latest_routing_id.state, 'historical',
            "Incorrect state, it should be 'historical'")

    def test_temporary_routing_versioning(self):
        self.create_ecr()
        self.create_eco()
        self.eco_temporary_id.write({'applicability': 'routing',
                                     'latest_routing_id': self.temp_routing.id
                                     })
        self.latest_routing_id = self.eco_temporary_id.latest_routing_id.copy({
            'active': False,
            'change_order_type': self.eco_temporary_id.type})
        version = self.eco_temporary_id.latest_routing_id.version

        self.assertEqual(
            self.latest_routing_id.state, 'draft',
            "New Routing must be in state 'draft'")
        self.assertEqual(
            self.latest_routing_id.version, version, 'New Version is created')
        self.assertFalse(
            self.latest_routing_id.active,
            'New Routings must be created inactive')
        self.latest_routing_id.button_activate()
        self.assertTrue(
            self.latest_routing_id.active,
            'Incorrect activation, check must be True')
        self.assertEqual(
            self.latest_routing_id.state, 'active',
            "Incorrect state, it should be 'active'")
        self.latest_routing_id.button_historical()
        self.assertFalse(
            self.latest_routing_id.active,
            'Check must be False, after historification')
        self.assertEqual(
            self.latest_routing_id.state, 'historical',
            "Incorrect state, it should be 'historical'")
