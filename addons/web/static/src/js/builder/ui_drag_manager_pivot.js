flectra.define('web.UIDragManagerPivot', function (require) {
    "use strict";
    var core = require('web.core');
    var Widget = require('web.Widget');
    var bus = require('builder.bus');
    var misc = require('web.Miscellaneous');
    var pivot_renderer = require('web.PivotRenderer');
    var view_registry = require('web.view_registry');
    var Qweb = core.qweb;

    var pivot_view = Widget.extend({

        className: 'web_pivot_editor',

        init: function (parent, context, options) {
            this._super.apply(this, arguments);
            this._action = options.action_obj;
            this.fields_not_in_view = options.fields_not_in_view;
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
            var View = view_registry.get('pivot');
            this.view = new View(fields_view, self._action.options.action.viewManager.env);
            def = this.view.CreateAppBuilderEditor(this, pivot_renderer, editor_params);
            return def;
        },

        initDragula: function () {
            var self = this;
            self.view_id = self._action.active_view.fields_view.view_id;
            self.attrs = self._action.active_view.fields_view.arch.attrs;
            var sidebar_content = $('.web_sidebar_content');
            sidebar_content.remove();
            var pivot_view = Qweb.render('web.pivot_view', {widget: self});
            $('.tab-pane').append($('<div class="web_sidebar_content">').append(pivot_view));
            var sidebar = $('.web_sidebar');
            sidebar.remove();
            $('.o_main').append(sidebar);
            self.p_disable_link = $('input#disable_linking');
            self.p_display_quantity = $('input#display_quantity');
            self.disable_tabs([0, 2]);
            self.propertyListener();
            self.setPropertyValues(self.attrs);
        },

        propertyListener: function () {
            var self = this;
            self.p_disable_link.bind('change', this, self.onChange);
            self.p_display_quantity.bind('change', this, self.onChange);
        },

        setPropertyValues: function (attrs) {
            var self = this;
            _.each(attrs, function (e, i) {
                var input = $('input#' + i);
                if (input.length) {
                    input.prop('checked', e);
                }
            });
        },

        onChange: function (ev) {
            var id = this.id;
            var value = this.checked ? true : '';
            var options = {};
            options.view_id = ev.data.view_id;
            options.pos = 'attributes';
            options.attr_name = id;
            options.attr_value = value;
            options.tag_operation = 'pivot';
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
    core.action_registry.add('app_builder_pivot_view', pivot_view);

});