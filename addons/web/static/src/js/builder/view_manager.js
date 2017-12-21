flectra.define('builder.ViewManager', function (require) {
    "use strict";
    var ViewManager = require('web.ViewManager');
    var ActionManager = require('web.ActionManager');
    var ActionRelation = require('web.ActionRelation');
    ViewManager.include({
        init: function () {
            this._super.apply(this, arguments);
            this.manager = new ActionManager();
            this.relation = new ActionRelation(this);
        },

        update_control_panel: function () {
            var active_view_obj;
            var self = this;
            setTimeout(function () {
                if (self.action_manager !== undefined) {
                    active_view_obj = self.active_view;
                    var updated_history = self.manager._update_action_history('active_view', active_view_obj);
                    self.relation._set_active_view(updated_history);
                    var l = window.location;
                    if (l.search.indexOf('app_builder=main') !== -1) {
                        self.relation.action_app_builder_mode();
                    }
                    else if (l.search.indexOf('app_builder=app_creator') !== -1) {
                        self.relation.app_creator_mode();
                    }
                }
            }, 1);
            return this._super.apply(this, arguments);
        }
    });
});