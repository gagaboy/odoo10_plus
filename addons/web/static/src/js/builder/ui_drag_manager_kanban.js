flectra.define('web.UIDragManagerKanban', function (require) {
    "use strict";


    var core = require('web.core');
    var Widget = require('web.Widget');
    var bus = require('builder.bus');
    var view_registry = require('web.view_registry');
    var field_registry = require('web.field_registry');
    var misc = require('web.Miscellaneous');
    var kanban_renderer = require('web.KanbanRenderer');
    var rpc = require('web.rpc');
    var drake = null, view_id;
    var qweb = core.qweb;
    var self;
    var element = [];

    var kanban_view = Widget.extend({

        className: 'web_kanban_editor',

        init: function (parent, context, options) {
            this._super.apply(this, arguments);
            this._action = options.action_obj;
            this.field_component_widget = options.prototype;
            this.register_container = options.dragula_container;
            this.non_ext = options.fields_not_in_view;
            this.sidebar = $('#FieldAttrSideNav');
            bus.on('arch_updated', this, this.arch_updated.bind(this));
        },

        arch_updated: function () {
            var self = this;
            if (this._action) {
                this._action.options.action.is_auto_load = true;
                this.do_action(this._action.options.action, this._action.options).then(function () {
                    core.bus.trigger('clear_cache');
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
                    self.initDragula(self.register_container);
                    $('div.oe_kanban_global_click').not(':first').remove();
                    $('div.o_kanban_header').remove();
                    self.$el.attr('style', "width:1000px;margin:10px");
                });
                $(document.body).click(function (ev) {
                    self._on_lose_focus(ev);
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
            var View = view_registry.get('kanban');
            self.view = new View(fields_view, self._action.options.action.viewManager.env);
            def = self.view.CreateAppBuilderEditor(self, kanban_renderer, editor_params);
            return def;
        },

        initialize_contollers: function () {
            var self = this;
            self.p_invisible = $('#show_invisible');
            self.p_visible = $('#el_invisible');
            self.p_required = $('#el_required');
            self.p_readonly = $('#el_readonly');
            self.p_text = $('#string');
            self.p_tool_tip = $('#tool_tip');
            self.p_placeholder = $('#placeholder');
            self.p_widget_id = $('#widget_id');
            self.p_groups_id = $('#groups_id');
            self.p_default = $('#default');
            self.p_domain = $('#domain');
            self.p_context = $('#context');
            self.p_domain.parent().parent().hide();
            self.p_context.parent().parent().hide();

            //Some controls we don't require in kanban so simply remove them.
            self.p_invisible.parents('div.web_sidebar_checkbox').remove();
            $('#can_edit').parents('div.web_sidebar_checkbox').remove();
            $('#can_delete').parents('div.web_sidebar_checkbox').remove();
            self.p_required.parents('tr').remove();
            self.p_readonly.parents('tr').remove();
            self.p_tool_tip.parents('tr').remove();
            self.p_placeholder.parents('tr').remove();
            var krender = qweb.render('web.sideBarKanbanControls', {});
            self.p_visible.parents('tr').after(krender);
        },

        initDragula: function (register_container) {
            self = this;
            if (drake) {
                drake.destroy();
                self.unbind_property_listener();
            }
            self.initialize_contollers();
            self.exist_fields_obj = self._action.active_view.fields_view.fields;
            self.fields = self.exist_fields_obj;
            self.model = self._action.active_view.fields_view.model;
            self.view_attrs = self._action.active_view.fields_view.arch.attrs;
            self.arch = self._action.active_view.fields_view.arch;
            self.kanban_renderer = new kanban_renderer(self, self.editor.state, {
                arch: self.arch,
                mode: 'readonly',
                viewType: 'kanban'
            });
            self.fields = self.kanban_renderer.state.fields;
            view_id = self._action.active_view.fields_view.view_id;
            self.p_can_create = $('#can_create');
            self.p_can_edit = $('#can_edit');
            self.p_can_delete = $('#can_delete');
            if (self.view_attrs) {
                self.p_can_create.prop('checked', parseInt(self.view_attrs.create));
                self.p_can_edit.prop('checked', parseInt(self.view_attrs.edit));
                self.p_can_delete.prop('checked', parseInt(self.view_attrs.delete));
            }
            $('.web_sidebar_content:eq(4)').hide();//hide As we don't need notebook in kanban view
            $('.web_sidebar_content:eq(5)').hide();//hide As we don't need notebook in kanban view

            drake = dragula(register_container, {
                accepts: function (el, target) {
                    return target !== register_container[0] && register_container[1];
                },
                moves: function (el, target) {
                    return target !== register_container[2];
                },
                copy: function (el) {
                    return $(el).attr('data-action') === 'new';
                },
                revertOnSpill: true,
                direction: 'vertical'
            });
            self._on_focus('.web_span');
            self._eventlistener('drag', 'drop', 'shadow', 'dragend');
            self.read_group_values();
        },

        unbind_property_listener: function () {
            $('#string').unbind('change');
            $('#tool_tip').unbind('change');
            $('#placeholder').unbind('change');
            $('#show_invisible').unbind('change');
            $('#el_invisible').unbind('change');
            $('#el_required').unbind('change');
            $('#el_readonly').unbind('change');
            $('#can_create').unbind('change');
            $('#can_edit').unbind('change');
            $('#can_delete').unbind('change');
            $('#groups_id').unbind('change');
            $('#widget_id').unbind('change');
            $('#default').unbind('change');
            $('#domain').unbind('change');
            $('#context').unbind('change');
            $('#btn_rm_view').unbind('click');
        },

        propertyListener: function () {
            self.p_text.bind('change', this, self.onTextChange);
            self.p_tool_tip.bind('change', this, self.onTextChange);
            self.p_placeholder.bind('change', this, self.onTextChange);
            self.p_default.bind('change', this, self.onTextChange);
            self.p_domain.bind('change', this, self.onTextChange);
            self.p_context.bind('change', this, self.onTextChange);
            self.p_invisible.bind('change', self.onCheckChange);
            self.p_visible.bind('change', self.onCheckChange);
            self.p_required.bind('change', self.onCheckChange);
            self.p_readonly.bind('change', self.onCheckChange);
            self.p_can_create.bind('change', self.onCheckChange);
            self.p_can_edit.bind('change', self.onCheckChange);
            self.p_can_delete.bind('change', self.onCheckChange);
            self.p_groups_id.bind('change', self.onChange);
            self.p_widget_id.bind('change', self.onChange);
        },

        onTextChange: function (ev) {
            var options = {};
        },

        onCheckChange: function () {

        },

        onChange: function () {

        },

        _eventlistener: function (drag, drop, shadow, dragend) {
            drake.on(drag, this.onDrag.bind(drake));
            drake.on(drop, this.onDrop.bind(drake));
            drake.on(shadow, this.onShadow.bind(drake));
            drake.on(dragend, this.onDragEnd.bind(drake));
        },

        onDrag: function (el) {
            element.push(el);
            el.className = "ui-drag-item";
            setTimeout(function () {
                el.className = null;
            }, 100)
        },


        onDrop: function (el, source) {

        },

        table: function () {
            var row = document.createElement("div");
            row.style.height = "100%";
            row.style.width = "100%";
            row.style.backgroundColor = "#0E76A8";
            row.appendChild(document.createTextNode('\u00A0 \u00A0 \u00A0 \u00A0'));
            return row;
        },

        onShadow: function (el, source) {
            $("li[data-id='" + $(el).attr('data-id') + "']").animate({'opacity': '1'}, 200);
            var $currentTable = $(source).closest('table');
            var index = $(source).index();
            $currentTable.find('td').removeClass('tb-hover');
            $currentTable.find('th').removeClass('th-hover');
            $currentTable.find('tr').each(function (i, tr) {
                $(tr).find('td').eq(index).addClass('tb-hover');
                $(tr).find('th').eq(index).addClass('th-hover');
            });
            if (!this._shadow) {
                this._shadow = self.table();
                this._shadow.classList.add("gu-transit");
                this._shadow.classList.add("ui-shadow-border");
            }
            el.style.display = 'none';
            el.parentNode.insertBefore(this._shadow, el);
        },

        onDragEnd: function (el) {
            $(el).removeAttr('style');
            $(el).removeClass('ui-shadow-border');
            $(el).removeClass('gu-transit');
            $(el).removeClass('ui-drag-item');
            if (this._shadow) {
                this._shadow.remove();
                this._shadow = null;
            }
        },

        read_group_values: function () {
            var data = [];
            rpc.query({
                model: 'res.groups',
                method: 'search_read'
            }).then(function (resp) {
                _.each(resp, function (e) {
                    data.push({id: e.id, text: e.display_name})
                });
                $('.group_m2m_select2').select2({
                    placeholder: 'Security Group Names',
                    data: data,
                    multiple: true,
                    value: []
                });
            });
        },

        get_default_value: function (name) {
            var options = {};
            options.view_id = view_id;
            options.model = this.model;
            options.field_name = name;
            options.tag_operation = 'default_value';
            options.op = 'get';
            var ajax = misc.set_or_get_default_value(options);
            if (ajax) {
                ajax.done(function (default_value) {
                    self.p_default.val(default_value[name]);
                });
            }
        },

        setPropertyValue: function ($target) {
            var self = this;
            var attrs = self.fields[self.field_name];
            if (attrs) {
                var string = attrs.string || '';
                self.p_text.val(string);
                self.field_widgets = _.chain(field_registry.map).pairs().filter(function (arr) {
                    return _.contains(arr[1].prototype.supportedFieldTypes, attrs.type) && arr[0].indexOf('.') < 0;
                }).map(function (array) {
                    return array[0];
                }).sortBy().value();
                var data = [];
                for (var i = 0; i < self.field_widgets.length; i++) {
                    data.push({id: i, text: self.field_widgets[i]})
                }
                $('#widget_id').select2({
                    placeholder: 'Widgets',
                    data: data,
                    multiple: false,
                    value: []
                });
                self.get_default_value(self.field_name);
            }

        },

        find_in_columns: function (field_string) {
        },

        find_in_fields: function (field_string, attr_name) {
        },

        getFieldAttribute: function (field_string) {
        },

        _on_lose_focus: function (ev) {
            var self = this;
            var $target = $(ev.target);
            // since we don't want to hide nav-overlay for a specific area click(s) on body.
            if ($target.hasClass('ui-selector-border-kan') || $target.parent('li').hasClass('app_builder-custom')
                || $target[0].tagName === 'TD' || $target.parents('div#FieldAttrSideNav').length) {
                return;
            }
            self.close_sidebar();
            self.$el.find('.ui-selector-border').removeClass('ui-selector-border');
        },

        _on_focus: function (selector) {
            var highlight = 'ui-selector-border-kan';
            var self = this;
            var currentElement = $(selector).click(function (e) {
                currentElement.removeClass(highlight);
                $(this).addClass(highlight);
                self.open_sidebar();
                self.field_name = $(e.target).attr('field_name') || false;
                self.setPropertyValue($(e.currentTarget));
            });
        },
        open_sidebar: function () {
            misc.on_overlay_close();
            this.sidebar.css('width', '350px');
        },
        close_sidebar: function () {
            this.sidebar.css('width', '0');
        }
    });

    //return UIDrag;
    core.action_registry.add('app_builder_kanban_view', kanban_view);
});

