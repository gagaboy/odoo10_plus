flectra.define('web.ActionViewEditorSidebar', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var rpc = require('web.rpc');

    return Widget.extend({
        template: 'web.ActionViewEditorSidebar',
        events: {
            'change input,textarea': 'update_attrs'
        },

        init: function (parent, action, view_id) {
            this._super.apply(this, arguments);
            this.action = action;
            this.attrs = {
                name: action.display_name,
                help: action.help ? action.help.replace(/\n\s+/g, '\n') : ''
            };
            this.view_id = view_id;
        },

        start: function () {
            var self = this;
            self.$el.find('.group_m2m_select2').append($('<option/>', {}));
            var data = [];

            rpc.query({
                model: self.action.type,
                method: 'search_read',
                domain: [['id', '=', self.action.id]]
            }).then(function (resp) {
                self.$el.find('#groups_id').select2("val", resp[0].groups_id)
            });

            rpc.query({
                model: 'res.groups',
                method: 'search_read'
            }).then(function (resp) {
                _.each(resp, function (e) {
                    data.push({id: e.id, text: e.name})
                });
                self.$el.find('.group_m2m_select2').select2({
                    placeholder: 'Security Group Names',
                    data: data,
                    multiple: true
                });
            });

        },

        update_attrs: function (ev) {
            var $element = $(ev.currentTarget);
            var attr_name = $(ev.currentTarget).attr('id');
            var new_attrs = {};
            new_attrs[attr_name] = $element.val();
            this.trigger_up('update_attributes', new_attrs);
        },


    });

});