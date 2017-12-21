flectra.define('web.UIDragManagerCalendar', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var misc = require('web.Miscellaneous');
    var bus = require('builder.bus');
    var calendar_renderer = require('web.CalendarRenderer');
        var view_registry = require('web.view_registry');
    var Qweb = core.qweb;


    var calendar_view = Widget.extend({

        className: 'web_calendar_editor o_view_manager_content',

        init: function (parent, context, options) {
            this._super.apply(this, arguments);
            this._action = options.action_obj;
            this.field_component_widget = options.prototype;
            this.register_container = options.dragula_container;
            this.fields_not_in_view = options.fields_not_in_view;
            this.fields = options.fields_not_in_view;
            this.fields_in_view = options.fields_view;
            this.view_id = options.action_obj.active_view.fields_view.view_id;
            this.attrs = options.action_obj.active_view.fields_view.arch.attrs;
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

        do_action: function (action, options) {
            return this._super.apply(this, arguments);
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.editor().then(function (editor) {
                    self.editor = editor;
                    self.editor.appendTo(self.$el);
                    self.initDragula();
                });
            });

        },

        editor: function () {
            var self = this;
            var def;
            var fields_view = self._action.active_view.fields_view;
            var editor_params = {
                mode: 'readonly',
                arch: fields_view.arch
            };
            var View = view_registry.get('calendar');
            this.view = new View(fields_view, self._action.options.action.viewManager.env);
            def = this.view.CreateAppBuilderEditor(this, calendar_renderer, editor_params);
            return def;
        },

        initDragula: function () {
            var self = this;
            $('.o_calendar_sidebar_container').hide();
            self.disable_tabs([0, 2]);
            self.order_by_asc();
            var sidebar_content = $('.web_sidebar_content');
            sidebar_content.remove();
            var calendar_view = Qweb.render('web.calendar_view', {widget: self});
            $('.tab-pane').append($('<div class="web_sidebar_content">').append(calendar_view));
            var sidebar = $('.web_sidebar');
            sidebar.remove();
            $('.o_main').append(sidebar);
            self.qcreate = $('input#quick_add');
            self.start_date = $('select#date_start');
            self.stop_date = $('select#date_stop');
            self.delay_field = $('select#date_delay');
            self.color_field = $('select#color');
            self.all_day_field = $('select#all_day');
            self.default_display_field = $('select#mode');
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
            self.qcreate.bind('change', this, self.onChange).bind('change', this, self.onChange);
            self.start_date.bind('change', this, self.onChange);
            self.stop_date.bind('change', this, self.onChange);
            self.delay_field.bind('change', this, self.onChange);
            self.color_field.bind('change', this, self.onChange);
            self.all_day_field.bind('change', this, self.onChange);
            self.default_display_field.bind('change', this, self.onChange);

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
            if (this.id === 'quick_add') {
                options.attr_value = this.checked;
            }
            else {
                options.attr_value = value;
            }

            options.tag_operation = 'calendar';
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

    core.action_registry.add('app_builder_calendar_view', calendar_view);
});