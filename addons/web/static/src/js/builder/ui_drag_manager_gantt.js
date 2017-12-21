flectra.define('web.UIDragManagerGantt', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var misc = require('web.Miscellaneous');
    var bus = require('builder.bus');
    var Qweb = core.qweb;


    return Widget.extend({
        init: function () {
            this._super.apply(this, arguments);
            bus.on('arch_updated', this, this.arch_updated.bind(this));
        },

        arch_updated: function () {
            var self = this;
            if (this._action) {
                this._action.options.action.is_auto_load = true;
                var def = this._action.options.action_manager.do_action(this._action.options.action, this._action.options);
                def.done(function () {
                    self.destroy();
                });
            }
        },

        initDragula: function (register_container, is_revert, action_obj, fields_in_view, non_ext, field_component_widget) {
            var self = this;
            self._action = action_obj;
            self.fields_not_in_view = non_ext;
            self.fields_in_view = fields_in_view;
            self.field_component_widget = field_component_widget;
            self.fields = non_ext;
            self.view_id = action_obj.active_view.fields_view.view_id;
            self.attrs = action_obj.active_view.fields_view.arch.attrs;
            $('.o_calendar_sidebar_container').hide();
            self.disable_tabs([0, 2]);
            self.order_by_asc();
            var sidebar_content = $('.web_sidebar_content');
            sidebar_content.remove();
            var gantt_view = Qweb.render('web.gantt_view', {widget: self});
            $('.tab-pane').append($('<div class="web_sidebar_content">').append(gantt_view));
            var sidebar = $('.web_sidebar');
            sidebar.remove();
            $('.o_main').append(sidebar);
            self.start_date = $('select#date_start');
            self.stop_date = $('select#date_stop');
            self.group_by = $('select#default_group_by');
            self.propertyListener();
            self.setPropertyValues(self.attrs);
        },

        order_by_asc: function () {
            this.ordered_fields = _.sortBy(this.fields, function (field) {
                return field.string.toLowerCase();
            });
        },

        propertyListener: function () {
            var self = this;
            self.start_date.bind('change', this, self.onChange);
            self.stop_date.bind('change', this, self.onChange);
            self.group_by.bind('change', this, self.onChange);

        },

        setPropertyValues: function (attrs) {
            var self = this;
            _.each(attrs, function (e, i) {
                var select = $('select#' + i);
                var input = $('input#' + i);
                if (select.length && i !== 'mode') {
                    select.find(':selected').val(e);
                    select.find(':selected').text(self.fields_in_view[e].string);
                } else {
                    if (select.has('option:contains(' + e + ')').length) {
                        $("select#mode option[value=" + e + "]").prop('selected', true);
                    }

                }
                if (input.length) {
                    input.prop('checked', (e === 'True' ));
                }
            });
        },

        onChange: function (ev) {
            var id = this.id;
            var value = this.value;
            var options = {};
            options.view_id = ev.data.view_id;
            options.pos = 'attributes';
            options.attr_name = id;
            options.attr_value = value;
            options.tag_operation = 'gantt';
            misc.update_view(options);
        },

        disable_tabs: function (arr) {
            $('.web_header').find('a[href="#view"]').tab('show');
            _.each(arr, function (e) {
                var li = $('.web_header').find($('li')).get(e);
                $(li).addClass('disabled');
                $(li).find('a').removeAttr('data-toggle').removeAttr('href');
            })
        }
    });


});