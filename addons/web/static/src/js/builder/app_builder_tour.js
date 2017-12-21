flectra.define('builder.tour', function (require) {
    "use strict";
    var core = require('web.core');
    var tour = require('web_tour.tour');
    var _t = core._t;

    tour.register('builder_tour', {url: "/web",}, [{
        trigger: '.web_navbar_item',
        content: _t('Start building apps, Modify Views This small button Does lots of magic here,' + ':D Let’s activate <b>Flectra App Builder</b>.'),
        position: 'bottom',
    }, {
        trigger: 'button[data-action="mk_app_view"]',
        content: _t('Click here To switch <b> App Creator</b>, Creating An App is Way Damn Easy. '),
        position: 'bottom',
    }, {
        trigger: '.fs-continue',
        content: _t('Grab your seat and get Ready to create your <b>app</b> within <b>5 minute</b>?'),
        position: 'top',
    }, {
        trigger: 'input.fs-anim-lower',
        content: _t('Give Your <b>App Name</b>,' + '<br/><b>\t• </b>Choose a name that’s unique' + '<br/><b>\t• </b>Choose a name that’s descriptive' + '<br/><b>\t• </b>Choose a name that’s easy to say and spell'),
        position: 'bottom'
    }, {
        trigger: 'input.fs-anim-lower',
        content: _t('Give Your <b>Menu Name</b>,e.g My Products, My Itinerary'),
        position: 'bottom'
    }, {
        trigger: 'input.fs-anim-lower',
        content: _t('Give Your <b>App Category</b> e.g Tools,Warehouse,Food Court '),
        position: 'bottom'
    }, {
        trigger: 'input.fs-anim-lower',
        content: _t('Give Your <b>App Version</b>,it is good to practice like odoo_version_app_version'),
        position: 'bottom'
    }, {
        trigger: 'textarea.fs-anim-lower',
        content: _t('Describe Your <b>Application</b>' + 'The goal is to <b>explain app ' + 'features and important app information for users</b>'),
        position: 'bottom'
    }]);
    tour.register('web_tour_icon_maker', {url: "/web?app_builder=app_creator"}, [{
        trigger: '.fcolor_picker',
        content: _t('Select your Favourite Color for App Icon From Wide Variety of Colors <b>Click Here.</b>'),
        position: 'top'
    }, {
        trigger: '.bcolor_picker',
        content: _t('Select Your Favourite Color for App Background From Wide Variety of Colors <b>Click Here.</b>'),
        position: 'top'
    }, {
        trigger: '.cs-skin-boxes',
        content: _t('Start Decorating Your App with icon, We have wide varieties of <b>Material Icons</b>.'),
        position: 'top'
    }, {
        trigger: '.icon_preview',
        content: _t('Wow, Looking cool! And I’m sure you can design it even better!'),
        position: 'top'
    }, {
        trigger: '.cupload_icon',
        content: _t("Just A reminder You can choose an Image, cool isn't it?"),
        position: 'bottom'
    }, {
        trigger: '.fs-continue',
        content: _t("That's it, we are here, hit continue."),
        position: 'top'
    }, {
        trigger: '.fs-current',
        content: _t("Take Your time,look at the details, We fetch it for you to preview." + "<b> We care each and every details!</b>"),
        position: 'top'
    }, {
        trigger: '.fs-continue',
        content: _t("Awesome, We just completed your first app. Click Here Now"),
        position: 'top'
    }]);
    tour.register('web_tour_screen_designing', {url: "/web?app_builder=main"}, [{
        trigger: 'li[data-id="Text"]',
        content: _t("WOW! Your are so fast, Now Let's Customize your view,<b>Drag & Drop Text Field on view"),
        position: 'top'
    }, {
        trigger: '.app_builder-custom:eq(1)',
        content: _t('Click Here To Customize the field.'),
        position: 'left'
    }, {
        trigger: 'input#string',
        content: _t('Now Change the name of the field.'),
        position: 'left'
    }, {
        trigger: 'div#top-nav',
        content: _t('Great Job, Now Click Here to reveal App builder menu.'),
        position: 'bottom'
    }, {
        trigger: 'button[data-action="close_view"]',
        content: _t("That was a great journey, have fun with app builder."),
        position: 'top'
    }]);
});
