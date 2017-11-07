# -*- coding: utf-8 -*-
# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra.tests.common import TransactionCase


class TestMultiBranch(TransactionCase):
    def setUp(self):
        super(TestMultiBranch, self).setUp()
        self.branch0 = self.env['res.branch'].create({
            'name': 'Test Branch',
            'code': 'TB'})

        self.branch1 = self.env['res.branch'].create({
            'name': 'Test Branch 1',
            'code': 'TB1'})
        self.branch2 = self.env['res.branch'].create(
            {'name': 'Test Branch 2', 'code': 'TB2'})

        self.test_user0 = self.env['res.users'].create({
            'login': 'testuser0',
            'partner_id': self.env['res.partner'].create({
                'name': "Test User0"
            }).id,
            'default_branch_id': self.branch0.id,
            'branch_ids': [(4, self.branch1.id)]
        })

    def test_partner0(self):
        self.model_id = \
            self.env['ir.model'].search([('model', '=', 'res.partner')])
        self.record_rules = self.env['ir.rule'].create({
            'name': 'Partner',
            'model_id': self.model_id.id,
            'domain_force':
                "['|',('branch_id','=', False),'|', "
                "('branch_id','=',user.default_branch_id.id), "
                "('branch_id','in', [b.id for b in user.branch_ids] )]"
        })
        self.branch_partner0 = self.env['res.partner'].create({
            'name': 'Test Partner0',
            'email': 'test@123.example.com',
            'branch_id': self.branch2.id
        })
        self.branch_partner2 = self.env['res.partner'].create(
            {'name': 'Test Partner2', 'email': 'test@123.example.com',
             'branch_id': self.branch1.id})

        self.env = self.env(user=self.test_user0)
        self.branch_partner1 = self.env['res.partner'].create({
            'name': 'Test Partner1',
            'email': 'test@123.example.com',
            'branch_id': self.branch0.id
        })
        self.branch_partner1.sudo(user=self.test_user0).write(
            {"name": 'Test Partner11'})
        self.branch_partner2.sudo(user=self.test_user0).write(
            {"name": 'Test Partner22'})
        self.branch_partner0.sudo(user=self.test_user0).write(
            {"name": 'Test Partner22'})





