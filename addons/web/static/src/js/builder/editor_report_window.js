flectra.define('web.ReportEditorSidebar', function (require) {
    "use strict";
    var Widget = require('web.Widget');
    var rpc = require('web.rpc');
    return Widget.extend({
        template: 'web.reportSideBar',
        events: {
            'change input[type="text"],input[type="checkbox"],select': 'onChange'
        },
        init: function (parent) {
            var self = this;
            this.report_config = parent;
            this._super.apply(this, arguments);
        },
        start: function () {
            var self = this;
            self.$el.find('#id_pmenu').prop('checked', true);
            self.$el.find('.paper_m2m_select2').append($('<option/>', {}));
            self.$el.find('.group_m2m_select2').append($('<option/>', {}));
            self._rpc({
                model: 'ir.actions.report',
                method: 'get_report_data',
                args: [self.report_config.res_id]
            }).then(function (resp) {
                resp = resp[0];
                self.$el.find('#name').val(resp.name);
                if ('paperformat_id' in resp) {
                    setTimeout(function () {
                        self.$el.find('#paperformat_id').val(resp.paperformat_id);
                    }, 100);
                }
                if ('groups_id' in resp) {
                    self.$el.find('#groups_id').val(resp.groups_id).trigger("change");
                }

            });

            rpc.query({
                model: 'report.paperformat',
                method: 'search_read'
            }).then(function (resp) {
                _.each(resp, function (e) {
                    self.$el.find('.paper_m2m_select2').append($('<option/>', {
                        value: e.id,
                        text: e.name
                    }));
                });
            });
            var data = [];
            rpc.query({
                model: 'res.groups',
                method: 'search_read'
            }).then(function (resp) {
                _.each(resp, function (e) {
                    data.push({id: e.id, text: e.name})
                });
                self.$el.find('.group_m2m_select2').select2({
                    placeholder: 'Security Group Names',
                    data: data,
                    multiple: true,
                    value: self.report_config.groups_id
                });
            });

        },
        onChange: function (ev) {
            var $element = $(ev.currentTarget);
            var new_configuration = {};
            var ele_id = $element.attr('id');
            if (ele_id === "id_pmenu") {
                new_configuration['ir_values_id'] = $element.is(':checked') ? 'True' : '';
            }
            else if (ele_id === "name") {
                new_configuration[ele_id] = $element.val();
            } else {
                new_configuration[ele_id] = $element.val();
            }

            this.trigger_up('configure_app_builder_report', {
                old_config: this.report_config,
                new_config: new_configuration
            });
        }
    });
});