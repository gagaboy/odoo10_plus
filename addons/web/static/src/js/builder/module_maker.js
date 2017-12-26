flectra.define('web.ModuleMaker', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var ActionRelation = require('web.ActionRelation');
    var ModuleMakerUtility = require('web.ModuleMakerUtils');
    var misc = require('web.Miscellaneous');
    var Dialog = require('web.Dialog');
    var relation;

    var ModuleMaker = Widget.extend({
        template: 'web.ModuleMaker',
        events: {
            'click .fs-continue': 'on_next_page',
            'click .fs-nav-dots button': 'on_prev_page',
            'click #cupload_icon > a': 'upload_binary',
            'change input[type=color]': 'change_color',
            'change #iupload_icon': 'onFileSelect',
            'keyup input#q3': 'checkDuplicate'
        },

        init: function () {
            this._super.apply(this, arguments);
            var self = this;
            this.current_page = 0;
            this.colors = ['#3b3f45', '#804141', '#efbe59', '#5b9857', '#5a4a94', '#d9524e', '#3f8790', '#325f3e'];
            this.ICONS = [
                'whatshot',
                'all_inclusive',
                'all_out',
                'android',
                'announcement',
                'blur_circular',
                'blur_linear',
                'blur_off',
                'blur_on',
                'book',
                'bookmark',
                'copyright',
                'create',
                'create_new_folder',
                'credit_card',
                'crop',
                'drafts',
                'drag_handle',
                'drive_eta',
                'dvr',
                'edit',
                'edit_location',
                'eject',
                'forum',
                'forward',
                'forward_10',
                'forward_30',
                'forward_5',
                'free_breakfast',
                'fullscreen',
                'fullscreen_exit',
                'functions',
                'gamepad'
            ];
            this.hex_colors = ["ffebee", "FCE4EC", "F3E5F5", "EDE7F6", "E8EAF6", "E3F2FD", "E1F5FE", "E0F7FA",
                "E0F2F1", "E8F5E9", "F1F8E9", "F9FBE7", "FFFDE7", "FFF8E1", "FFF3E0", "FBE9E7", "EFEBE9",
                "FAFAFA", "ECEFF1", "ffcdd2", "F8BBD0", "E1BEE7", "D1C4E9", "C5CAE9", "BBDEFB", "B3E5FC",
                "B2EBF2", "B2DFDB", "C8E6C9", "DCEDC8", "F0F4C3", "FFF9C4", "FFECB3", "FFE0B2", "FFCCBC",
                "D7CCC8", "F5F5F5", "CFD8DC", "ef9a9a", "F48FB1", "CE93D8", "B39DDB", "9FA8DA", "90CAF9", "81D4FA",
                "80DEEA", "80CBC4", "A5D6A7", "C5E1A5", "E6EE9C", "FFF59D", "FFE082", "FFCC80", "FFAB91", "BCAAA4",
                "EEEEEE", "B0BEC5", "e57373", "F06292", "BA68C8", "9575CD", "7986CB", "64B5F6", "4FC3F7", "4DD0E1", "4DB6AC",
                "81C784", "AED581", "DCE775", "FFF176", "FFD54F", "FFB74D", "FF8A65", "A1887F", "E0E0E0", "90A4AE", "ef5350",
                "EC407A", "AB47BC", "7E57C2", "5C6BC0", "42A5F5", "29B6F6", "26C6DA", "26A69A", "66BB6A", "9CCC65", "D4E157",
                "FFEE58", "FFCA28", "FFA726", "FF7043", "8D6E63", "BDBDBD", "78909C", "f44336", "E91E63", "9C27B0", "673AB7",
                "3F51B5", "2196F3", "03A9F4", "00BCD4", "009688", "4CAF50", "8BC34A", "CDDC39", "FFEB3B", "FFC107", "FF9800",
                "FF5722", "795548", "9E9E9E", "607D8B", "e53935", "D81B60", "8E24AA", "5E35B1", "3949AB", "1E88E5", "039BE5",
                "00ACC1", "00897B", "43A047", "7CB342", "C0CA33", "FDD835", "FFB300", "FB8C00", "F4511E", "6D4C41", "757575",
                "546E7A", "d32f2f", "C2185B", "7B1FA2", "512DA8", "303F9F", "1976D2", "0288D1", "0097A7", "00796B", "388E3C",
                "689F38", "AFB42B", "FBC02D", "FFA000", "F57C00", "E64A19", "5D4037", "616161", "455A64", "c62828", "AD1457",
                "6A1B9A", "4527A0", "283593", "1565C0", "0277BD", "00838F", "00695C", "2E7D32", "558B2F", "9E9D24", "F9A825",
                "FF8F00", "EF6C00", "D84315", "4E342E", "424242", "37474F", "b71c1c", "880E4F", "4A148C", "311B92", "1A237E",
                "0D47A1", "01579B", "006064", "004D40", "1B5E20", "33691E", "827717", "F57F17", "FF6F00", "E65100", "BF360C",
                "3E2723", "212121", "263238"];
            this.app_licence = [
                ['GPL-2', 'GPL Version 2'],
                ['GPL-2 or any later version', 'GPL-2 or later version'],
                ['GPL-3', 'GPL Version 3'],
                ['GPL-3 or any later version', 'GPL-3 or later version'],
                ['AGPL-3', 'Affero GPL-3'],
                ['LGPL-3', 'LGPL Version 3'],
                ['Other OSI approved licence', 'Other OSI Approved Licence'],
                ['OEEL-1', 'Flectra Enterprise Edition License v1.0'],
                ['OPL-1', 'Flectra Proprietary License v1.0'],
                ['Other proprietary', 'Other Proprietary']
            ];
            this.controls = [];
            relation = new ActionRelation();
            relation.pageElements().sub_menu.hide();
            relation.pageElements().control_panel.hide();
            relation.pageElements().o_navbar.remove();
            relation.register_close_button();
            this.$app_builder_nav = $('.app_builder_nav');
            this.$app_builder_nav.find('button[data-action=app_create]').hide();
            this.$app_builder_nav.next().remove();
            $(document.body).unbind("keyup");
            $(document.body).on("keyup", function (ev) {
                var keyCode = ev.keyCode || ev.which;
                if (keyCode === 13) {
                    ev.preventDefault();
                    ev.delegateTarget = $('.flectra_module_maker');
                    self.on_enterKey_listener(ev);
                }
            });
        },

        start: function () {
            // Utility Tools.
            var self = this;
            self.mmu = new ModuleMakerUtility(this);
            self.mmu.prependTo(this.$app_builder_nav);
            $('button[data-action="mk_app_view"]').hide();
            $('#top-nav').hide();
        },

        checkDuplicate: function (ev) {
            var $target = $(ev.currentTarget);
            var objName = $target.val().replace(/[^A-Z0-9]+/ig, "_");
            misc.check_obj_name(objName, $target);
        },

        upload_binary: function (ev) {
            //Use InCase user don't wanna create icon but upload image!.
            ev.preventDefault();
            $(ev.currentTarget).next().attr('accept', 'image/*');
            $(ev.currentTarget).next().trigger('click');
        },

        onFileSelect: function (e) {
            var self = this;
            var $target = $(e.currentTarget);
            var ext = $target.val().split('.').pop().toLowerCase();
            if ($.inArray(ext, ['gif', 'png', 'jpg', 'jpeg']) === -1) {
                Dialog.alert(self, 'invalid Image File!');
                return;
            }
            self.files = $target.prop('files');
            var file = self.files[0];
            var fr = new FileReader();
            var def = $.Deferred();
            fr.onload = function () {
                var image_binary = {
                    file_name: file.name,
                    base_64_data: fr.result.split('base64,')[1]
                };
                def.resolve(image_binary);
            };
            fr.readAsDataURL(file);
            $.when(def).then(function (image_binary) {
                self.set_default_icon(null, null, image_binary)
            });
        },

        change_color: function (ev) {
            //changes color from color picker input.
            var $target = $(ev.currentTarget);
            var $icon_prev = this.$el.find('.icon_preview');
            $icon_prev.css({'background-image': ''});
            var color = $target.val();
            var picker = $target.parent().attr('id');
            if (picker === 'fcolor_picker') {
                $icon_prev.css({'color': color});
                $icon_prev.attr('data-color', color);
            } else {
                $icon_prev.css({'backgroundColor': color});
                $icon_prev.attr('data-bcolor', color);
            }
        },

        on_enterKey_listener: function (ev) {
            //listen to enter key press.
            var self = this;
            if (ev.target.tagName === 'TEXTAREA')
                return;
            setTimeout(function () {
                self.on_next_page(ev);
            }, 20)
        },

        on_prev_page: function (ev) {
            // a hack for clicking on dot(s) to identify current page.
            this.current_page = $('.fs-dot-current').index();
            var currentTarget = $(ev.delegateTarget);
            var $page = currentTarget.find('li.fs-current');
            this.automate_color_changer(currentTarget);
            if (this.current_page === 6) {
                this.$el.find('.icon_preview').removeClass('top-40');
            }
            if (this.current_page === 7) {
                this.$el.find('.icon_preview').addClass('top-40');
            }
        },

        automate_color_changer: function (currentTarget) {
            currentTarget.stop().animate({backgroundColor: this.colors[this.current_page]}, 300);
        },

        on_next_page: function (ev) {
            var $target = $(ev.target);
            if($target.attr('has_model') === "0"){
                return;
            }
            var currentTarget = $(ev.delegateTarget);
            var $page = currentTarget.find('li.fs-current');
            var $error = currentTarget.find('span.fs-message-error');
            var $input = $page.find('input[type=text]');
            var $textarea = $page.find('textarea');
            var $number = $page.find('input[type=number]');
            var $licence_list = $page.find('select.custom-select-fx');
            var color = '#' + _.sample(this.hex_colors);
            var bcolor = '#' + _.sample(this.hex_colors);
            if ($input.length)
                this.controls.push($input);
            if ($licence_list.length)
                this.controls.push($licence_list);
            if ($number.length)
                this.controls.push($number);
            if ($textarea.length)
                this.controls.push($textarea);
            if (!$error.hasClass('fs-show')) {
                this.current_page++;
                this.automate_color_changer(currentTarget);
            }
            this.set_default_icon(color, bcolor, null);
            this.setup_preview();
            this.fetch_values();
            this.create_app_when_ready();
        },
        fetch_values: function () {
            // since we are traversing into pages we need to collect
            // all input data so we are going to fetch values of it.
            var self = this;
            if (this.current_page === 7) {
                this.app_name = $(self.controls[0]).val().replace(/[^A-Z0-9]+/ig, "_");
                this.menu_name = $(self.controls[1]).val().replace(/[^A-Z0-9]+/ig, "_");
                this.app_category = $(self.controls[2]).val().replace(/[^A-Z0-9]+/ig, "_");
                this.app_version = $(self.controls[3]).val();
                this.app_description = $(self.controls[5]).val();
                this.app_licence = $(self.controls[4]).val();
                this.color = this.$el.find('.icon_preview').attr('data-color');
                this.backgroundColor = this.$el.find('.icon_preview').attr('data-bcolor');
                this.icon = [this.color, this.backgroundColor, this.$el.find('.icon_preview').first().text()];
                self.$el.find('#app_name').html('').append('App Name : ' + this.app_name);
                self.$el.find('#object_name').html('').append('Object Name : ' + this.menu_name);
                self.$el.find('#app_category').html('').append('Category : ' + this.app_category);
                self.$el.find('#app_version').html('').append('Version : ' + this.app_version);
                self.$el.find('#app_description').html('').append('Description : ' + this.app_description);
                self.$el.find('#app_licence').html('').append('Licence : ' + this.app_licence);
            }
        },

        set_default_icon: function (color, bcolor, image_binary) {
            var self = this;
            if (this.current_page === 6) {
                var $icon_prev = this.$el.find('.icon_preview');
                self.$el.find('.icon_preview').removeClass('top-40');
                if (!image_binary) {
                    var icon = _.sample(this.ICONS);
                    var fcolor_picker = $('#fcolor_picker').find('input[type=color]');
                    var bcolor_picker = $('#bcolor_picker').find('input[type=color]');
                    $icon_prev.css({'color': color});
                    $icon_prev.attr('data-color', color);
                    $icon_prev.css({'backgroundColor': bcolor});
                    $icon_prev.attr('data-bcolor', bcolor);
                    fcolor_picker.attr('value', color);
                    bcolor_picker.attr('value', bcolor);
                    var $div = '<div class="material-icon-preview material-icons icon_preview_mirror">' + icon + '</div>';
                    $icon_prev.html('');
                    $icon_prev.append($div);
                    self.theres_binary = false;
                    self.set_selectFX_props(color, bcolor, icon);
                } else {
                    self.image_binary_data = 'data:image/png;base64,' + image_binary.base_64_data;
                    self.theres_binary = true;
                    $icon_prev.html('');
                    $icon_prev.css({'background-image': 'url(' + self.image_binary_data + ')'});
                    $icon_prev.css({
                        "background-repeat": "no-repeat",
                        "background-position": "center center",
                        "background-size": "cover"
                    });
                }
            }
        },

        set_selectFX_props: function (color, backcolor, icon) {
            if (color) {
                this.setCSSelect(0, color);
            }
            if (backcolor) {
                this.setCSSelect(1, backcolor);
            }
            if (icon) {
                $('.cs-placeholder:eq(' + 2 + ')').html('');
                this.setCSSelect(2, icon);
                var div = '<div class="material-icon-preview material-icons icon_preview_mirror">' + icon + '</div>';
                $('.cs-placeholder:eq(' + 2 + ')').append(div);
            }
        },

        setCSSelect: function (index, color) {
            $('div.cs-options:eq(' + index + ')').find('li').each(function (es, el) {
                if ($(el).attr('data-value') === color) {
                    $(el).addClass('cs-selected');
                }
            });
            $('.cs-placeholder:eq(' + index + ')').css('backgroundColor', color).text(color)
        },

        setup_preview: function () {
            if (this.current_page === 7) {
                var $icon_prev = this.$el.find('.icon_preview');
                $icon_prev.addClass('top-40');
            }
        },

        create_app_when_ready: function () {
            var self = this;
            if (this.current_page === 8) {
                var app_creator_data = [
                    self.app_name, self.menu_name, self.icon,
                    self.app_category, self.app_version,
                    self.app_description, self.app_licence,
                    self.theres_binary
                ];
                misc.create_new_app(app_creator_data, self.files)
                    .then(function (result) {
                        self.trigger_up('on_new_app_create', result);
                    });
            }
        }
    });
    core.action_registry.add('action_web_app_creator', ModuleMaker);
});