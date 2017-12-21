flectra.define('web.ActionViewEditorCards', function (require) {
    "use strict";

    var Widget = require('web.Widget');

    return Widget.extend({
        template: 'web.ActionViewEditorCards',
        events: {
            'click div.views-info': 'on_view_card_click'
        },

        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.view_type = options.view_type;
            this.view_desc = options.view_desc;
            this.default_view = options.default_view;
            this.disabled_views = options.disabled_views;
        },

        start: function () {
            var self = this;
            self.disable_view(self.disabled_views);
        },

        disable_view: function (views) {
            var self = this;
            _.each(views, function (e) {
                var v = self.$el.find('div[data-view=' + e + ']');
                v.addClass('disabled-view-card');
            });
        },

        on_view_card_click: function (ev) {
            if(!_.contains(this.disabled_views,this.view_type))
                this.trigger_up('open_view', {view_clicked: this.view_type});
            else
                this.trigger_up('activate_view',{view_clicked: this.view_type});
        }

    });

});