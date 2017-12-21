flectra.define('web.AddButtonDialog', function (require) {
    "use strict";
    var Dialog = require('web.Dialog');
    var rpc = require('web.rpc');
    var FA_ICONS = [];
    var items_per_pages = 54;
    return Dialog.extend({
        init: function (parent) {
            this.model = parent.model;
            this.active = 1;
            var options = {
                title: 'Add A Button',
                size: 'medium',
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
            var self = this, data = [], fields = [];
            FA_ICONS = [];
            var icons = $.getJSON("/web/static/lib/fontawesome/fa_icons.json", function (d) {
                $.each(d, function (key, val) {
                    data.push('fa ' + key);
                });
                FA_ICONS = data;
            });

            self.$el.append($('<div class="col-md-12 mt8">').append($('<label>').text('Button Label')).append($('<input ' +
                'id="input_text_field_id" ' +
                'placeholder="Button Text">').attr('class', 'col-md-12')
            ));

            icons.then(function (items) {
                var counter = 0;
                var page = 1;
                var total_items = FA_ICONS.length;

                var el = self.$el.append($('<div class="col-md-12 mt8">')
                    .append($('<label>').text('Icons'))
                    .append($('<label>').attr('class', 'pull-right current_page').text('Page : ' + self.active))
                    .append($('<div id="icon_container">').addClass('col-md-10 col-md-offset-1')));

                _.each(FA_ICONS, function (e, i) {
                    counter++;
                    var fa_icon = $('<div data-value="' + e + '">')
                        .attr('class', 'col-sm-2 btn-icon  icon_btn_chooser')
                        .append($('<i class="' + e + '">'));
                    var $ipage = $('<div>').attr('class', 'icon_page' + page);
                    var $ilist = $ipage.append(fa_icon);
                    el.find('#icon_container').append($ilist);
                    if (counter === items_per_pages) {
                        counter = 0;
                        page++;
                    }
                });
                self.$el.append($('<button>').attr('class', 'btn btn-primary prev pull-left').text('<'));
                self.$el.append($('<button>').attr('class', 'btn btn-primary next pull-right').text('>'));
                self.$el.append($('<div class="col-md-12 mt8">').append($('<label>').text('Relation')).append($('<input ' +
                    'id="input_relation_field_m2o" >').attr('class', 'col-md-12')
                ));

                rpc.query({
                    model: 'ir.model.fields',
                    method: 'search_read',
                    domain: [['relation', '=', self.model], ['ttype', '=', 'many2one'], ['store', '=', true]]
                }).then(function (resp) {
                    _.each(resp, function (e) {
                        fields.push({
                            id: e.id,
                            text: e.field_description,
                            field_name: e.name
                        })
                    });
                    $('#input_relation_field_m2o').select2({
                        placeholder: 'Relational fields',
                        data: fields,
                        multiple: false,
                        value: []
                    });
                });
                self.hide_page(1);
                self.$el.find('.icon_page1').attr('active_page', '1');
                self.$el.find('.btn-icon').bind('click', self.on_icon_click);
                self.$el.find('button.next.pull-right').bind('click', self.on_next);
                self.$el.find('button.prev.pull-left').bind('click', self.on_prev);
            });

        },
        hide_page: function (active) {
            var self = this;
            for (var j = 1; j <= 13; j++) {
                if (j !== self.active)
                    self.$el.find('.icon_page' + j).hide();
                else
                    self.$el.find('.icon_page' + j).show();
            }
        },
        on_next: function () {
            var self = this;
            if (self.active >= 13)
                return;
            self.active++;
            this.hide_page(self.active);
            this.update_page_number();
        },
        on_prev: function () {
            var self = this;
            if (self.active === 1) {
                self.active = 1;
                return;
            }
            self.active--;
            this.hide_page(self.active);
            this.update_page_number();
        },

        update_page_number: function () {
            this.$el.find('.current_page').html('Page : ' + this.active);
        },

        on_icon_click: function (ev) {
            var target = $(ev.currentTarget);
            this.$('.icon_btn_chooser_selected').removeClass('icon_btn_chooser_selected')
                .addClass('icon_btn_chooser');
            target.attr('class', 'col-sm-2 icon_btn_chooser_selected');
        },

        store_reserve: function () {
            var self = this;
            var options = {};
            var btn_name = self.$el.find('#input_text_field_id').val();
            var selected_icon = self.$el.find('.icon_btn_chooser_selected').attr('data-value');
            var relation_field = self.$el.find('#input_relation_field_m2o').select2('data');
            if (btn_name && selected_icon && relation_field) {
                options.btn_name = btn_name;
                options.icon = selected_icon.replace(/fa /g, '');
                options.field_name = self.$el.find('#input_relation_field_m2o').select2('data').field_name;
                options.rel_id = relation_field.id;
                self.trigger('save', options);
                self.close();
            } else {
                Dialog.alert(this, 'Please Input Data To Fields');
                return 0;
            }
        }
    });

});