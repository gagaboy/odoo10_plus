flectra.define('builder.bus', function (require) {
    "use strict";

    var Action = require('web.Bus');
    var bus = new Action();

    bus.on('app_builder_toggled', null, function (mode) {
        var URL = $.deparam.querystring();
        mode ? URL.app_builder = mode : delete URL.app_builder;
        push_history(URL);
    });

    bus.on('action_reload', null, function (mode, action) {
        if (!mode && action === 'home') {
            var location = window.location;
            var url = location.href.replace('app_builder=main', '');
            var qs = $.deparam.querystring();
            var qs_key = Object.keys(qs);
            var qs_value = Object.values(qs);
            if (qs_key.length >= 2) {
                if ($.inArray('app_builder', qs_key) >= 0) {
                    if (qs_key.indexOf('app_builder') > 0) {
                        url = location.href.replace('&app_builder=main', '');
                    }
                }
            }
            if ($.inArray('app_creator', qs_value) >= 0) {
                if (qs_key.indexOf('app_builder') > 0) {
                    url = location.href.replace('&app_builder=app_creator', '');
                } else {
                    url = location.href.replace('app_builder=app_creator', '');
                }
            }

            window.history.pushState({path: url}, '', url);
            location.reload();
        }
    });

    function push_history(act_url) {
        var location = window.location;
        var pathname = location.pathname;
        var pqs = $.deparam.querystring();
        var url = location.href.replace(/\?+/g, '');
        url = url.replace($.param(pqs), '');
        url = url.replace(pathname, pathname + '?' + $.param(act_url));
        window.history.pushState({path: url}, '', url);
    }

    return bus;
});
