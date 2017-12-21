flectra.define('web.app_builder_report_kanban', function (require) {
    "use strict";

    var view_registry = require('web.view_registry');
    var AddReportDialog = require('web.kanban_report_dialog');
    var KanbanController = require('web.KanbanController');
    var KanbanView = require('web.KanbanView');


    var AppBuilderReportKanbanController = KanbanController.extend({
        _onButtonNew: function () {
            var model = this.initialState.context.search_default_model;
            new AddReportDialog(this, model).open();
        },

        _onOpenRecord: function (ev) {
            ev.stopPropagation();
            var self = this;
            var id = ev.target.id || ev.data.id;
            this._rpc({
                model: 'ir.actions.report',
                method: 'report_edit_data',
                args: [id]
            }).then(function (resp) {
                var action = _.extend(self.__parentedParent.action, resp);
                self.do_action(action, {
                    no_update_state: true
                });
            });
        }
    });

    var AppBuilderKanbanReports = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: AppBuilderReportKanbanController
        })
    });

    view_registry.add('app_builder_report_kanban', AppBuilderKanbanReports);
    return AppBuilderKanbanReports;
});