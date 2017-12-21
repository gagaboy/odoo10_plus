# -*- coding: utf-8 -*-

import unittest
import flectra.tests


@flectra.tests.common.at_install(False)
@flectra.tests.common.post_install(True)
class TestTour(flectra.tests.HttpCase):
    registry_test_mode = False

    @unittest.skip('pending fix for multi-cursor lock problem')
    def test_new_app(self):
        self.phantom_js("/web?builder=app_creator",
                        "flectra.__DEBUG__.services['web_tour.tour'"
                        "].run('builder_tour')",
                        "flectra.__DEBUG__.services['web_tour.tour'"
                        "].tours.builder_tour.ready",
                        login="admin")
