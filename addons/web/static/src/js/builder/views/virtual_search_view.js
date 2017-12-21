flectra.define('web.VirtualSearchView', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var core = require('web.core');
    var qweb = core.qweb;

    return Widget.extend({
        className: "o_search_view",
        init: function (parent, arch, fields) {
            this._super.apply(this, arguments);
            this.arch = arch;
            this.fields = fields
        },

        start: function () {
            var self = this;
            this.$el.empty();
            this.$el.html(qweb.render('web.searchRenderer', this.widget));
            this.node_attrs = [];
            _.each(this.arch.children, function (node, index) {
                self.node_attrs.push(node.attrs);
                if (node.tag === "field") {
                    self.add_field(node, index);
                } else if (node.tag === "filter") {
                    self.add_filter(node, index);
                } else if (node.tag === "separator") {
                    self.add_separator(node, index);
                } else if (node.tag === "group") {
                    self.loop_group_by(node, index);
                }
            });

            return this._super.apply(this, arguments);
        },
        add_field: function (node, index) {
            var $tbody = this.$('.web_search_autocompletion_fields tbody');
            var field_string = this.fields[node.attrs.name].string;
            var display_string = node.attrs.string || field_string;
            var field_name = node.attrs.name || null;
            var $new_row = $('<tr>').append(
                $('<td>').attr('index', index).attr('name', field_name).append(
                    $('<span>').text(display_string)
                ));
            $tbody.append($new_row);
            return $new_row;
        },
        add_filter: function (node, index) {
            var $tbody = this.$('.web_search_filters tbody');
            var display_string = node.attrs.string || node.attrs.help;
            var field_name = node.attrs.name || null;
            var $new_row = $('<tr>').append(
                $('<td>').attr('index', index).attr('name', field_name).append(
                    $('<span>').text(display_string)
                ));
            $tbody.append($new_row);
            return $new_row;
        },
        add_separator: function (node, index) {
            var $tbody = this.$('.web_search_filters tbody');
            var td = $('<td>').attr('index', index).append(
                $('<hr/>')
            );
            var $new_row = $('<tr class="o_web_separator">').html(td);

            $tbody.append($new_row);
            return $new_row;
        },
        add_group_by: function (node, index) {
            var $tbody = this.$('.web_search_group_by tbody');
            var display_string = node.attrs.string;
            /*var group_by_name = node.attrs.context.match(":.?'(.*)'")[1];*/
            var field_name = node.attrs.name || null;
            var $new_row = $('<tr>').append(
                $('<td>').attr('index', index + 1).attr('name', field_name).append(
                    $('<span>').text(display_string)
                ));
            $tbody.append($new_row);
            return $new_row;
        },
        loop_group_by: function (groups, index) {
            var self = this;
            _.each(groups.children, function (node, i) {
                if (node.tag === "filter") {
                    self.add_group_by(node, i);
                }
            });
        }
    });
});
