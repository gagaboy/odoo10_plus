flectra.define('web.AppExportDialog', function (require) {
    "use strict";
    var Dialog = require('web.Dialog');
    var rpc = require('web.rpc');
    var framework = require('web.framework');

    return Dialog.extend({
        template: 'web.module_maker_app_list',

        init: function (parent) {
            var options = {
                title: 'Select Apps To Export.',
                size: 'medium',
                buttons: [
                    {
                        text: "Export",
                        classes: 'btn-success',
                        click: _.bind(this.on_export, this)
                    },
                    {text: "Cancel", classes: 'btn-danger', close: true}
                ]
            };
            this._super(parent, options);
        },
        start: function () {
            var self = this;
            var app_data_id = [];
            self.$el.removeClass('container');
            self.$el.attr('style', 'padding-left:0;padding-right:0');
            self.$el.parent().removeClass('container');
            rpc.query({
                model: 'ir.model.data',
                method: 'search_read',
                args: [[['is_app_builder', '=', true], ['model', '=', 'ir.ui.menu']],
                    ['id', 'model', 'name', 'res_id', 'app_data_id']
                ]
            }).then(function (resp) {
                if (resp.length) {
                    framework.blockUI();
                    _.each(resp, function (e) {
                        app_data_id.push(e);
                        rpc.query({
                            model: e.model,
                            method: 'search_read',
                            args: [[['id', '=', e.res_id]],
                                ['id', 'name', 'web_icon', 'web_icon_data']
                            ]
                        }).then(function (resp2) {
                            _.each(resp2, function (e2) {
                                _.each(app_data_id, function (data) {
                                    if (data.res_id === e2.id) {
                                        var $tr = $('<tr>').attr('record-id', data.app_data_id[0]);
                                        if (e2.web_icon) {
                                            var web_icon = e2.web_icon.split(',');

                                            $tr.append($('<td>').append('<div class="cbox">' +
                                                '<input type="checkbox">' +
                                                '</div>'));
                                            $tr.append($('<td>').append('<div class="app_text">'
                                                + e2.name + '</div>'));

                                            $tr.append($('<td>').append($('<div class="image"/>')
                                                .append('<i class="material-icons">' + web_icon[2] + '</i>')
                                                .attr('style', 'color:' + web_icon[0] + ';background:' + web_icon[1])
                                            ));


                                            $('.flectra_app_list').append($tr);
                                        }
                                        if (e2.web_icon_data) {

                                            $tr.append($('<td>').append('<div class="cbox">' +
                                                '<input type="checkbox">' +
                                                '</div>'));

                                            $tr.append($('<td>').append('<div class="app_text">'
                                                + e2.name + '</div>'));

                                            $tr.append($('<td>').append($('<div class="image"/>')
                                                .css({
                                                    "background": 'url(data:image/png;base64,' + e2.web_icon_data + ')',
                                                    "background-repeat": "no-repeat",
                                                    "background-position": "center center",
                                                    "background-size": "cover"
                                                })
                                            ));


                                            $('.flectra_app_list').append($tr);
                                        }
                                    }
                                });
                            });
                            framework.unblockUI();
                        });
                    });
                } else {
                    self.close();
                    Dialog.alert(this, 'Nothing To Export');
                    return 0;
                }
            });
        },

        on_export: function () {
            var self = this;
            var cbox = $('.cbox input:checked');
            var record_set = [];
            _.each(cbox, function (el) {
                var id = $(el).parent().parent().parent().attr('record-id');
                record_set.push(id);
            });
            self.trigger('on_export', record_set);
            self.close();
        }
    });
});