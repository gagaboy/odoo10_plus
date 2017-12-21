flectra.define('web.Miscellaneous', function (require) {
    "use strict";
    var ajax = require('web.ajax');
    var bus = require('builder.bus');
    var Dialog = require('web.Dialog');
    var data_manager = require('web.data_manager');
    var framework = require('web.framework');
    var session = require('web.session');
    var ir_action = require('web.ir_actions');
    var CDATA_WRAPPER = {
        "CDATA_FIELDS": [('ir.actions.server', 'code'), ('ir.model.fields', 'compute'), ('ir.rule', 'domain_force'), ('ir.actions.act_window', 'help'), ('ir.actions.server', 'help'), ('ir.model.fields', 'help')]
    };
    var SEQ_MODEL = {
        "SEQ_MODEL":
            ['res.groups', 'ir.model', 'ir.model.fields', 'ir.ui.view', 'ir.actions.act_window', 'ir.actions.report', 'mail.template', 'ir.actions.server', 'ir.ui.menu', 'ir.filters', 'base.automation', 'ir.model.access', 'ir.rule']
    };
    var XML_DB_FLDS = {"XML_FIELDS": [('ir.ui.view', 'arch')]};
    var WHITELIST_FILEDS = {
        'ir.filters': [
            'action_id', 'active', 'context', 'domain', 'is_default', 'model_id', 'name', 'sort'
        ],
        'ir.ui.menu': ['action', 'active', 'groups_id', 'name', 'parent_id', 'sequence', 'web_icon'],
        'ir.model': ['info', 'is_mail_thread', 'model', 'name', 'state', 'transient'],
        'ir.model.access': [
            'active', 'group_id', 'model_id', 'name', 'perm_create', 'perm_read', 'perm_unlink',
            'perm_write'
        ],
        'ir.model.fields': [
            'complete_name', 'compute', 'copy', 'depends', 'domain', 'field_description', 'groups',
            'help', 'index', 'model', 'model_id', 'name', 'on_delete', 'readonly', 'related',
            'relation', 'relation_field', 'required', 'selectable', 'selection',
            'size', 'state', 'store', 'track_visibility', 'translate',
            'ttype'
        ],
        'base.automation': [
            'action_server_id', 'active', 'filter_domain', 'filter_pre_domain',
            'last_run', 'on_change_fields', 'trg_date_id', 'trg_date_range',
            'trg_date_range_type', 'trigger'
        ],
        'ir.ui.view': [
            'active', 'arch', 'field_parent', 'groups_id', 'inherit_id', 'mode', 'model', 'name',
            'priority', 'type'
        ],
        'mail.template': [
            'auto_delete', 'body_html', 'copyvalue', 'email_cc', 'email_from', 'email_to', 'lang',
            'model_id', 'model_object_field', 'name', 'null_value', 'partner_to', 'ref_ir_act_window',
            'reply_to', 'report_name', 'report_template', 'scheduled_date', 'sub_model_object_field',
            'sub_object', 'subject', 'use_default_to', 'user_signature'
        ],
        'res.groups': ['color', 'comment', 'implied_ids', 'is_portal', 'name', 'share'],
        'ir.actions.act_window': [
            'auto_search', 'binding_model_id', 'binding_type', 'context', 'domain', 'filter',
            'groups_id', 'help', 'limit', 'multi', 'name', 'res_model', 'search_view_id', 'src_model',
            'target', 'type', 'usage', 'view_id', 'view_ids', 'view_mode', 'view_type'
        ],
        'ir.actions.report': [
            'attachment', 'attachment_use', 'binding_model_id', 'binding_type', 'groups_id', 'model',
            'multi', 'name', 'report_name', 'report_type'
        ],
        'ir.actions.server': [
            'binding_model_id', 'binding_type', 'child_ids', 'code', 'crud_model_id', 'help',
            'link_field_id', 'model_id', 'name', 'sequence', 'state'
        ],
        'ir.rule': [
            'active', 'domain_force', 'groups', 'model_id', 'name', 'perm_create', 'perm_read',
            'perm_unlink', 'perm_write'
        ],
    };
    var data = [];

    return {

        activate_new_view: function (action, new_view, view_mode) {
            var self = this;
            var def = $.Deferred();
            data_manager.invalidate();
            var attrs = {};
            if (new_view === 'calendar' || new_view === 'gantt') {
                attrs = {
                    'date_stop': 'write_date',
                    'date_start': 'create_date'
                };
            }
            ajax.jsonRpc('/web/activate_new_view', 'call', {
                action_type: action.type,
                action_id: action.id,
                model: action.res_model,
                view_t: new_view,
                view_mode: view_mode,
                options: attrs
            }).then(function (resp) {
                if (resp !== true) {
                    Dialog.alert(self, resp);
                    def.reject();
                } else {
                    self.refresh_action(action.id).then(def.resolve.bind(def));
                }

            });
            return def;
        },

        getBackgroundImage: function (files) {
            var def = $.Deferred();
            if (files) {
                var file = files[0];
                var fr = new FileReader();
                fr.onload = function () {
                    ajax.jsonRpc('/web/get_background', 'call', {
                        file_name: file.name,
                        base_64_data: fr.result.split('base64,')[1]
                    }).then(function (resp) {
                        def.resolve(resp);
                    });
                };
                fr.readAsDataURL(file);
            } else {
                def.resolve(false);
            }
            return def;
        },

        export_utility: function (app_data_ids) {
            framework.blockUI();
            _.each(app_data_ids, function (id) {
                data = [];
                data.push(SEQ_MODEL, WHITELIST_FILEDS, CDATA_WRAPPER, XML_DB_FLDS, id);
                session.get_file({
                    url: '/web/export_from_app_builder',
                    data: {data: JSON.stringify(data)},
                    complete: framework.unblockUI
                });
            });
        },

        create_new_app: function (data, files) {
            var self = this;
            return self.getBackgroundImage(files).then(function (attachment_id) {
                return ajax.jsonpRpc('/web/create_new_app', 'call', {
                    data: data,
                    attachment_id: attachment_id,
                    is_app: true,
                    group_id: self.rstring(6)
                }).fail(function (result, error) {
                    Dialog.alert(self, error + ' Failed to create app possibly model exists!');
                });
            });
        },

        getActions: function (action_name, model_name) {
            var def = $.Deferred();
            ajax.jsonRpc('/web/get_model', 'call', {
                model: model_name
            }).done(function (model) {
                if (action_name === 'reports')
                    def.resolve(ir_action.get_report_action(model));
                if (action_name === 'ac_controls')
                    def.resolve(ir_action.get_access_control_action(model));
                if (action_name === 'udf_filters')
                    def.resolve(ir_action.get_udf_filters_action(model));
                if (action_name === 'ac_autom')
                    def.resolve(ir_action.get_automation_action(model));
            });
            return def;
        },

        edit_view_attrs: function (action, attrs) {
            var self = this;
            var def = $.Deferred();
            data_manager.invalidate();
            ajax.jsonRpc('/web/set_update_action', 'call', {
                type: action.type,
                id: action.id,
                attrs: attrs
            }).then(function (resp) {
                if (resp !== true) {
                    Dialog.alert(self, resp);
                    def.reject();
                } else {
                    self.refresh_action(action.id).then(def.resolve.bind(def));
                }

            });
            return def;
        },

        new_report_create: function (model_name, template_name) {
            return ajax.jsonRpc('/web/create_report_from_xml', 'call', {
                db_model: model_name,
                xml: template_name,
                context: session.user_context,
            });
        },

        generate_report_action: function (old_report_config, new_report_config) {
            return ajax.jsonRpc('/web/generate_report_action', 'call', {
                id: old_report_config.res_id,
                config: new_report_config
            });
        },

        update_view: function (options) {
            var self = this;
            framework.blockUI();
            ajax.jsonRpc('/web/update_view', 'call', {
                options: options
            }).done(function (resp) {
                data_manager.invalidate();
                framework.unblockUI();
                bus.trigger('arch_updated', resp);
            }).fail(function (resp) {
                Dialog.alert(self, "Failed To Update View " + resp);
            });
        },

        update_list_view: function (options) {
            ajax.jsonRpc('/web/update_list_view', 'call', {
                options: options
            }).done(function (resp) {
                data_manager.invalidate();
                bus.trigger('arch_updated', resp);
            });
        },

        check_obj_name: function (name, $target) {
            var self = this;
            return ajax.jsonRpc('/web/check_obj_name', 'call', {
                model_name: name
            }).then(function (has_obj) {
                if (has_obj) {
                    $target.attr('has_model', 0)
                } else {
                    $target.attr('has_model', 1);
                }
            });
        },

        update_search_view: function (options) {
            ajax.jsonRpc('/web/update_search_view', 'call', {
                options: options
            }).done(function (resp) {
                data_manager.invalidate();
                bus.trigger('arch_updated', resp);
            });
        },

        set_or_get_default_value: function (options) {
            var response = ajax.jsonRpc('/web/default_value', 'call', {
                options: options
            });
            if (options['op'] === 'set') {
                response.done(function (resp) {
                    data_manager.invalidate();
                    bus.trigger('arch_updated', resp);
                });
            } else {
                return response;
            }
        },

        refresh_action: function (id) {
            return data_manager.load_action(id).then(function (new_action) {
                bus.trigger('action_changed', new_action);
                return new_action;
            });
        },

        rstring: function (size) {
            var text = "";
            var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
            for (var i = 0; i < size; i++)
                text += possible.charAt(Math.floor(Math.random() * possible.length));
            return text;
        },

        on_overlay_open: function (ev) {
            var self = ev.data;
            if ($('.drawer_is_open').length) {
                self.on_overlay_close();
                $('.drawer_is_open').removeClass('drawer_is_open');
                return;
            }
            var $target = $(ev.currentTarget);
            $target.addClass('drawer_is_open');
            $("#submenu_overlay").css({"height": "70px"});
            $("#submenu_overlay").css({"width": "55.86%"});
            $("#top-nav").css({"marginTop": "70px"});
            $(".o_main_content").stop().animate({marginTop: "80px"});
        },

        on_overlay_close: function () {
            $("#submenu_overlay").css({"height": "0"});
            $("#submenu_overlay").css({"width": "55.86%"});
            $("#top-nav").css({"marginTop": "0"});
            $(".o_main_content").stop().animate({marginTop: "0px"});
        }
    };
});