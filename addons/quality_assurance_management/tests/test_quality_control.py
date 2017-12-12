# Part of Flectra. See LICENSE file for full copyright and licensing details.

import logging

from flectra import fields
from flectra.exceptions import UserError
from flectra.tests.common import TransactionCase


class TestQuality(TransactionCase):
    def setUp(self):
        super(TestQuality, self).setUp()
        self.Production = self.env['mrp.production']
        self.SaleOrder = self.env['sale.order']
        self.SaleOrderLine = self.env['sale.order.line']
        self.PurchaseOrder = self.env['purchase.order']
        self.PurchaseOrderLine = self.env['purchase.order.line']
        self.Product = self.env['product.product']
        self.StockPicking = self.env['stock.picking.type']
        self.qc_team = self.env['qc.team']
        self.qc_reason = self.env['inspection.reason']
        self.qc_test = self.env['qc.test']
        self.quantitative = self.env['quantitative.quality']
        self.qualitative = self.env['qualitative.quality']
        self.res_user_model = self.env['res.users']
        self.main_company = self.env.ref('base.main_company')
        self.product1 = self.env.ref('product.consu_delivery_03')
        self.product2 = self.env.ref('product.product_product_3')
        self.partner1 = self.env.ref('base.res_partner_1')
        self.partner2 = self.env.ref('base.res_partner_2')
        self.qc_inspection = self.env['qc.inspection']
        self.incident_report = self.env['incident.report']
        self.process_wizard = self.env['process.wizard']

        self.user_1 = self.res_user_model.create(dict(
            name="Julie",
            company_id=self.main_company.id,
            login="julie",
            password='Julie',
            email="julie@test.com"
        ))
        self.user_2 = self.res_user_model.create(dict(
            name="Marie",
            company_id=self.main_company.id,
            login="marie",
            password='Marie',
            email="marie@test.com"
        ))

        self.qc_reason_fail = self.qc_reason.create(dict(
            code="weight",
            name="Weight bit higher"
        ))

        self.qc_reason_incident = self.qc_reason.create(dict(
            code="incident",
            name="Test Incident Report"
        ))

        self.qc_team = self.qc_team.create(dict(
            name="Testing Team",
            alias_name="julie",
            member_ids=[(6, 0, [self.user_1.id, self.user_2.id])]
        ))

    def create_qc_tests(self):
        incoming_ids = self.StockPicking.search([('code', '=', 'incoming')],
                                                limit=1)
        outgoing_ids = self.StockPicking.search([('code', '=', 'outgoing')],
                                                limit=1)

        self.qc_test = self.qc_test.create(dict(
            reference="Test Basic Computer",
            qc_team_id=self.qc_team.id,
            responsible_id=self.user_1.id,
            active=True,
            applied_on='1_product',
            product_id=self.product1.id,
            picking_type_ids=[(6, 0, [incoming_ids.id, outgoing_ids.id])],
        ))
        self.qc_test.quantitative_ids = self.quantitative.create(dict(
            name="Test",
            uom_id=self.product1.uom_id.id,
            type='quantitative',
            min_dimension=50,
            min_value=60,
            max_value=100,
            max_dimension=110,
            qc_test_id=self.qc_test.id
        ))
        self.qc_test.qualitative_ids = self.qualitative.create(dict(
            name="Test",
            question_ids=[(0, 0, {'question': 'Test Design'})],
            qc_test_id=self.qc_test.id
        ))

        logging.info('Name - %s' % (self.qc_test.reference))
        logging.info('qc_team_id - %s' % (self.qc_test.qc_team_id))
        logging.info('responsible_id - %s' % (self.qc_test.responsible_id))
        logging.info('applied_on - %s' % (self.qc_test.applied_on))
        logging.info('product_tmpl_id - %s' % (self.qc_test.product_tmpl_id))
        logging.info('picking_type_ids - %s' % (self.qc_test.picking_type_ids))

        self.assertEqual(self.qc_test.state, 'draft',
                         "QC test state should be in Draft state")
        self.qc_test.do_review()
        self.assertEqual(self.qc_test.state, 'review',
                         "QC test state should be in Review state")
        self.qc_test.do_approve()
        self.assertEqual(self.qc_test.state, 'approve',
                         "QC test state should be in Approved state")
        logging.info("======================================================")
        logging.info("For Purchase and Sale order Test created Succesfully")
        logging.info("======================================================")

    def create_mo_qc_tests(self):
        mrp_operation_ids = self.StockPicking.search([('code', '=',
                                                  'mrp_operation')],
                                                limit=1)

        self.qc_test = self.qc_test.create(dict(
            reference="Computer SC234",
            qc_team_id=self.qc_team.id,
            responsible_id=self.user_1.id,
            active=True,
            applied_on='1_product',
            product_tmpl_id=self.product2.id,
            picking_type_ids=[(6, 0, [mrp_operation_ids.id])],
        ))
        self.qc_test.quantitative_ids = self.quantitative.create(dict(
            name="Test",
            uom_id=self.product2.uom_id.id,
            type='quantitative',
            min_dimension=50,
            min_value=60,
            max_value=100,
            max_dimension=110,
            qc_test_id=self.qc_test.id
        ))
        self.qc_test.qualitative_ids = self.qualitative.create(dict(
            name="Test",
            question_ids=[(0, 0, {'question': 'Test Design'})],
            qc_test_id=self.qc_test.id
        ))

        logging.info('Name - %s' % (self.qc_test.reference))
        logging.info('qc_team_id - %s' % (self.qc_test.qc_team_id))
        logging.info('responsible_id - %s' % (self.qc_test.responsible_id))
        logging.info('applied_on - %s' % (self.qc_test.applied_on))
        logging.info('product_tmpl_id - %s' % (self.qc_test.product_tmpl_id))
        logging.info('picking_type_ids - %s' % (self.qc_test.picking_type_ids))

        self.assertEqual(self.qc_test.state, 'draft',
                         "QC test state should be in Draft state")
        self.qc_test.do_review()
        self.assertEqual(self.qc_test.state, 'review',
                         "QC test state should be in Review state")
        self.qc_test.do_approve()
        self.assertEqual(self.qc_test.state, 'approve',
                         "QC test state should be in Approved state")
        logging.info("======================================================")
        logging.info("For Mrp Production Test created Succesfully")
        logging.info("======================================================")

    def test_po_quality_inspection(self):
        self.create_qc_tests()
        self.po1 = self.PurchaseOrder.create(dict(
            partner_id=self.partner1.id
        ))
        self.po1.order_line.create(dict(
            product_id=self.product1.id,
            name=self.product1.name,
            product_qty=5,
            product_uom=self.product1.uom_id.id,
            date_planned=fields.Datetime.now(),
            price_unit=3000,
            order_id=self.po1.id
        ))
        logging.info('self.po1....%s', (self.po1.name))
        for line in self.po1.order_line:
            logging.info('| %s   | %d   | %d ' % (
                line.product_id.name, line.product_qty,
                line.price_subtotal))
            logging.info(
                '============================================================='
                '====================')
        self.po1.button_confirm()
        self.assertEqual(self.po1.state, 'purchase',
                         'Purchase: PO state should be "Purchase"')
        self.assertEqual(self.po1.picking_count, 1,
                         'Purchase: one picking should be created"')
        self.po1.action_view_picking()
        inspection_id = self.qc_inspection.search([
            ('reference', '=', self.po1.name),
            ('product_id', 'in', [x.product_id.id for x in
                                  self.po1.order_line])], limit=1)

        for quantitative in inspection_id.quantitative_ids:
            quantitative.value = 70
            self.assertEqual(quantitative.dimension_status, 'optimum',
                             'Status: Quantitative status should be optimum')
        for qualitative in inspection_id.qualitative_ids:
            qualitative.name = "Test Qualitative data"
            qualitative.dimension_status = 'optimum'
            qualitative.question_ids = [(0, 0, {'answer': 'yes'})],
            self.assertEqual(qualitative.dimension_status, 'optimum',
                             'Status: Qualitative status should be optimum')

        inspection_id.action_pass()
        self.assertEqual(inspection_id.quality_state, 'pass',
                         "Inspection should be in 'PASS' state")

        process_wizard = self.process_wizard.create({
            'reason_id': self.qc_reason_fail.id,
            'remarks': "Test Fail Reason"})
        process_wizard.with_context({
            'active_ids': inspection_id.id}).action_fail()
        self.assertEqual(inspection_id.quality_state, 'fail',
                         "Inspection should be in 'FAIL' state")

        inspection_id.action_incident()
        incident_id = self.incident_report.search(
            [('product_tmpl_id', '=',
              inspection_id.product_id.product_tmpl_id.id)], limit=1)
        self.assertEqual(incident_id.state, 'new',
                         "Incident should be in 'New' state")

        incident_id.write({
            'inspection_reason_id': self.qc_reason_incident.id,
            'improvements': "Write Improvement Actions Here",
            'protections': "Write Protections Action Here",
            'remarks': "Write Description Here"
        })

        incident_id.action_confirm()
        self.assertEqual(incident_id.state, 'confirm',
                         "Incident should be in 'Confirmed' state")

        incident_id.action_inprogress()
        self.assertEqual(incident_id.state, 'in_progress',
                         "Incident should be in 'In Progress' state")

        incident_id.action_done()
        self.assertEqual(incident_id.state, 'done',
                         "Incident should be in 'Done' state")
        with self.assertRaises(UserError):
            incident_id.unlink()
        logging.info("=============================================")
        logging.info("Purchase order Quality Inspection Completed "
                     "Successfully")
        logging.info("=============================================")

    def test_so_quality_inspection(self):
        self.create_qc_tests()
        self.so1 = self.SaleOrder.create(dict(
            partner_id=self.partner2.id
        ))
        self.so1.order_line.create(dict(
            product_id=self.product1.id,
            name=self.product1.name,
            product_uom_qty=5,
            product_uom=self.product1.uom_id.id,
            price_unit=3000,
            order_id=self.so1.id
        ))
        logging.info('self.so1....%s', (self.so1.name))
        for line in self.so1.order_line:
            logging.info('| %s   | %d   | %d ' % (
                line.product_id.name, line.product_uom_qty,
                line.price_subtotal))
            logging.info(
                '============================================================='
                '====================')
        self.so1.action_confirm()
        self.assertTrue(self.so1.state == 'sale',
                        'Sale: SO should be in state "sale"')
        with self.assertRaises(UserError):
            self.so1.unlink()
        self.assertTrue(self.so1.picking_ids,
                        'Sale Stock: no picking created for stockable products')
        self.assertEqual(self.so1.delivery_count, 1,
                         'Sale: one picking should be created"')
        self.so1.action_view_delivery()

        inspection_id = self.qc_inspection.search([
            ('reference', '=', self.so1.name),
            ('product_id', 'in', [x.product_id.id for x in
                                  self.so1.order_line])], limit=1)

        for quantitative in inspection_id.quantitative_ids:
            quantitative.value = 70
            self.assertEqual(quantitative.dimension_status, 'optimum',
                             'Status: Quantitative status should be optimum')
        for qualitative in inspection_id.qualitative_ids:
            qualitative.name = "Test Qualitative data"
            qualitative.dimension_status = 'optimum'
            qualitative.question_ids = [(0, 0, {'answer': 'no'})],
            self.assertEqual(qualitative.dimension_status, 'optimum',
                             'Status: Qualitative status should be optimum')

        inspection_id.action_pass()
        self.assertEqual(inspection_id.quality_state, 'pass',
                         "Inspection should be in 'PASS' state")

        process_wizard = self.process_wizard.create({
            'reason_id': self.qc_reason_fail.id,
            'remarks': "Test Fail Reason"})
        process_wizard.with_context({
            'active_ids': inspection_id.id}).action_fail()
        self.assertEqual(inspection_id.quality_state, 'fail',
                         "Inspection should be in 'FAIL' state")

        inspection_id.action_incident()
        incident_id = self.incident_report.search(
            [('product_tmpl_id', '=',
              inspection_id.product_id.product_tmpl_id.id)], limit=1)
        self.assertEqual(incident_id.state, 'new',
                         "Incident should be in 'New' state")

        incident_id.write({
            'inspection_reason_id': self.qc_reason_incident.id,
            'improvements': "Write Improvement Actions Here",
            'protections': "Write Protections Action Here",
            'remarks': "Write Description Here"
        })

        incident_id.action_confirm()
        self.assertEqual(incident_id.state, 'confirm',
                         "Incident should be in 'Confirmed' state")

        incident_id.action_inprogress()
        self.assertEqual(incident_id.state, 'in_progress',
                         "Incident should be in 'In Progress' state")

        incident_id.action_done()
        self.assertEqual(incident_id.state, 'done',
                         "Incident should be in 'Done' state")
        with self.assertRaises(UserError):
            incident_id.unlink()
        logging.info("====================================================")
        logging.info("Sale order Quality Inspection Completed Successfully")
        logging.info("====================================================")

    def test_mo_quality_inspection(self):
        self.create_mo_qc_tests()
        mrp_operation_ids = self.StockPicking.search([('code', '=',
                                                       'mrp_operation')],
                                                     limit=1)
        bom = self.env['mrp.bom']._bom_find(product=self.product2,
                                            picking_type=mrp_operation_ids,
                                            company_id=self.user_1.company_id.id)
        self.mo1 = self.env['mrp.production'].create({
            'name': 'MO/Test-00002',
            'product_id': self.product2.id,
            'product_qty': 3,
            'bom_id': bom.id,
            'product_uom_id': self.product2.uom_id.id,
        })
        self.mo1.onchange_product_id()
        self.assertTrue(self.mo1.state == 'confirmed',
                        'Sale: MO should be in state "confirmed"')

        self.mo1.action_assign()
        self.assertTrue(self.mo1.inspection_ids,
                        'Inspection: Inspection should be created for Mo.')
        inspection_id = self.qc_inspection.search([
            ('reference', '=', self.mo1.name),
            ('product_id', '=', self.mo1.product_id.id)], limit=1)

        for quantitative in inspection_id.quantitative_ids:
            quantitative.value = 70
            self.assertEqual(quantitative.dimension_status, 'optimum',
                             'Status: Quantitative status should be optimum')
        for qualitative in inspection_id.qualitative_ids:
            qualitative.name = "Test Qualitative data"
            qualitative.dimension_status = 'optimum'
            qualitative.question_ids = [(0, 0, {'answer': 'no'})],
            self.assertEqual(qualitative.dimension_status, 'optimum',
                             'Status: Qualitative status should be optimum')

        inspection_id.action_pass()
        self.assertEqual(inspection_id.quality_state, 'pass',
                         "Inspection should be in 'PASS' state")

        process_wizard = self.process_wizard.create({
            'reason_id': self.qc_reason_fail.id,
            'remarks': "Test Fail Reason"})
        process_wizard.with_context({
            'active_ids': inspection_id.id}).action_fail()
        self.assertEqual(inspection_id.quality_state, 'fail',
                         "Inspection should be in 'FAIL' state")

        inspection_id.action_incident()
        incident_id = self.incident_report.search(
            [('product_tmpl_id', '=',
              inspection_id.product_id.product_tmpl_id.id)], limit=1)
        self.assertEqual(incident_id.state, 'new',
                         "Incident should be in 'New' state")

        incident_id.write({
            'inspection_reason_id': self.qc_reason_incident.id,
            'improvements': "Write Improvement Actions Here",
            'protections': "Write Protections Action Here",
            'remarks': "Write Description Here"
        })

        incident_id.action_confirm()
        self.assertEqual(incident_id.state, 'confirm',
                         "Incident should be in 'Confirmed' state")

        incident_id.action_inprogress()
        self.assertEqual(incident_id.state, 'in_progress',
                         "Incident should be in 'In Progress' state")

        incident_id.action_done()
        self.assertEqual(incident_id.state, 'done',
                         "Incident should be in 'Done' state")
        with self.assertRaises(UserError):
            incident_id.unlink()
        logging.info("====================================================")
        logging.info("Mrp Production Quality Inspection Completed "
                     "Successfully")
        logging.info("====================================================")