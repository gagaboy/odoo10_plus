flectra.define('qc.dashboard', function (require) {
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

var QCTeamDashboardRenderer = KanbanRenderer.extend({
    events: _.extend({}, KanbanRenderer.prototype.events, {
        'click .o_dashboard_action': '_onDashboardActionClicked',
    }),

     _render: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            var values = self.state.dashboardValues;
            var qc_dashboard = QWeb.render('quality_assurance_management
            .QCTeamDashboard', {
                widget: self,
                show_demo: values.show_demo,
                values: values,
            });
            self.$el.prepend(qc_dashboard);
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

var QCDashboardModel = KanbanModel.extend({

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
            model: 'qc.team',
            method: 'get_team_dashboard_datas',
        });
        return $.when(super_def, dashboard_def).then(function(id, dashboardValues) {
            self.dashboardValues[id] = dashboardValues;
            return id;
        });
    },
});

var QCDashboardController = KanbanController.extend({
    custom_events: _.extend({}, KanbanController.prototype.custom_events, {
        dashboard_open_action: '_onDashboardOpenAction',
    }),

    _onDashboardOpenAction: function (e) {
        var self = this;
        var action_name = e.data.action_name;
        return this.do_action(action_name);
    },
});

var QCDashboardView = KanbanView.extend({
    config: _.extend({}, KanbanView.prototype.config, {
        Model: QCDashboardModel,
        Renderer: QCDashboardRenderer,
        Controller: QCDashboardController,
    }),
    display_name: _lt('Dashboard'),
    icon: 'fa-dashboard',
    searchview_hidden: true,
});

view_registry.add('qc_dashboard', QCDashboardView);

return {
    Model: QCDashboardModel,
    Renderer: QCDashboardRenderer,
    Controller: QCDashboardController,
};

});