flectra.define('web.UIDragManagerForm', function (require) {
    "use strict";
    var core = require('web.core');
    var Widget = require('web.Widget');
    var rpc = require('web.rpc');
    var misc = require('web.Miscellaneous');
    var field_dialog = require('web.FieldCreatorDialog');
    var field_registry = require('web.field_registry');
    var button_dialog = require('web.AddButtonDialog');
    var bus = require('builder.bus');
    var form_renderer = require('web.FormRenderer');
    var view_registry = require('web.view_registry');
    var drake = null;
    var QWeb = core.qweb;
    var self;
    var element = [];
    var selected_label, selected_tab;

    var form_view = Widget.extend({

        className: 'web_form_editor',

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
                    self.register_container = self.register_container.concat(Array.from(self.$el[0].querySelectorAll("tbody")));
                    self.initDragula(self.register_container);
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
            var View = view_registry.get('form');
            this.view = new View(fields_view, self._action.options.action.viewManager.env);
            def = this.view.CreateBuilderEditor(this, form_renderer, editor_params);
            return def;
        },

        initDragula: function (register_container) {
            self = this;
            if (drake) {
                drake.destroy();
                self.unbind_property_listener();
                $('.o_form_sheet').find('.oe_button_box').find('#add_button').first().remove();
                $('#add-tab').remove();
            }
            self.p_text = $('#string');
            self.p_tool_tip = $('#tool_tip');
            self.p_placeholder = $('#placeholder');
            self.p_invisible = $('#show_invisible');
            self.p_visible = $('#el_invisible');
            self.p_required = $('#el_required');
            self.p_readonly = $('#el_readonly');
            self.p_groups_id = $('#groups_id');
            self.p_widget_id = $('#widget_id');
            self.p_default = $('#default');
            self.p_domain = $('#domain');
            self.p_context = $('#context');
            self.p_can_create = $('#can_create');
            self.p_can_edit = $('#can_edit');
            self.p_can_delete = $('#can_delete');
            self.p_domain.parent().parent().hide();
            self.p_context.parent().parent().hide();
            self.exist_fields_obj = self._action.active_view.fields_view.fields;
            self.view_id = self._action.active_view.fields_view.view_id;
            self.arch = self._action.active_view.fields_view.arch;
            self.model = self._action.active_view.fields_view.model;
            self.view_attrs = self.arch.attrs;
            self.$button = QWeb.render('web.sideBar.button', {});
            self.form_renderer = new form_renderer(self, {}, {
                arch: self.arch,
                viewType: 'form'
            });
            self.new_arch = self.form_renderer.arch;

            drake = dragula(register_container, {
                revertOnSpill: true,
                accepts: function (el, target) {
                    return target !== register_container[0];
                },
                moves: function (el, target) {
                    return target.tagName !== "TBODY";
                },
                copy: function (el, target) {
                    return $(el).attr('data-action') === 'new';
                }
            });

            $('div.o_notebook > ul > li').addClass('app_builder-custom');

            var len = $('div.o_notebook').length;
            for (var i = 0; i < len; i++) {
                $($('div.o_notebook')[i]).attr('notebook_id', i + 1);
            }
            if (self.view_attrs) {
                self.p_can_create.prop('checked', parseInt(self.view_attrs.create));
                self.p_can_edit.prop('checked', parseInt(self.view_attrs.edit));
                self.p_can_delete.prop('checked', parseInt(self.view_attrs.delete));
            }

            $('.o_form_sheet').find('.oe_button_box').prepend(self.$button);
            $('.o_form_view').find('header').remove();
            $('.o_chatter').remove();
            $('.o_form_sheet').find("tr").addClass('app_builder-custom');
            $('.o_form_sheet').find("table.o_group").each(function (i, e) {
                if ($(e).children().children().children().length === 0) {
                    $(e).addClass('empty_container');
                    var tbody = '<tbody><tr><td>&nbsp;</td><td>&nbsp;</td></tr></tbody>';
                    $(e).append(tbody);
                    drake.containers.push($(e).children()[1]);
                }
            });
            self.unbind_events();
            self._on_focus('.app_builder-custom');
            self.attachTab();
            self.propertyListener();
            self._eventlistener('drag', 'drop', 'shadow', 'dragend');
            self.read_group_values();
        },

        uniqueIdGenerator: function () {
            return (Math.random() * Math.pow(36, 4) << 0).toString(36);
        },

        unbind_events: function () {
            var links = $('a');
            _.each(links, function (e) {
                if ($(e).hasClass('o_form_uri')) {
                    $(e).unbind();
                    $(e).attr('href', 'javascript:void(0);');
                }
            });
            $('button').unbind();
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

        attachTab: function () {
            var tab = QWeb.render("web.addTab", {});
            var navtabs = $(".o_notebook > ul");
            navtabs.append(tab);
            $(navtabs).on("click", "a", function (e) {
                e.preventDefault();
                if (!$(this).is('#add-tab')) {
                    $(this).tab('show');
                }
            }).on("click", "span", function () {
                var anchor = $(this).siblings('a');
                $(anchor.attr('href')).remove();
                $(this).parent().remove();
                $(".nav-tabs li").children('a').first().click();
            });
            $('#add-tab').bind('click', {navtabs: navtabs}, this.onClick);
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
            $('#add_button').unbind('click');
            $('#btn_rm_view').unbind('click');
            $('#btn_hide_nav').unbind('click');
            $('#add_notebook').unbind('click');
        },

        propertyListener: function () {
            self.p_text.bind('change', self.onTextChange);
            self.p_tool_tip.bind('change', self.onTextChange);
            self.p_placeholder.bind('change', self.onTextChange);
            self.p_invisible.bind('change', self.onCheckChange);
            self.p_visible.bind('change', self.onCheckChange);
            self.p_required.bind('change', self.onCheckChange);
            self.p_readonly.bind('change', self.onCheckChange);
            self.p_can_create.bind('change', self.onCheckChange);
            self.p_can_edit.bind('change', self.onCheckChange);
            self.p_can_delete.bind('change', self.onCheckChange);
            self.p_groups_id.bind('change', self.onChange);
            self.p_widget_id.bind('change', self.onChange);
            self.p_default.bind('change', self.onTextChange);
            self.p_domain.bind('change', self.onTextChange);
            self.p_context.bind('change', self.onTextChange);
            $('#add_button').bind('click', self.onClick);
            $('#btn_rm_view').bind('click', self.onClick);
            $('#btn_hide_nav').bind('click', self.onClick);
            $('#add_notebook').bind('click', self.onClick);
        },

        onClick: function (e) {
            var options = {};
            if (this.id === 'add_button') {
                var dialog = new button_dialog(self).open();
                options.view_id = self.view_id;
                options.pos = 'inside';
                options.tag_operation = 'add_button';
                options.field_type = 'many2one';
                dialog.on('save', self, function (values) {
                    options = _.extend(options, values);
                    misc.update_view(options);
                });
            }
            else if (this.id === 'btn_rm_view') {
                var to_remove = $(drake.containers).find('.ui-selector-border');
                if (to_remove.length > 0) {
                    var r_id = $(to_remove).attr('data-id');
                    if (element.length > 0) {
                        for (var i = 0; i < element.length; i++) {
                            if (r_id === $(element[i]).attr('data-id')) {
                                $('.web_sidebar_field_container ul').prepend(element[i])
                            }
                        }
                    }
                    var field_str = to_remove.find('label').html().trim();
                    var field_name = self.getFieldAttribute(field_str, 'string').name;
                    options.view_id = self.view_id;
                    options.field_name = field_name;
                    options.pos = 'replace';
                    options.tag_operation = 'field';
                    to_remove.remove();
                    misc.update_view(options);
                }
                else {
                    to_remove = self._action.el.find(".ui-selector-border");
                    var notebook_pos = $(to_remove).parent().parent().attr('notebook_id');
                    var total_page = $(to_remove).siblings().length - 1;
                    $(to_remove).remove();
                    $(to_remove.find('a').attr('href')).remove();
                    var result = [];
                    self.tabArch(self.arch, result, 'page');
                    for (var i in result) {
                        if (result[i].attrs.string) {
                            if (result[i].attrs.string === selected_tab.text().trim()) {
                                options.view_id = self.view_id;
                                options.pos = 'replace';
                                options.tag_operation = 'page';
                                options.field_name = result[i].attrs.name;
                                options.total_page = total_page;
                                options.notebook_id = notebook_pos;
                                to_remove.remove();
                                misc.update_view(options);
                            }
                        }
                    }
                }
            }

            else if (this.id === 'add_notebook') {
                var notebook = QWeb.render('web.notebook', {});
                $('.o_form_sheet').append(notebook);
                options.group_id = "app_builder_group_" + self.uniqueIdGenerator();
                options.view_id = self.view_id;
                options.pos = 'inside';
                options.tag_operation = 'notebook';
                misc.update_view(options);
            }

            else if (this.id === 'add-tab') {
                e.preventDefault();
                var prev_tab_name = $(this).parent().prev().find('a').html().trim();
                var notebook_pos = $(this).parent().parent().parent().attr('notebook_id');
                var navtabs = e.data.navtabs;
                var tab_string = "New Tab " + self.uniqueIdGenerator();
                var group_id = "app_builder_group_" + self.uniqueIdGenerator();
                var id = $(navtabs).children().length; //think about it ;)
                var tabId = 'contact_' + id;
                $(this).closest('li').before('<li class="app_builder-custom"><a href="#contact_' + id + '">' + tab_string + '</a></li>');
                var tab = '<div class="tab-pane" id="' + tabId + '">' +
                    '<div class="o_group">' +
                    '<table class="o_group o_inner_group o_group_col_6">' +
                    '<tbody>' +
                    '<tr class="app_builder-custom">' +
                    '<td colspan="2" style="width: 100%;">  |' +
                    '</td>' +
                    '</tr>' +
                    '<tr class="app_builder-custom">' +
                    '<td colspan="1" class="o_td_label"> ' +
                    '</td>' +
                    '<td colspan="1" style="width: 100%;">' +
                    '</td>' +
                    '</tr>' +
                    '</tbody>' +
                    '</table>' +
                    '</div>' +
                    '</div>';
                $(navtabs.siblings()).append(tab);
                options.view_id = self.view_id;
                options.pos = 'after';
                options.tab_name = prev_tab_name;
                options.tab_string = tab_string;
                options.group_id = group_id;
                options.notebook_id = notebook_pos;
                options.tag_operation = 'page';
                misc.update_view(options);

                // Register New Container with event
                var len = $(navtabs.siblings()).find('tbody').length;
                var tbody = $(navtabs.siblings()).find('tbody')[len - 1];
                drake.containers.push(tbody);
                self._on_focus('.app_builder-custom');
            } else if (this.id === "btn_hide_nav") {
                self.close_sidebar();
            }
        },

        onTextChange: function () {
            var options = {};
            var old_text;
            options.view_id = self.view_id;
            options.pos = 'attributes';
            if (this.id === "string") {
                var new_text = $(this).val();
                options.tab_string = new_text;
                options.attr_name = 'string';
                if (selected_label !== null) {
                    old_text = selected_label.text();
                    options.field_name = self.getFieldAttribute(old_text, 'string').name;
                    options.tag_operation = 'field';
                    misc.update_view(options);
                    selected_label.text(new_text);
                }
                else if (selected_tab !== null) {
                    var result = [];
                    old_text = selected_tab.text();
                    self.tabArch(self.arch, result, 'page');
                    for (var i in result) {
                        if (result[i].attrs.string) {
                            if (result[i].attrs.string === old_text.trim()) {
                                options.field_name = result[i].attrs.name;
                                options.tag_operation = 'page';
                                misc.update_view(options);
                                break;
                            }
                        }
                    }
                }
            }
            else if (this.id === "tool_tip") {
                old_text = selected_label.text();
                var help_text = $(this).val();
                options.tag_operation = 'field';
                options.field_name = self.getFieldAttribute(old_text, 'string').name;
                options.tab_string = help_text;
                options.attr_name = 'help';
                misc.update_view(options);
            }
            else if (this.id === "placeholder") {
                old_text = selected_label.text();
                var placeholder = $(this).val();
                options.tag_operation = 'field';
                options.field_name = self.getFieldAttribute(old_text, 'string').name;
                options.tab_string = placeholder;
                options.attr_name = 'placeholder';
                misc.update_view(options);
            } else if (this.id === "default") {
                old_text = selected_label.text();
                var default_value = $(this).val();
                options.tag_operation = 'default_value';
                options.field_name = self.getFieldAttribute(old_text, 'string').name;
                options.value = default_value;
                options.model = self.model;
                options.op = 'set';
                misc.set_or_get_default_value(options);
            } else if (this.id === "domain") {
                old_text = selected_label.text();
                options.tag_operation = 'field';
                options.field_name = self.getFieldAttribute(old_text, 'string').name;
                options.tab_string = $(this).val();
                options.attr_name = 'domain';
                misc.update_view(options);

            } else if (this.id === "context") {
                old_text = selected_label.text();
                options.tag_operation = 'field';
                options.field_name = self.getFieldAttribute(old_text, 'string').name;
                options.tab_string = $(this).val();
                options.attr_name = 'context';
                misc.update_view(options);
            }
        },

        onChange: function () {
            var options = {};
            options.view_id = self.view_id;
            options.pos = "attributes";
            if (this.id === 'groups_id') {
                rpc.query({
                    model: 'ir.model.data',
                    method: 'search_read',
                    domain: [['res_id', '=', $(this).val()], ['model', '=', 'res.groups']]
                }).then(function (resp) {
                    _.each(resp, function (e) {
                        options.field_name = self.getFieldAttribute(selected_label.text(), 'string').name;
                        options.tag_operation = 'field';
                        options.tab_string = e.complete_name;
                        options.attr_name = 'groups';
                        misc.update_view(options);
                    });
                });
            }
            if (this.id === 'widget_id') {
                var widget_text = self.field_widgets[$(this).val()];
                options.field_name = self.getFieldAttribute(selected_label.text(), 'string').name;
                options.tag_operation = 'field';
                options.tab_string = widget_text;
                options.attr_name = 'widget';
                misc.update_view(options);
            }
        },

        onCheckChange: function () {
            var options = {};
            var old_text = selected_label ? selected_label.text() : '';
            options.tag_operation = 'field';
            if(old_text)
                options.field_name = self.getFieldAttribute(old_text, 'string')['name'] || '';
            options.view_id = self.view_id;
            options.pos = "attributes";
            if (this.id === "show_invisible") {
                if (this.checked) {
                    self._action.el.find('.o_invisible_modifier').each(function (i, e) {
                        if (e.tagName.toLowerCase() === "label") {
                            $(e).removeClass('o_invisible_modifier').parent().parent().addClass('web_show_invisible');
                        } else {
                            $(e).removeClass('o_invisible_modifier').addClass('web_show_invisible');
                        }
                    });
                } else {
                    self._action.el.find('.web_show_invisible').removeClass('web_show_invisible').addClass('o_invisible_modifier');
                }
            }
            if (this.id === "el_invisible") {
                options.attr_name = 'invisible';
                if (this.checked) {
                    selected_label.addClass('o_form_invisible');
                    selected_label.parent().siblings().children().addClass('o_form_invisible');
                    options.tab_string = '1';
                } else {
                    selected_label.removeClass('web_show_invisible').removeClass('o_form_invisible');
                    selected_label.parent().siblings().children().removeClass('web_show_invisible').removeClass('o_form_invisible');
                    options.tab_string = '0';
                }
                misc.update_view(options);
            }
            if (this.id === "el_required") {
                options.attr_name = 'required';
                if (this.checked) {
                    options.tab_string = '1';
                } else {
                    options.tab_string = '0';
                }
                misc.update_view(options);
            }
            if (this.id === "el_readonly") {
                options.attr_name = 'readonly';
                if (this.checked) {
                    options.tab_string = '1';
                } else {
                    options.tab_string = '0';
                }
                misc.update_view(options);
            }
            if (this.id === 'can_create') {
                options.attr_name = 'create';
                options.field_name = 'form';
                if (this.checked) {
                    options.tab_string = '1';
                } else {
                    options.tab_string = '0';
                }
                misc.update_view(options);
            }
            if (this.id === 'can_edit') {
                options.attr_name = 'edit';
                options.field_name = 'form';
                if (this.checked) {
                    options.tab_string = '1';
                } else {
                    options.tab_string = '0';
                }
                misc.update_view(options);
            }
            if (this.id === 'can_delete') {
                options.attr_name = 'delete';
                options.field_name = 'form';
                if (this.checked) {
                    options.tab_string = '1';
                } else {
                    options.tab_string = '0';
                }
                misc.update_view(options);
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
            }, 100);
        },

        prevUntil: function (source, id) {
            var e_prev = $(source).find('tr[data-id=' + id + ']').prev().prev();
            if (e_prev.hasClass('app_builder-custom')) {
                return e_prev;
            }
            return undefined;
        },

        nextUntil: function (source, id) {
            var e_next = $(source).find('tr[data-id=' + id + ']').next();
            if (e_next.hasClass('app_builder-custom')) {
                return e_next;
            }
            return undefined;
        },

        find_field_xpath: function (fields, match, pos) {
            //@todo Wrapper method in case we need pre-processing with fields
            return {
                'xpath_field': self.getFieldAttribute(match, 'string').name,
                'position': pos
            }
        },

        onDrop: function (el, source) {
            var options = {};
            var def = null;
            options.field_name = $(el).attr('data-id');
            options.view_id = self.view_id;
            options.tag_operation = 'field';
            var fields_in_view = self._action.active_view.fields_view.fields;
            var res = [];
            var rendered = QWeb.render('web.char', {
                'id': options.field_name,
                'f_data': "",
                'string': ""
            });
            $(el).replaceWith(rendered);
            options.nearest_prev = self.prevUntil(source, options.field_name)
                ? self.prevUntil(source, options.field_name).find('label,div').html().trim() : undefined;
            options.nearest_next = self.nextUntil(source, options.field_name)
                ? self.nextUntil(source, options.field_name).find('label,div').html().trim() : undefined;
            if (options.nearest_next !== undefined || options.nearest_prev !== undefined) {
                var data = self.find_field_xpath(fields_in_view,
                    'before' ? options.nearest_prev : options.nearest_next
                    , options.nearest_prev ? 'after' : 'before');
                if (data) {
                    options.xpath_field = data.xpath_field;
                    options.pos = data.position;
                }
                else {
                    data = self.find_field_xpath(fields_in_view,
                        'before' ? options.nearest_next : options.nearest_prev
                        , options.nearest_next ? 'before' : 'after');
                    options.xpath_field = data.xpath_field;
                    options.pos = data.position;
                }
            }
            if (self.non_ext[options.field_name]) {
                // existing fields
                var group = $(source).parents('.tab-pane');
                var check_empty_group = group.find('table').hasClass('empty_container');
                var alignment;
                if ((group.hasClass('tab-pane') && check_empty_group)) {
                    self.tabArch(self.arch, res, "notebook");
                    if (res.length > 0) {
                        var notebook_pos = group.parents('.o_notebook').attr('notebook_id');
                        var index = $($('.o_notebook')[notebook_pos - 1]).find('li.active').index();
                        var tab_name = res[notebook_pos - 1].children[index].attrs.name;
                        alignment = $(source).parent().index() == 0 ? 'left' : 'right';
                        options.group_name = tab_name + "_" + alignment;
                        options.tag_operation = 'page';
                        options.pos = "inside";
                        misc.update_view(options);
                    }
                } else if (($(source).parents('.o_form_sheet').hasClass('o_form_sheet') &&
                        $(source).parent().hasClass('empty_container'))) {
                    self.tabArch(self.arch, res, "group");
                    if (res.length > 0) {
                        var source_index = $(source).parent().index();
                        options.group_name = res[source_index + 1].attrs.name;
                        options.tag_operation = 'page';
                        options.pos = "inside";
                        misc.update_view(options);
                    }
                } else {
                    misc.update_view(options);
                }
            } else {
                //new fields
                _.each(self.field_component_widget, function (prototype) {
                    if (prototype['label'] === options.field_name) {
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
                    }
                });
                $.when(def).then(function (values) {
                    options = _.extend(options, values);
                    misc.update_view(options);
                });
            }
        },

        tabArch: function (object, result, search_string) {
            if (object) {
                if (object.hasOwnProperty('tag') && object['tag'] === search_string) {
                    result.push(object);
                }
                for (var i = 0; i < Object.keys(object).length; i++) {
                    if (typeof object[Object.keys(object)[i]] == "object") {
                        self.tabArch(object[Object.keys(object)[i]], result, search_string);
                    }
                }
            }
        },

        table: function () {
            var row = document.createElement("tr");
            row.id = "temp";
            row.className = "app_builder-custom gu-transit";
            var cell = document.createElement("td");
            cell.appendChild(document.createTextNode('\u00A0'));
            var cell2 = document.createElement("td");
            cell2.appendChild(document.createTextNode('\u00A0'));
            row.appendChild(cell);
            row.appendChild(cell2);
            return row;
        },

        onShadow: function (el) {
            $("li[data-id='" + $(el).attr('data-id') + "']").animate({'opacity': '1'}, 200);
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
            self._on_focus('.app_builder-custom');
            if (this._shadow) {
                this._shadow.remove();
                this._shadow = null;
            }
        },

        get_default_value: function (name) {
            var options = {};
            options.view_id = self.view_id;
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

        setPropertyValue: function (elements) {
            if (elements.length > 0) {
                var string = elements[0].html().trim();
                var attrs = self.getFieldAttribute(string, 'string');
                self.p_visible.prop('checked', elements[0].hasClass('o_invisible_modifier'));
                console.log('===', attrs);
                if (attrs) {
                    self.p_required.prop('checked', attrs.required);
                    self.p_readonly.prop('checked',attrs.readonly);
                    self.get_default_value(attrs.name);
                    self.p_text.val(attrs.string);
                    self.p_tool_tip.val(attrs.help);
                    self.p_placeholder.val(attrs.placeholder);
                    if (attrs.type) {
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
                            placeholder: 'Form Widgets',
                            data: data,
                            multiple: false,
                            value: []
                        });
                    }
                    if (attrs.type === 'many2many') {
                        self.p_domain.parent().parent().show();
                        self.p_context.parent().parent().show();
                    } else {
                        self.p_domain.parent().parent().hide();
                        self.p_context.parent().parent().hide();
                    }
                } else {
                    self.p_tool_tip.val("");
                    self.p_placeholder.val("");
                    self.p_domain.val("");
                    self.p_context.val("");
                }
            }
        },

        getFieldAttribute: function (attr_value, attr_name) {
            var field_attrs = null, self = this;
            var res = [];
            this.tabArch(self.new_arch, res, "field");
            _.each(self.exist_fields_obj, function (object) {
                if (object[attr_name] === attr_value) {
                    field_attrs = object;
                }
            });
            if (field_attrs === null) {
                _.each(res, function (object) {
                    if (object.attrs.string === attr_value) {
                        field_attrs = self.getFieldAttribute(object.attrs.name, 'name');
                        field_attrs = $.extend({}, field_attrs, object.attrs);
                    }
                });
            }
            return field_attrs;
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
            var highlight = 'ui-selector-border';
            var currentElement = $(selector).click(function (e) {
                self.open_sidebar();
                var elements = [];
                $('#btn_rm_view').show();
                self.p_visible.parent().parent().show();
                self.p_required.parent().parent().show();
                self.p_readonly.parent().parent().show();
                self.p_tool_tip.parent().parent().show();
                self.p_placeholder.parent().parent().show();
                self.p_groups_id.parent().parent().show();
                self.p_widget_id.parent().parent().show();
                self.p_default.parent().parent().show();
                self.p_domain.parent().parent().show();
                self.p_context.parent().parent().show();
                currentElement.removeClass(highlight);
                $(this).addClass(highlight);
                selected_label = $(this).find('label').length > 0 ? $(this).find('label') : null;
                selected_tab = $(this).find('a[data-toggle="tab"]').length > 0 ? $(this).find('a') : null;
                if (selected_label !== null) {
                    elements.push(selected_label);
                }
                if (selected_tab !== null) {
                    elements.push(selected_tab);
                    self.p_visible.parent().parent().hide();
                    self.p_required.parent().parent().hide();
                    self.p_readonly.parent().parent().hide();
                    self.p_tool_tip.parent().parent().hide();
                    self.p_placeholder.parent().parent().hide();
                    self.p_groups_id.parent().parent().hide();
                    self.p_widget_id.parent().parent().hide();
                    self.p_default.parent().parent().hide();
                    self.p_domain.parent().parent().hide();
                    self.p_context.parent().parent().hide();
                }
                self.setPropertyValue(elements)
            });
            return currentElement;
        },
        open_sidebar: function () {
            misc.on_overlay_close();
            self.sidebar.css('width', '350px');
        },
        close_sidebar: function () {
            self.sidebar.css('width', '0');
        }
    });

    core.action_registry.add('app_builder_form_view', form_view);
});