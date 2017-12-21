flectra.define('web.ModuleMakerUtils', function (require) {
    "use strict";

    var misc = require('web.Miscellaneous');
    var Widget = require('web.Widget');
    var AppExportDialog = require('web.AppExportDialog');
    var rpc = require('web.rpc');
    return Widget.extend({
        template: 'web.ModuleMakerUtility',

        events: {
            'click li > a': 'onMenuItemClick',
            'change .bg_upload': 'onFileSelect'
        },

        init: function (parent) {
            this._super.apply(this, arguments);
        },

        start:function () {
            var self = this;
            rpc.query({
                model: 'ir.module.module',
                method: 'search_read',
                args: [[['name', '=', 'base_import_module']],
                    ['id', 'name', 'state']
                ]
            }).then(function (resp) {
                self.state = resp[0]['state'];
                if(self.state !== 'installed')
                    self.$el.find('#app_builder_import').hide();
            })
        },

        onMenuItemClick: function (e) {
            e.preventDefault();
            var self = this;
            var $target = $(e.currentTarget);
            var id = $target.first().attr('id');

            if (id === 'app_builder_export') {
                var dialog = new AppExportDialog(self).open();
                dialog.on('on_export', self, function (values) {
                    misc.export_utility(values);
                });
            }
            if (id === 'app_builder_import') {
                self.do_action({
                    name: 'Import modules',
                    res_model: 'base.import.module',
                    views: [[false, 'form']],
                    type: 'ir.actions.act_window',
                    target: 'new'
                }, {
                    on_close: function () {
                        self.redo_menu()
                    }
                });
            }
        },

        redo_menu: function () {
            //@TODO can't find any other way to reload menu.
            window.location.reload();
        }
    })
});

