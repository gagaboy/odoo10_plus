flectra.define('web.EditorAppBuilderReports', function (require) {
    "use strict";

    var core = require('web.core');
    var Report = require('report.client_action');
    var ReportSidebar = require('web.ReportEditorSidebar');
    var misc = require('web.Miscellaneous');

    var app_builder_report = Report.extend({

        template: 'web.report_container',
        custom_events: {'configure_app_builder_report': 'generate_report_action_configuration'},

        init: function (parent, action, options) {
            options = _.extend(options, {
                report_url: '/report/html/' + action.report_name + '/' + action.active_ids,
                report_name: action.report_name,
                report_file: action.report_file,
                name: action.name,
                display_name: action.display_name,
                context: {
                    active_ids: action.active_ids
                }
            });
            this.view_id = action.view_id;
            this.res_model = 'ir.actions.report';
            this.res_id = action.id;
            this._super(parent, action, options);
        },
        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.sidebar = new ReportSidebar(self);
            });
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return self.sidebar.prependTo(self.$el);
            });
        },
        _on_iframe_loaded: function () {
            this._super.apply(this, arguments);
        },
        generate_report_action_configuration: function (ev) {
            misc.generate_report_action(ev.data.old_config, ev.data.new_config);
        }

    });

    core.action_registry.add('app_builder_report_editor', app_builder_report)

});