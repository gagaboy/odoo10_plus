flectra.define('support_desk.dashboard', function (require) {
"use strict";

var core = require('web.core');
var KanbanController = require('web.KanbanController');
var KanbanModel = require('web.KanbanModel');
var KanbanRenderer = require('web.KanbanRenderer');
var KanbanView = require('web.KanbanView');
var view_registry = require('web.view_registry');

var QWeb = core.qweb;

var _t = core._t;
var _lt = core._lt;

var supportdeskDashboardRenderer = KanbanRenderer.extend({
    events: _.extend({}, KanbanRenderer.prototype.events, {
        'click .o_dashboard_action': '_onDashboardActionClicked',
    }),

     _render: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            var values = self.state.dashboardValues;
            var support_desk_dashboard = QWeb.render('support_desk.supportdeskTeamDashboard', {
                widget: self,
                show_demo: values.show_demo,
                values: values,
            });
            self.$el.prepend(support_desk_dashboard);
        });
    },
    _onDashboardActionClicked: function (e) {
        e.preventDefault();
        var $action = $(e.currentTarget);
        this.trigger_up('dashboard_open_action', {
            action_name: $action.attr('name'),
        });
    },
});

var supportdeskDashboardModel = KanbanModel.extend({

    init: function () {
        this.dashboardValues = {};
        this._super.apply(this, arguments);
    },

    get: function (localID) {
        var result = this._super.apply(this, arguments);
        result.dashboardValues = this.dashboardValues[localID];
        return result;
    },

    load: function () {
        return this._loadDashboard(this._super.apply(this, arguments));
    },

    reload: function () {
        return this._loadDashboard(this._super.apply(this, arguments));
    },

    _loadDashboard: function (super_def) {
        var self = this;
        var dashboard_def = this._rpc({
            model: 'supportdesk.team',
            method: 'get_data_for_dashboard',
        });
        return $.when(super_def, dashboard_def).then(function(id, dashboardValues) {
            self.dashboardValues[id] = dashboardValues;
            return id;
        });
    },
});

var supportdeskDashboardController = KanbanController.extend({
    custom_events: _.extend({}, KanbanController.prototype.custom_events, {
        dashboard_open_action: '_onDashboardOpenAction',
    }),

    _onDashboardOpenAction: function (e) {
        var self = this;
        var action_name = e.data.action_name;
        return this.do_action(action_name);
    },
});

var supportdeskDashboardView = KanbanView.extend({
    config: _.extend({}, KanbanView.prototype.config, {
        Model: supportdeskDashboardModel,
        Renderer: supportdeskDashboardRenderer,
        Controller: supportdeskDashboardController,
    }),
    display_name: _lt('Dashboard'),
    icon: 'fa-dashboard',
    searchview_hidden: true,
});

view_registry.add('support_desk_dashboard', supportdeskDashboardView);

return {
    Model: supportdeskDashboardModel,
    Renderer: supportdeskDashboardRenderer,
    Controller: supportdeskDashboardController,
};

});
