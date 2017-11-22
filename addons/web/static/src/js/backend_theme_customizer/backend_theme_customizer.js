flectra.define('web.BackendThemeCustomizer', function (require) {
"use strict";

var SystrayMenu = require('web.SystrayMenu');
var Widget = require('web.Widget');
var Theme = require('web.CustomizeSwitcher');
var session = require('web.session');

/**
 * Menu item appended in the systray part of the navbar, redirects to the Inbox in Discuss
 * Also displays the needaction counter (= Inbox counter)
 */

var CustomizeMenu = Widget.extend({
    template: 'web.customize_menu',
    events: {
        "click": "on_click",
    },
    on_click: function (event) {
        theme_customize_backend();
    },
});

function theme_customize_backend() {
    if (Theme.open && !Theme.open.isDestroyed()) return;
    Theme.open = new Theme();
    Theme.open.appendTo("body");
    var error = window.getComputedStyle(document.body, ':before').getPropertyValue('content');
    if (error && error !== 'none') {
        themeError(eval(error));
    }
}

if (session.is_superuser) {
    SystrayMenu.Items.push(CustomizeMenu);
}

});
