flectra.define('web.FieldCreatorDialog', function (require) {
    "use strict";
    var Dialog = require('web.Dialog');
    var rpc = require('web.rpc');

    return Dialog.extend({
        init: function (parent, model, ttype, fields) {
            this.model = model;
            this.ttype = ttype;
            this.fields = fields;
            var options = {
                title: 'Add a field',
                size: 'small',
                buttons: [
                    {
                        text: "save",
                        classes: 'btn-success',
                        click: _.bind(this.store_reserve, this)
                    },
                    {text: "Cancel", classes: 'btn-danger', close: true}
                ]
            };
            this._super(parent, options);
        },
        start: function () {
            var self = this;
            var data = [];
            if (self.ttype === 'selection') {
                self.$el.append($('<label>').text('Enter Selection Items')
                    .append($('<textarea ' +
                        'id="selection_field_id" ' +
                        'rows="5" cols="35" ' +
                        'placeholder="Key1,Value1\nKey2,Value2\n">')
                    ));
            }
            else if (self.ttype === 'many2many' || self.ttype === 'many2one') {
                self.$el.append($('<input id="select2_m2m_m2o" class="select2-full-width">'));
                rpc.query({
                    model: 'ir.model',
                    method: 'search_read',
                    domain: [['state', '=', 'base'], ['transient', '=', false]]
                }).then(function (resp) {
                    _.each(resp, function (e) {
                        data.push({
                            id: e.id,
                            text: e.display_name,
                            field_name: e.name
                        })
                    });
                    $('#select2_m2m_m2o').select2({
                        placeholder: 'Relational fields',
                        data: data,
                        multiple: false,
                        value: []
                    });
                });

            }
            else if (self.ttype === 'one2many') {
                self.$el.append($('<input id="select2_o2m" class="select2-full-width">'));
                rpc.query({
                    model: 'ir.model.fields',
                    method: 'search_read',
                    domain: [['model', '=', self.model], ['ttype', '=', 'many2one']]
                }).then(function (resp) {
                    _.each(resp, function (e) {
                        data.push({
                            id: e.id,
                            text: e.field_description,
                            field_name: e.name
                        })
                    });
                    $('#select2_o2m').select2({
                        placeholder: 'Relational fields',
                        data: data,
                        multiple: false,
                        value: []
                    });
                });
            }
        },
        store_reserve: function () {
            var self = this;
            var values = {};
            if (this.ttype === 'selection') {
                values.selection = _.map(self.$el.find('#selection_field_id').val()
                    .split("\n"), function (value) {
                    if (value) {
                        return [value.trim().split(',')[0], value.trim().split(',')[1]]
                    }
                });
            }
            else if (this.ttype === 'many2many' || this.ttype === 'many2one') {
                var selected_data = self.$el.find('#select2_m2m_m2o').select2('data');
                values.rel_id = selected_data.id;
                values.field_description = selected_data.field_name;
            }
            else if (this.ttype === 'one2many') {
                var data = self.$el.find('#select2_o2m').select2('data');
                values.rel_id = data.id;
                values.field_description = data.field_name;
            }
            this.trigger('save_field', values);
        }

    });

});