flectra.define('web.action_view_editor', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var ActionViewEditorSidebar = require('web.ActionViewEditorSidebar');
    var ActionViewEditorCards = require('web.ActionViewEditorCards');
    var VIEW_TYPES = ['form', 'search', 'list', 'kanban', 'graph', 'pivot', 'calendar', 'gantt'];
    var VIEW_DESC = {
        'form': 'Form views are used to display the data from a single record.',
        'search': 'Search views are a break from previous view types in that they dont display content',
        'list': 'List views are used to display the data from a multiple record.',
        'kanban': 'The kanban view is a kanban board visualisation: it displays records as cards.',
        'graph': 'The graph view is used to visualize aggregations over a number of records or record groups.',
        'pivot': 'The pivot view is used to visualize aggregations as a pivot table.',
        'calendar': 'Calendar views display records as events in a daily, weekly or monthly calendar.',
        'gantt': 'Gantt views appropriately display Gantt charts (for scheduling).'
    };

    return Widget.extend({
        template: 'web.ActionViewEditor',
        events: '',

        init: function (parent, action, current_active_views, view_id) {
            this._super.apply(this, arguments);
            this.action = action;
            this.active_views = current_active_views;
            this.active_views.push('search');
            this.default_view = current_active_views[0];
            this.view_id = view_id;
        },

        start: function () {
            var self = this;
            var inactive_views = [], regulate_views;
            _.each(VIEW_TYPES, function (e) {
                if (!_.contains(self.active_views, e)) {
                    inactive_views.push(e);
                }
            });
            regulate_views = self.active_views.concat(inactive_views);
            _.each(regulate_views, function (e) {
                var cards = new ActionViewEditorCards(self, {
                    view_type: e,
                    view_desc: VIEW_DESC[e],
                    default_view: self.default_view,
                    disabled_views: inactive_views
                });
                if (_.contains(['form', 'search'], e)) {
                    cards.column = 'col-md-6';
                    cards.appendTo(self.$('div[data="general"]'));
                }
                else if (_.contains(['list', 'kanban', 'grid'], e)) {
                    cards.column = 'col-md-4';
                    cards.appendTo(self.$('div[data="multiple"]'));
                }
                else if (_.contains(['calendar', 'gantt'], e)) {
                    cards.column = 'col-md-6';
                    cards.appendTo(self.$('div[data="timeline"]'));
                }
                else if (_.contains(['graph', 'pivot'], e)) {
                    cards.column = 'col-md-4';
                    cards.appendTo(self.$('div[data="reporting"]'));
                }

            });

            this.action_view_editor_sidebar = new ActionViewEditorSidebar(this, this.action, this.view_id);
            this.action_view_editor_sidebar.appendTo(this.$el);
        }

    })

});