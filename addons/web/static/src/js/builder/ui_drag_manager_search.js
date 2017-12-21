flectra.define('web.search_view_editor', function (require) {
    "use strict";

    var bus = require('builder.bus');
    var core = require('web.core');
    var Widget = require('web.Widget');
    var Dialog = require('web.Dialog');
    var search_view = require('web.VirtualSearchView');
    var Misc = require('web.Miscellaneous');
    var qweb = core.qweb;
    var drake = null, element = [];

    var Main = Widget.extend({
        className: 'web_search_editor',
        custom_events: {},

        init: function (parent, context, options) {
            this._super.apply(this, arguments);
            this.fields_view = options.fields_view;
            this.fields_not_in_view = options.fields_not_in_view;
            this.view_id = options.fields_view.view_id;
            this.view_type = options.fields_view.view_type;
            this.view_name = options.fields_view.name;
            this._action = options.action_obj;
            this.overlay = $('#FieldAttrSideNav');
            bus.on('arch_updated', this, this.arch_updated.bind(this));
        },

        arch_updated: function () {
            if (this._action) {
                this._action.options.action.is_auto_load = true;
                this._action.options.action_manager.do_action(this._action.options.action, this._action.options);
            }
        },

        start: function () {
            var self = this;
            var property_tab = $('#properties');
            property_tab.find('.web_sidebar_content').html(qweb.render('web.search_view_properties', {}));
            self.label = $('#string');
            self.domain = $('#domain');
            self.rm_btn = $('#btn_rm_view');
            var sidebar_container = $('.web_sidebar_content');
            if (!this._action.options.action.is_auto_load) {
                sidebar_container.eq(2).remove();
                sidebar_container.eq(4).remove();
                sidebar_container.eq(5).remove();
            }
            sidebar_container.eq(6).before(
                qweb.render('web.search_view_filters', {}));
            this.search_view = new search_view(this, this.fields_view.arch, this.fields_view.fields, {}, {}, {});
            var def = this.search_view.appendTo(this.$el);
            $.when(def).then(function () {
                var drag_drop_container_search =
                    [document.querySelector('.web_sidebar_field_container ul#componenets'),
                        document.querySelector('.web_sidebar_field_container ul#existing')]
                        .concat(Array.from(self.$el[0].querySelectorAll("tbody")));
                self.initDragula(drag_drop_container_search, true);
                self._eventlistener('drag', 'drop', 'shadow', 'dragend');
                self.$el.find('tr').addClass('app_builder-custom');
                self.$el.find('thead').find('tr').removeClass('app_builder-custom');
                self._on_focus('.app_builder-custom');
                self.propertyListener();
                self.attrs = self.search_view.node_attrs;
            });
            $(document.body).click(function (ev) {
                self._on_lose_focus(ev);
            });
        },
        initDragula: function (register_container) {
            if (drake) {
                drake.destroy();
            }
            drake = dragula(register_container, {
                accepts: function (el, target) {
                    return target !== register_container[0] || register_container[1];
                },
                moves: function (el, target) {
                    return target === register_container[0] || target === register_container[1];
                },
                copy: function (el) {
                    return $(el).attr('data-action') === 'filters' || $(el).attr('data-action') === 'separator';
                },
                revertOnSpill: true,
                direction: 'vertical'
            });
        },
        _eventlistener: function (drag, drop, shadow, dragend) {
            drake.on(drag, this.onDrag.bind(drake));
            drake.on(drop, this.onDrop.bind(drake, this));
            drake.on(shadow, this.onShadow.bind(drake, this));
            drake.on(dragend, this.onDragEnd.bind(drake));
        },
        propertyListener: function () {
            var self = this;
            self.label.bind('change', this, self.onTextChange);
            self.domain.bind('change', this, self.onTextChange);
            self.rm_btn.bind('click', this, self.onRemoveElement);
        },

        onRemoveElement: function (ev) {
            var options = {};
            var self = ev.data;
            var target = $('.ui-selector-border');
            var parent = target.parent();
            var is_group = parent.parent().attr('data-type') === 'group_by';
            var is_filter = parent.parent().attr('data-type') === 'filters';
            var is_automated_field = parent.parent().attr('data-type') === 'autocompletion_fields';
            var is_hr = target.find('hr').length === 1;
            var data = self.find_name(parent, 'TR');
            data.index = data.index + 1;
            options.view_id = self.view_id;
            options.tag_operation = 'attributes';
            options.attr_name = 'remove';
            options.pos = 'replace';
            if (is_filter) {
                if (data.name) {
                    options.expr = '//filter[@name="' + data.name + '"][not(ancestor::field)]';
                } else {
                    options.expr = '/search[1]/filter[' + data.index + ']';
                }
            }
            if (is_group) {
                if (data.name) {
                    options.expr = '//filter[@name="' + data.name + '"][not(ancestor::field)]';
                } else {
                    options.expr = '/search[1]/group[1]/filter[' + data.index + ']';
                }
            }
            if (is_automated_field) {
                var field_name = self.find_field_xpath(self.fields_view.fields, self.field_string, 'attributes').xpath_field;
                options.expr = '//field[@name="' + field_name + '"][not(ancestor::field)]';
            }
            if (is_hr) {
                options.expr = '/search[1]/separator[' + self.index_of + ']';
            }
            Misc.update_search_view(options);
        },

        onTextChange: function (ev) {
            var options = {};
            var self = ev.data;
            var parent = $('.ui-selector-border').parent();
            var is_group = parent.parent().attr('data-type') === 'group_by';
            var is_filter = parent.parent().attr('data-type') === 'filters';
            var is_automated_field = parent.parent().attr('data-type') === 'autocompletion_fields';
            var data = self.find_name(parent, 'TR');
            options.view_id = self.view_id;
            options.tag_operation = 'attributes';
            options.pos = 'attributes';
            data.index = data.index + 1;
            if (this.id === 'string') {
                options.value = this.value;
                options.attr_name = 'string';
                if (is_filter) {
                    if (data.name) {
                        options.expr = '//filter[@name="' + data.name + '"][not(ancestor::field)]';
                    } else {
                        options.expr = '/search[1]/filter[' + data.index + ']';
                    }
                    options.attrfor = 'filter';
                }
                if (is_group) {
                    if (data.name) {
                        options.expr = '//filter[@name="' + data.name + '"][not(ancestor::field)]';
                    } else {
                        options.expr = '/search[1]/group[1]/filter[' + data.index + ']';
                    }
                    options.attrfor = 'group';
                }
                if (is_automated_field) {
                    var field_name = self.find_field_xpath(self.fields_view.fields, self.field_string, 'attributes').xpath_field;
                    options.expr = '//field[@name="' + field_name + '"][not(ancestor::field)]';
                    options.attrfor = 'field';
                }
            } else {
                if (is_filter) {
                    options.value = this.value;
                    options.attr_name = 'domain';
                    if (data.name) {
                        options.expr = '//filter[@name="' + data.name + '"][not(ancestor::field)]';
                    } else {
                        options.expr = '/search[1]/filter[' + data.index + ']';
                    }
                    options.attrfor = 'filter';
                }
            }
            Misc.update_search_view(options);
        },

        onDrag: function (el) {
            element.push(el);
            el.className = "ui-drag-item";
            setTimeout(function () {
                el.className = null;
            }, 100)
        },

        prevUntil: function (source, id) {
            var e_prev = $(source).find('li[data-id=' + id + ']').prev().prev();
            if (e_prev) {
                return e_prev;
            }
            return undefined;
        },

        nextUntil: function (source, id) {
            var e_next = $(source).find('li[data-id=' + id + ']').next();
            if (e_next) {
                return e_next;
            }
            return undefined;
        },

        find_index: function (source, selector) {
            var children = $(source).children();
            var index = false;
            for (var i = 0; i < children.length; i++) {
                if (children[i].tagName === selector) {
                    if (children[i].className === 'app_builder-custom ui-selector-border') {
                        return i;

                    }
                    else {
                        index = i;
                    }
                }
            }
            return index;
        },

        find_name: function (source, selector) {
            var children = $(source).children();
            var data = {};
            for (var i = 0; i < children.length; i++) {
                if (children[i].tagName === selector) {
                    if (children[i].className === 'app_builder-custom ui-selector-border') {
                        data.name = $(children[i]).find('td').attr('name');
                        data.index = (i);
                        return data;

                    } else {
                        data.name = $(children[i - 1]).find('td').attr('name');
                        data.index = (i);
                    }
                }
            }
            return data;
        },

        onDrop: function (odoo_object, el, source) {
            var options = {};
            var self = odoo_object;
            var parent = $(source).parent();
            var field_type = $(el).attr('id') || 'field';
            var is_group = parent.attr('data-type') === 'group_by';
            var is_filter = parent.attr('data-type') === 'filters';
            var is_automated_field = parent.attr('data-type') === 'autocompletion_fields';
            var data = self.find_name(source, 'DIV');
            var def = $.Deferred();
            options.field_name = $(el).attr('data-id');
            options.view_id = self.view_id;
            options.tag_operation = is_automated_field ? 'add_field' : is_group ? 'add_group' : is_filter ? 'add_filter' : null;
            if (is_automated_field && field_type === 'field') {
                options.nearest_prev = self.prevUntil(source, options.field_name)
                    ? self.prevUntil(source, options.field_name).find('span').html().trim() : undefined;
                options.nearest_next = self.nextUntil(source, options.field_name)
                    ? self.nextUntil(source, options.field_name).find('span').html().trim() : undefined;

                if (options.nearest_next !== undefined || options.nearest_prev !== undefined) {
                    var xdata = self.find_field_xpath(self.fields_view.fields,
                        'before' ? options.nearest_prev : options.nearest_next
                        , options.nearest_prev ? 'after' : 'before');
                    if (xdata) {
                        options.xpath_field_name = xdata.xpath_field;
                        options.pos = xdata.position;
                    }
                    else {
                        xdata = self.find_field_xpath(self.fields_view.fields,
                            'before' ? options.nearest_next : options.nearest_prev
                            , options.nearest_next ? 'before' : 'after');
                        options.xpath_field_name = xdata.xpath_field;
                        options.pos = xdata.position;
                    }
                }
                def.resolve(options);
            } else if (is_group && field_type === 'field') {
                options.pos = data.index === 0 ? 'before' : 'after';
                if (data.name) {
                    options.expr = '//filter[@name="' + data.name + '"][not(ancestor::field)]';
                } else {
                    options.expr = '/search[1]/group[1]/filter[' + data.index + ']';
                }
                options.attributes = self.get_attributes(self.fields_not_in_view, options.field_name);
                if (options.attributes.type !== 'one2many') {
                    def.resolve(options);
                } else {
                    def.reject();
                }
            } else if (is_filter && (field_type === 'filters' || field_type === 'separator')) {
                options.pos = data.index === 0 ? 'before' : 'after';
                if (data.name) {
                    options.expr = '//filter[@name="' + data.name + '"][not(ancestor::field)]';
                } else {
                    options.expr = '/search[1]/filter[' + data.index + ']';
                }
                options.tag_operation = field_type === 'separator' ? 'add_separator' : options.tag_operation;
                options.attributes = self.get_attributes(self.fields_not_in_view, options.field_name);
                options.field_name = "app_builder_" + field_type + "_" + Misc.rstring(4);
                def.resolve(options);
            } else {
                def.reject();
            }
            $.when(def).then(function (args) {
                Misc.update_search_view(args);
            }).fail(function () {
                Dialog.alert(self, 'Field Not Droppable!');
                var id = $(el).attr('id') || 'field';
                $(el).remove();
                if(id ==='filters' || id==='separator'){}
                else{
                    $('ul#existing').prepend(el);
                }
            });

        },

        table: function () {
            var row = document.createElement("div");
            row.style.height = "100%";
            row.style.width = "100%";
            row.style.backgroundColor = "#0E76A8";
            row.appendChild(document.createTextNode('\u00A0 \u00A0 \u00A0 \u00A0'));
            return row;
        },

        onShadow: function (odoo_object, el, source) {
            var self = odoo_object;
            $("li[data-id='" + $(el).attr('data-id') + "']").animate({'opacity': '1'}, 200);
            var $currentTable = $(source).closest('table');
            var index = $(source).index();
            $currentTable.find('td').removeClass('tb-hover');
            $currentTable.find('th').removeClass('th-hover');
            $currentTable.find('tr').each(function (i, tr) {
                $(tr).find('td').eq(index).addClass('tb-hover');
                $(tr).find('th').eq(index).addClass('th-hover');
            });
            if (!this._shadow) {
                this._shadow = self.table();
                this._shadow.classList.add("gu-transit");
                this._shadow.classList.add("ui-shadow-border");
            }
            el.style.display = 'none';
            el.parentNode.insertBefore(this._shadow, el);
        },

        onDragEnd: function (el) {
            $(el).removeAttr('style');
            $(el).removeClass('ui-shadow-border');
            $(el).removeClass('gu-transit');
            $(el).removeClass('ui-drag-item');
            if (this._shadow) {
                this._shadow.remove();
                this._shadow = null;
            }
        },

        find_field_xpath: function (fields, match, pos) {
            for (var j in fields) {
                // if (fields[j].__attrs.string) {
                //     if (fields[j].__attrs.string === match) {
                //         return {
                //             'xpath_field': j.trim()
                //         }
                //     }
                // } else
                {
                    if (fields[j].string === match) {
                        return {
                            'xpath_field': j.trim(),
                            'position': pos
                        }
                    }
                }
            }
        },

        get_attributes: function (fields, key) {
            return fields[key];
        },

        get_selector_parent: function (selector) {
            return $(selector).parent().parent().attr('data-type');
        },

        get_attrs: function (field_string) {
            var self = this;
            _.each(this.attrs, function (obj) {
                var string = obj.string || obj.help;
                if (string === field_string) {
                    self.label.val(obj.string || obj.help);
                    self.domain.val(obj.domain);
                }
            });
        },
        _on_lose_focus: function (ev) {
            var self = this;
            var $target = $(ev.target);
            // since we don't want to hide nav-overlay for a specific area click(s) on body.
            if ($target.parent().parent().hasClass('ui-selector-border') || $target.parent('li').hasClass('app_builder-custom')
                || $target[0].tagName === 'TD' || $target.parents('div#FieldAttrSideNav').length) {
                return;
            }
            self.close_sidebar();
            self.$el.find('.ui-selector-border').removeClass('ui-selector-border');
        },

        _on_focus: function (selector) {
            var highlight = 'ui-selector-border';
            var self = this;
            var currentElement = self.$el.find(selector).click(function (e) {
                self.open_sidebar();
                var get_parent_name = self.get_selector_parent($(this));
                self.index_of = $(this).index();
                self.field_string = $(this).find('span').text();
                currentElement.removeClass(highlight);
                self.domain.parent().parent().show();
                self.label.parent().parent().show();
                self.label.val('');
                self.domain.val('');
                $(this).addClass(highlight);
                if (get_parent_name === 'autocompletion_fields' || get_parent_name === 'group_by') {
                    self.domain.parent().parent().hide();
                }
                if ($(this).find('hr').length) {
                    self.domain.parent().parent().hide();
                    self.label.parent().parent().hide();
                }
                self.get_attrs(self.field_string);
                $('.web_header').find('a[href="#properties"]').tab('show');
            });
            return currentElement;
        },

        do_action: function (action, options) {
            return this._super.apply(this, arguments);
        },
        open_sidebar: function () {
            Misc.on_overlay_close();
            this.overlay.css('width', '350px');
        },
        close_sidebar: function () {
            this.overlay.css('width', '0');
        }
    });

    core.action_registry.add('app_builder_search_view', Main);

});
