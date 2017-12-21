flectra.define('web.ir_actions', function (require) {
    "use strict";
    var core = require('web.core');
    var _t = core._t;

    return {
        get_report_action: function (model) {
            return {
                'name': _t('Reports'),
                'type': 'ir.actions.act_window',
                'res_model': 'ir.actions.report',
                'views': [[false, 'kanban'], [false, 'form']],
                'target': 'current',
                'domain': [],
                'context': {
                    'default_model': model.model,
                    'search_default_model': model.model,
                },
                'help': ' <p class="oe_view_nocontent">Click to add a new report.</p>'
            }
        },
        get_access_control_action: function (model) {
            return {
                'name': _t('Access Control Lists'),
                'type': 'ir.actions.act_window',
                'res_model': 'ir.model.access',
                'views': [[false, 'list'], [false, 'form']],
                'target': 'current',
                'domain': [],
                'context': {
                    'default_model_id': model.id,
                    'search_default_model_id': model.id,
                },
                'help': '<p class="oe_view_nocontent_create">Click to add a new access control list.</p>'
            }
        },
        get_udf_filters_action: function (model) {
            return {
                'name': _t('Filter Rules'),
                'type': 'ir.actions.act_window',
                'res_model': 'ir.filters',
                'views': [[false, 'list'], [false, 'form']],
                'target': 'current',
                'domain': [],
                'context': {
                    'default_model_id': model.model,
                    'search_default_model_id': model.model
                },
                'help': '<p class="oe_view_nocontent_create">Click to add a new filter.</p>'
            }
        },
        get_automation_action: function (model) {
            return {
                'name': _t('Automated Actions'),
                'type': 'ir.actions.act_window',
                'res_model': 'base.automation',
                'views': [[false, 'list'], [false, 'form']],
                'target': 'current',
                'domain': [],
                'context': {
                    'default_model_id': model.id,
                    'search_default_model_id': model.id
                },
                'help': '<p class="oe_view_nocontent_create">Click to add a new automated action.</p>'
            }
        }
    };
});