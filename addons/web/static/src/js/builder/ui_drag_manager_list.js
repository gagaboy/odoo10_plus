flectra.define('web.UIDragManagerList', function (require) {
    "use strict";

    var rpc = require('web.rpc');
    var core = require('web.core');
    var Widget = require('web.Widget');
    var drake = null, view_id;
    var field_dialog = require('web.FieldCreatorDialog');
    var bus = require('builder.bus');
    var view_registry = require('web.view_registry');
    var misc = require('web.Miscellaneous');
    var field_registry = require('web.field_registry');
    var list_renderer = require('web.ListRenderer');
    var self, current_col = [];
    var element = [];

    var list_view = Widget.extend({

        className: 'web_list_editor',

        init: function (parent, context, options) {
            this._super.apply(this, arguments);
            this._action = options.action_obj;
            this.field_component_widget = options.prototype;
            this.register_container = options.dragula_container;
            this.non_ext = options.fields_not_in_view;
            this.sidebar = $('#FieldAttrSideNav');
            bus.on('arch_updated', this, this.arch_updated.bind(this));
        },
        get_security_groups: function () {
            var data = [];
            var auto_load = this._action.options.action.is_auto_load;
            rpc.query({
                model: 'res.groups',
                method: 'search_read'
            }).then(function (resp) {
                _.each(resp, function (e) {
                    data.push({id: e.id, text: e.display_name})
                });
                if (!auto_load) {
                    $('.group_m2m_select2').select2({
                        placeholder: 'Security Group Names',
                        data: data,
                        multiple: true,
                        value: []
                    });
                }
            });
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
                    self.sidebar.remove();//remove side bar so it does not get registerd to dragula lib;
                    self.editor.appendTo(self.$el);
                    self.register_container = self.register_container
                        .concat(Array.from(document.querySelectorAll("td.web_td")));
                    self.initDragula(self.register_container);
                    $('.web_body').append(self.sidebar);//reinitialize sidebar after resolving conflict with dragula as we need it/
                    self.initialize_contollers();
                    self.propertyListener();
                    self.$el.attr('style', 'margin-top:10px');
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
            var View = view_registry.get('list');
            this.view = new View(fields_view, self._action.options.action.viewManager.env);
            def = this.view.CreateBuilderEditor(this, list_renderer, editor_params);
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

        },

        initDragula: function (register_container) {
            self = this;
            if (drake) {
                drake.destroy();
                self.unbind_property_listener();
            }

            //self._action = action_obj;
            //self.non_ext = non_ext;
            self.exist_fields_obj = self._action.active_view.fields_view.fields;
            self.fields = self.exist_fields_obj;
            //self.field_component_widget = field_component_widget;
            self.model = self._action.active_view.fields_view.model;
            self.view_attrs = self._action.active_view.fields_view.arch.attrs;
            self.arch = self._action.active_view.fields_view.arch;
            self.list_renderer = new list_renderer(self, {}, {
                arch: self.arch,
                mode: 'readonly',
                viewType: 'list'
            });
            view_id = self._action.active_view.fields_view.view_id;
            self.p_can_create = $('#can_create');
            self.p_can_edit = $('#can_edit');
            self.p_can_delete = $('#can_delete');
            if (self.view_attrs) {
                self.p_can_create.prop('checked', parseInt(self.view_attrs.create));
                self.p_can_edit.prop('checked', parseInt(self.view_attrs.edit));
                self.p_can_delete.prop('checked', parseInt(self.view_attrs.delete));
            }
            $('.web_sidebar_content:eq(2)').hide();//hide As we don't need notebook in list view

            drake = dragula(register_container, {
                accepts: function (el, target) {
                    return target !== register_container[0] && register_container[1];
                },
                moves: function (el, target) {
                    return target !== register_container[2];
                },
                copy: function (el, target) {
                    return $(el).attr('data-action') === 'new';
                },
                revertOnSpill: true,
                direction: 'horizontal'
            });

            self._eventlistener('drag', 'drop', 'shadow', 'dragend');
            var first_column = $(".o_list_view tr td:first-child,th:first-child");
            first_column.remove();
            var td = $('<td class="web_td"></td>');
            var th = $('<th class="web_th"></th>');
            $('td').before(td);
            $('th').before(th);
            drake.containers = drake.containers.concat(Array.from(document.querySelectorAll('.web_td')));
            $(".o_column_sortable").removeClass('o_column_sortable');
            $('tr[data-id]').removeAttr('data-id');

            $("th,td").hover(function () {
                var index = $(this).index();
                $("th, td").filter(":nth-child(" + (index + 1) + ")").addClass("current-col");
                $("th").filter(":nth-child(" + (index + 1) + ")").addClass("current-col").addClass('header-tab');
            }, function () {
                var index = $(this).index();
                $("th, td").removeClass("current-col");
                $("th").filter(":nth-child(" + (index + 1) + ")").removeClass("current-col").removeClass('header-tab');
            });

            self.get_security_groups();
            self._on_focus('th,td');
            $(document.body).on('click', '#btn_rm_view', function () {
                if (current_col.length) {
                    _.each(current_col, function (e, i) {
                        $(e).remove();
                    });
                    var nearest = $(current_col[0]);
                    var field_properties = self.find_in_fields(nearest.text(), 'string') || self.find_in_columns(nearest.text(), 'string');
                    var options = {};
                    options.view_id = view_id;
                    options.xpath_field_name = field_properties.name;
                    options.tag_operation = 'delete_field';
                    misc.update_list_view(options);
                }
            });

            $('tbody tr').on('click', function (ev) {
                ev.stopImmediatePropagation();
                return false;
            });
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
            var nearest = $(current_col[0]);
            var field_properties = self.find_in_fields(nearest.text(), 'string') || self.find_in_columns(nearest.text(), 'string');
            options.view_id = view_id;
            options.attr_value = $(this).val();
            options.xpath_field_name = field_properties.name || field_properties.attrs.name;
            options.tag_operation = 'change_field_attrs';
            options.model = ev.data.model;
            if (this.id === "default") {
                if (current_col.length) {
                    options.tag_operation = 'default_value';
                    options.field_name = options.xpath_field_name;
                    options.value = options.attr_value;
                    options.op = 'set';
                    misc.set_or_get_default_value(options);
                }
            } else {
                if (this.id === "string") {
                    if (current_col.length) {
                        options.attr_type = 'string';
                    }
                }

                else if (this.id === "tool_tip") {
                    if (current_col.length) {
                        options.attr_type = 'help';
                    }
                }

                else if (this.id === "placeholder") {
                    if (current_col.length) {
                        options.attr_type = 'placeholder';
                    }
                }
                else if (this.id === "domain") {
                    options.attr_type = 'domain';
                }

                else if (this.id === "context") {
                    options.attr_type = 'context';
                }
                misc.update_list_view(options);
            }
        },

        onCheckChange: function () {
            var options = {};
            options.view_id = view_id;
            options.attr_value = this.checked ? 1 : 0;
            var nearest = $(current_col[0]);
            var field_properties = self.find_in_fields(nearest.text(), 'string') || self.find_in_columns(nearest.text(), 'string');
            options.xpath_field_name = field_properties.name || field_properties.attrs.name;
            options.tag_operation = 'change_field_attrs';
            if (this.id === "el_invisible") {
                options.attr_type = 'invisible';
                misc.update_list_view(options);
            }
            else if (this.id === "el_required") {
                options.attr_type = 'required';
                misc.update_list_view(options);
            }
            else if (this.id === "el_readonly") {
                options.attr_type = 'readonly';
                misc.update_list_view(options);
            }
            else if (this.id === "can_create") {
                options.attr_type = 'create';
                options.xpath_field_name = 'tree';
                misc.update_list_view(options);
            }
            else if (this.id === "can_edit") {
                options.attr_type = 'edit';
                options.xpath_field_name = 'tree';
                misc.update_list_view(options);
            }
            else if (this.id === "can_delete") {
                options.attr_type = 'delete';
                options.xpath_field_name = 'tree';
                misc.update_list_view(options);
            }

        },

        onChange: function () {
            var options = {};
            options.view_id = view_id;
            var nearest = $(current_col[0]);
            var field_properties = self.find_in_fields(nearest.text(), 'string') || self.find_in_columns(nearest.text(), 'string');
            options.xpath_field_name = field_properties.name || field_properties.attrs.name;
            options.tag_operation = 'change_field_attrs';
            if (this.id === "widget_id") {
                options.attr_type = 'widget';
                options.attr_value = self.field_widgets[$(this).val()];
                misc.update_list_view(options);
            }
            if (this.id === 'groups_id') {
                rpc.query({
                    model: 'ir.model.data',
                    method: 'search_read',
                    domain: [['res_id', '=', $(this).val()], ['model', '=', 'res.groups']]
                }).then(function (resp) {
                    _.each(resp, function (e) {
                        options.attr_value = e.complete_name;
                        options.attr_type = 'groups';
                        misc.update_list_view(options);
                    });
                });
            }
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
            var $currentTable = $(source).closest('table');
            var index = $(source).index();
            var nearest = null, def = null;
            var result = [], options = {};
            $currentTable.find('tr').each(function (i, tr) {
                if ($(tr).find('th').eq(index + 1).length > 0) {
                    nearest = $(tr).find('th').eq(index + 1)
                }
            });
            var field_properties = self.find_in_fields(nearest.text(), 'string') || self.find_in_columns(nearest.text(), 'string');
            console.log('data-action', $(el));
            if ($(el).attr('data-action') === 'new') {
                _.each(self.field_component_widget, function (prototype) {
                    if (prototype['label'] === $(el).attr("data-id")) {
                        if (_.contains(['selection', 'one2many', 'many2one', 'many2many'], prototype['type'])) {
                            def = $.Deferred();
                            var dialog = new field_dialog(self, self.model, prototype['type'], prototype).open();
                            dialog.on('save_field', self, function (values) {
                                options.field_name = "x_builder_" + misc.rstring(4);
                                options.label = prototype['label'] + ' ' + misc.rstring(4);
                                options.field_type = prototype['type'];
                                options.selection_list = values.selection ? values.selection : null;
                                options.rel_id = values.rel_id ? values.rel_id : null;
                                options.field_description = values.field_description ? values.field_description : null;
                                def.resolve(options);
                                dialog.close();
                            });
                        } else {
                            def = $.Deferred();
                            options.field_name = "x_builder_" + misc.rstring(4);
                            options.label = prototype['label'] + ' ' + misc.rstring(4);
                            options.field_type = prototype['type'];
                            def.resolve(options);
                        }
                        $.when(def).then(function (values) {
                            options.view_id = view_id;
                            options.xpath_field_name = field_properties.name || field_properties.attrs.name;
                            options.tag_operation = 'add_field';
                            options = _.extend(options, values);
                            misc.update_list_view(options);
                        });
                    }

                });
            } else {
                $.when(def).then(function (values) {
                    options.view_id = view_id;
                    options.field_name = $(el).attr('data-id');
                    options.xpath_field_name = field_properties.name || field_properties.attrs.name;
                    options.tag_operation = 'add_field';
                    misc.update_list_view(options);
                });
            }
        },

        table: function () {
            var row = document.createElement("div");
            row.style.height = "100%";
            row.style.width = "3%";
            row.style.position = "absolute";
            row.style.top = "0px";
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

        setPropertyValue: function (current_col) {
            var self = this;
            var data = [];
            var nearest = $(current_col[0]);
            var attrs = self.find_in_fields(nearest.text(), 'string') || self.find_in_columns(nearest.text(), 'string');
            if (attrs) {
                var name = attrs.name || attrs.attrs.name;
                var new_attr = self.find_in_columns(attrs.name, 'name');
                if (new_attr)
                    attrs = _.extend({}, attrs, new_attr.attrs);
                var modifier = attrs || attrs['attrs'] || self.find_in_fields(name, 'name');
                self.get_default_value(name);
                self.p_tool_tip.val(modifier.help);
                self.p_placeholder.val(modifier.placeholder);
                self.p_required.prop('checked', modifier.required ? 1 : 0);
                self.p_readonly.prop('checked', modifier.readonly ? 1 : 0);
                var auto_load = this._action.options.action.is_auto_load;
                if (modifier.type) {
                    self.field_widgets = _.chain(field_registry.map).pairs().filter(function (arr) {
                        return _.contains(arr[1].prototype.supportedFieldTypes, modifier.type) && arr[0].indexOf('.') < 0;
                    }).map(function (array) {
                        return array[0];
                    }).sortBy().value();
                    for (var i = 0; i < self.field_widgets.length; i++) {
                        data.push({id: i, text: self.field_widgets[i]})
                    }
                    if (!auto_load) {
                        $('#widget_id').select2({
                            placeholder: 'Form Widgets',
                            data: data,
                            multiple: false,
                            value: []
                        });
                    }
                    if (modifier.type === 'many2many') {
                        self.p_domain.parent().show();
                        self.p_context.parent().show();
                    } else {
                        self.p_domain.parent().hide();
                        self.p_context.parent().hide();
                    }
                }
            } else {
                self.p_text.val("");
                self.p_tool_tip.val("");
                self.p_placeholder.val("");
                self.p_domain.val("");
                self.p_context.val("");
            }
            _.each(current_col, function (e, i) {
                if (i === 0) {
                    self.p_text.val($(e).html().trim() ? $(e).html().trim() : "");
                }
                if (e) {
                    if (e.tagName === "TD") {
                        self.p_tool_tip.val($(e).attr('title') ? $(e).attr('title') : "");
                    }
                }
            });

        },

        find_in_columns: function (field_string, attr_name) {
            var field_attrs = null;
            _.each(self.list_renderer.columns, function (object) {
                if (object.attrs[attr_name] === field_string) {
                    field_attrs = object;
                }
            });
            return field_attrs
        },

        find_in_fields: function (field_string, attr_name) {
            var field_attrs = null;
            _.each(self.exist_fields_obj, function (object) {
                if (object[attr_name] === field_string) {
                    field_attrs = object;
                }

            });
            return field_attrs
        },

        getFieldAttribute: function (field_string) {
            var field_attrs = null;
            _.each(self.exist_fields_obj, function (object) {
                if (object.name === field_string) {
                    field_attrs = object;
                }
            });
            return field_attrs
        },
        _on_lose_focus: function (ev) {
            var self = this;
            var $target = $(ev.target);
            // since we don't want to hide nav-overlay for a specific area click(s) on body.
            if ($target.parent().parent().hasClass('ui-selector-border') || $target.parent('li').hasClass('app_builder-custom')
                || $target[0].tagName === 'TD' || $target.parents('div#FieldAttrSideNav').length) {
                return;
            }
            self.close_sidebar();
            self.$el.find('.ui-selector-border').removeClass('ui-selector-border');
        },

        _on_focus: function (selector) {
            var highlight = 'ui-selector-border-col';
            $(selector).click(function (e) {
                self.open_sidebar();
                var $currentTable = $(this).closest('table');
                var index = $(this).index();
                $currentTable.find('td,th').removeClass(highlight);
                current_col = [];
                $currentTable.find('tr').each(function () {
                    $(this).find('td,th').eq(index).addClass(highlight);
                    current_col.push($(this).find('td,th').eq(index)[0]);
                });
                if (current_col) {
                    self.setPropertyValue(current_col);
                }
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
    core.action_registry.add('app_builder_list_view', list_view);
});

