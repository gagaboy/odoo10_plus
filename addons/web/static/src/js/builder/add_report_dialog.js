flectra.define('web.kanban_report_dialog', function (require) {
    "use strict";

    var misc = require('web.Miscellaneous');
    var Dialog = require('web.Dialog');
    var report_templates = [
        {
            name: 'basic_report',
            title: 'Basic Report',
            details: 'Basic Detail Report'
        },
        {
            name: 'blank_report',
            title: 'Blank Report',
            details: 'A perfect report to create form scratch'
        },
    ];


    return Dialog.extend({
        events: {
            'click .app_builder_report_item': 'on_report_template_click',
        },

        init: function (parent, model) {
            this.model = model;
            var options = {
                title: "Select A Report Template",
                size: 'medium',
                buttons: [],
            };
            this._super(parent, options);
        },

        start: function () {
            var $reports = $('<div>').addClass('app_builder_report_dialog');
            _.each(report_templates, function (rtemp) {
                $reports.append($('<div>').addClass('app_builder_report_item')
                    .data("template_name", rtemp.name)
                    .append($('<div>').addClass('app_builder_report_title').text(rtemp.title))
                    .append($('<span>').addClass('app_builder_report_desc').text(rtemp.details))
                );
            });
            this.$el.append($reports);
            return this._super.apply(this, arguments);
        },

        on_report_template_click: function (ev) {
            var self = this;
            var template_item = $(ev.currentTarget);
            misc.new_report_create(this.model, template_item.data('template_name'))
                .then(function (resp) {
                    self.trigger_up('open_record', {
                        id: resp.report_id,
                        view_id: resp.view_id
                    });
                    self.close();
                });
        }
    });

});