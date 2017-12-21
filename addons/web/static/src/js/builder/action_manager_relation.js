flectra.define('web.ActionRelation', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var ActionManager = require('web.ActionManager');
    var data = require('web.data');
    var data_manager = require('web.data_manager');
    var bus = require('builder.bus');
    var drag_manager_gantt = require('web.UIDragManagerGantt');
    var misc = require('web.Miscellaneous');
    var fields_manager = require('web.FieldsManager');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;
    var flag = false;
    var o_navbar;

    var Mediator = Widget.extend({
        init: function (parent, context, options) {
            this._super.apply(this, arguments);
            this._active_view = null;
            this._action = new ActionManager();
            this.parent = parent;
            var act = this._action._get_last_action();
            if (act.options !== undefined) {
                this.current_action = act.options.action;
                this.action_manager = act.options.action_manager;
                this.current_view = act.active_view === undefined ? act.options.active_view_object : act;
            }
            this.dragula_gantt = new drag_manager_gantt();
            bus.on('action_changed', this, this.action_updater.bind(this));
        },

        action_updater: function (new_action) {
            this.current_action = new_action;
        },

        action_app_builder_mode: function () {
            if (this.current_action.is_auto_load) {
                flag = false;
                this.destroy();
            }
            if (!flag) {
                var _action_manager = this._action._get_last_action();
                flag = true;
                _action_manager.active_view === undefined ? _action_manager.active_view = this.current_view.active_view : undefined;
                if ('action_obj' in _action_manager.options) {
                    _action_manager.options.action = _action_manager.options.action_obj.options.action;
                }
                this.infiltrate_sidebar(_action_manager);
            }
        },

        infiltrate_sidebar: function (_action_obj) {
            var self = this;
            var dataset = new data.DataSetSearch(self, self.current_action.res_model,
                self.current_action.context, self.current_action.domain);
            var options = {};
            var searchview_id = self.current_action.search_view_id && self.current_action.search_view_id[0];
            options.load_filters = true;
            self.views = self.current_action.views.slice();
            self.views.push([searchview_id || false, 'search']);
            self.view_type = _action_obj.active_view.type;

            var params = {
                model: dataset.model,
                context: dataset.get_context(),
                views_descr: self.views
            };
            data_manager.load_views(params, options).then(function (fields_views) {
                self.fields_views = fields_views[self.view_type];
                self.search_view_fields = fields_views[self.current_action.view_clicked];
                self.fields = self.fields_views.fieldsInfo[self.view_type];
                var fields_not_in_view;
                if (!self.search_view_fields) {
                    fields_not_in_view = _.omit(self.fields_views.fields, Object.keys(self.fields));
                }
                else {
                    fields_not_in_view = _.omit(self.search_view_fields.fields, Object.keys(self.fields));
                }
                self.on_app_builder_open("", fields_not_in_view, _action_obj);
            });
        },

        _set_active_view: function (view) {
            this._active_view = view;
        },

        render_template: function (t_name, obj_dict) {
            return QWeb.render('web.' + t_name, obj_dict);
        },

        sort_field_asc: function (object) {
            var keys = Object.keys(object);
            var i, len = keys.length;
            keys.sort();
            var sorted_object = {};
            for (i = 0; i < len; i++) {
                var k = keys[i];
                var obj = {};
                obj[k] = object[k];
                _.extend(sorted_object, obj);
            }
            return sorted_object;
        },

        on_app_builder_open: function (existing_fields, fields_not_in_view, action_obj) {
            var self = this;
            var field_widget = fields_manager['new_fields'];
            var prototype = [];
            _.each(field_widget, function (widget) {
                prototype.push({
                    'label': new widget(self).__proto__.label,
                    'type': new widget(self).__proto__.ttype
                });
            });

            prototype = prototype.sort(function (a, b) {
                return a.label.localeCompare(b.label);
            });

            var sorted_fields_not_in_view = self.sort_field_asc(fields_not_in_view);
            if (!self.current_action.is_auto_load) {
                var sidebar = self.render_template('sideBar', {
                    data: sorted_fields_not_in_view,
                    new_fields: prototype
                });
            }
            self.open_sideBar(sidebar);

            /*Register Drag and Drop*/

            if (self.view_type === "form") {
                var drag_drop_container_form =
                    [document.querySelector('.web_sidebar_field_container ul#new'),
                        document.querySelector('.web_sidebar_field_container ul#existing')]
                        .concat(Array.from(document.querySelectorAll("tbody")));

                self.action_manager.do_action('app_builder_form_view', {
                    no_update_state: true,
                    dragula_container: drag_drop_container_form,
                    action_obj: action_obj,
                    fields_not_in_view: fields_not_in_view,
                    prototype: prototype
                });
            }

            if (self.view_type === "list") {
                var drag_drop_container_list =
                    [document.querySelector('.web_sidebar_field_container ul#new'),
                        document.querySelector('.web_sidebar_field_container ul#existing')]
                        .concat(Array.from(document.querySelectorAll("td.web_td")));

                self.action_manager.do_action('app_builder_list_view', {
                    no_update_state: true,
                    dragula_container: drag_drop_container_list,
                    action_obj: action_obj,
                    fields_not_in_view: fields_not_in_view,
                    prototype: prototype
                });
            }

            if (self.view_type === "calendar") {
                self.action_manager.do_action('app_builder_calendar_view', {
                    no_update_state: true,
                    fields_view: self.fields_views.fields,
                    action_obj: action_obj,
                    fields_not_in_view: fields_not_in_view,
                    prototype: prototype
                });
            }

            if (self.view_type === "pivot") {
                self.action_manager.do_action('app_builder_pivot_view', {
                    no_update_state: true,
                    action_obj: action_obj,
                    fields_not_in_view: fields_not_in_view
                });
            }

            if (self.view_type === "gantt") {
                self.dragula_gantt.initDragula(null, true, action_obj,
                    self.fields_views.fields, fields_not_in_view, prototype);
            }

            if (self.view_type === "graph") {
                self.remove_sidebar();
                self.action_manager
                    .do_notify('Not Editable!!', 'Nothing To Edit In Graph View!');
            }

            if (self.current_action.view_clicked === "search") {
                self.action_manager.do_action('app_builder_search_view', {
                    no_update_state: true,
                    fields_view: self.search_view_fields,
                    fields_not_in_view: fields_not_in_view,
                    action_obj: action_obj
                });
            }
            else if (self.view_type === "kanban") {
                var drag_drop_container_kanban =
                    [document.querySelector('.web_sidebar_field_container ul#new'),
                        document.querySelector('.web_sidebar_field_container ul#existing')]
                        .concat(Array.from(document.querySelectorAll("span.web_span")));
                self.action_manager.do_action('app_builder_kanban_view', {
                    no_update_state: true,
                    dragula_container: drag_drop_container_kanban,
                    action_obj: action_obj,
                    fields_not_in_view: fields_not_in_view,
                    prototype: prototype
                });
            }
            var is_filters = self.is_filters_available();
            $("#top-nav").off('click').on('click', misc, misc.on_overlay_open);

            $('.submenu > li > a').off('click').on('click', self.on_menu_click);

            self.render_breadcrumbs('views', true);

            $(".submenu > li").mouseenter(function () {
                if ($(this).hasClass('magic-color')) {
                    return;
                }
                var width = $(this).width();
                var current_offset = $(this).offset().left;
                var parent_offset = $(this).parent().parent().offset().left;
                var left = current_offset - parent_offset;
                var div_offset = (current_offset - $(this).parent().children().first().offset().left);

                $('.magic-color').stop().animate({
                    width: width,
                    left: div_offset,
                    opacity: 1,
                    backgroundColor: '#141f36'
                }, 250);

                $('#line-top,#line-bottom').stop()
                    .animate({
                        width: width,
                        left: left,
                        opacity: 1,
                        overflow: "hidden"
                    }, 250);
            });
        },
        is_filters_available: function () {
            var self = this;
            rpc.query({
                model: 'ir.module.module',
                method: 'search_read',
                args: [[['name', '=', 'base_automation']],
                    ['id', 'name', 'state']
                ]
            }).then(function (resp) {
                self.state = resp[0]['state'];
                if (self.state !== 'installed')
                    $('.submenu').find('a[data-name=ac_autom]').hide();
            });
        },
        render_breadcrumbs: function (menu, is_view) {
            var $breadcrumb = $('.app_builder_breadcrumbs');
            $breadcrumb.empty();
            var arr = [];
            arr.push($('<li>').append($('<a>').text(menu)));
            if (this.view_type && is_view) {
                arr.push($('<li>').append($('<a>').text(this.view_type)));
            }
            _.each(arr, function (e) {
                $breadcrumb.append(e);
            });
        },

        on_menu_click: function (ev) {
            var self = this;
            var $menu = $(ev.currentTarget);
            var name = $menu.data('name');
            var is_view = false;
            var model = self.current_action.res_model;
            if ($.inArray(name, ['reports', 'ac_controls', 'udf_filters', 'ac_autom']) !== -1) {
                misc.getActions(name, model).then(function (resp) {
                    self.action_manager.do_action(resp, {
                        clear_breadcrumbs: true,
                        no_update_state: true
                    });
                    self.pageElements().control_panel.show();
                });
                flag = true;
            } else {
                self.current_action.is_auto_load = false;
                self.action_manager.do_action('action_web_main', {
                    action: self.current_action,
                    active_view_object: self._active_view,
                    res_id: self.current_action.res_id,
                    no_update_state: true,
                    clear_breadcrumbs: true,
                    view_redirect: true
                });
                flag = false;
            }
            self.remove_sidebar();
            self.render_breadcrumbs($menu.text(), is_view);
        },

        pageElements: function () {
            return {
                'main': $('.o_main'),
                'sub_menu': $('.f_launcher'),
                'o_navbar': $('.navbar-collapse'),
                'control_panel': $('.o_control_panel')
            };
        },

        open_sideBar: function (sidebar) {
            var sub_menu = this.pageElements().sub_menu;
            sub_menu.before(sidebar);
            o_navbar = this.pageElements().o_navbar;
            o_navbar.remove();
            this.pageElements().main.find('#web_container').animate({'width': '280px'}, 300);
            sub_menu.hide();
            this.pageElements().control_panel.hide();
            this.register_close_button();
        },

        register_close_button: function () {
            var self = this;
            var $nav = $('nav');
            var navbar = QWeb.render('web.view_navbar', {});
            $nav.removeAttr('id');
            $nav.find('.f_toggle_buttons').remove();
            $nav.find('.f_menu_systray').remove();
            $nav.find('#top-nav').remove();
            $nav.find('#submenu_overlay').remove();
            $nav.append(navbar);
            $('.o_main_navbar').remove();
            $(document.body).on('click', 'button[data-action="close_view"]', function (e) {
                self.close_sideBar();
                bus.trigger('action_reload  ', false, 'home');
            });
            $(document.body).off('click', 'button[data-action="mk_app_view"]')
                .on('click', 'button[data-action="mk_app_view"]', function (e) {
                    misc.on_overlay_close();
                    self.app_creator_mode();
                });
        },

        app_creator_mode: function () {
            var self = this;
            self.action_manager.do_action('action_web_app_creator', {
                clear_breadcrumbs: true,
                no_update_state: true
            });
            self.close_sideBar();
            bus.trigger('app_builder_toggled', 'app_creator');
        },

        remove_sidebar: function () {
            var main = this.pageElements().main;
            main.find('#web_container').animate({'width': '0px'}, 300).remove();
        },

        close_sideBar: function () {
            this.remove_sidebar();
            $('#oe_main').append(o_navbar);
            flag = false;
        }
    });
    return Mediator;
});
