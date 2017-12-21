flectra.define('web.Main', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var ActionManager = require('web.ActionManager');
    var ActionViewEditor = require('web.action_view_editor');
    var ActionRelation = require('web.ActionRelation');
    var Misc = require('web.Miscellaneous');
    var _action = new ActionManager();

    var Main = Widget.extend({
        className: 'web_main',
        custom_events: {
            'open_view': 'open_view',
            'activate_view': 'add_new_view',
            'update_attributes': 'update_action_attr'
        },

        init: function (parent, context, options) {
            this.action = options.action;
            this.active_view = options.active_view || options.active_view_object.active_view;
            this.res_id = this.action.res_id ? this.action.res_id : 1;
            this.relation = new ActionRelation();
            this.view_redirect = options.view_redirect;
            this._super.apply(this, arguments);
        },


        start: function () {
            var def, self = this;
            if (!self.view_redirect) {
                self.action_history = _action._get_last_action();
                self.action_history.options.no_update_state = true;
                self.active_view = self.action_history.options.active_view;
                self.action_history.options.view_type = self.active_view.type || self.active_view;
                def = self.do_action(self.action,
                    self.action_history.options);
            }
            else {
                var view_id = self.active_view.view_id;
                var current_view_types = self.action.view_mode.split(',');
                self.action_view_editor = new ActionViewEditor(self, self.action, current_view_types,
                    view_id);
                def = self.action_view_editor.prependTo(self.$el);
            }
            return $.when(def, this._super.apply(this, arguments));
        },

        open_view: function (ev) {
            var self = this;
            var data = ev.data;
            var target = self.action;
            self.action_history = _action._get_last_action();
            self.action_history.options.view_type = data.view_clicked;
            target.view_clicked = data.view_clicked;
            self.action_history.options.no_update_state = false;
            target.res_id = target.res_id ? target.res_id : self.res_id;
            self.do_action(target, self.action_history.options);
        },

        add_new_view: function (ev) {
            var self = this;
            var new_view = ev.data.view_clicked;
            var view_mode = self.action.view_mode + ',' + new_view;
            Misc.activate_new_view(self.action, new_view, view_mode).then(function (resp) {
                self.do_action('action_web_main', {
                    action: resp,
                    active_view: new_view,
                    view_redirect: false,
                });
            });
        },

        update_action_attr: function (ev) {
            var self = this;
            if (ev.data) {
                Misc.edit_view_attrs(self.action, ev.data).then(function (resp) {
                    self.action = resp;
                });
            }
        },

        do_action: function (action, options) {
            return this._super.apply(this, arguments).done(function () {
                Misc.on_overlay_close();
            });
        }
    });

    core.action_registry.add('action_web_main', Main);

});
