flectra.define('builder.systray', function (require) {
    "use strict";

    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');

    var FlectraAppBuilderConfig = Widget.extend({
        template: 'web.config',
        events: {
            "click a": function (e) {
                e.preventDefault();
                this.trigger_up('open_app_builder');
            }
        }
    });

    SystrayMenu.Items.push(FlectraAppBuilderConfig);

});