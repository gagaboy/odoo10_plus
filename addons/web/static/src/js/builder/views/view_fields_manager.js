flectra.define('web.FieldsManager', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var new_fields = [];
    var CharFieldComponent = Widget.extend({
        ttype: 'char',
        label: 'Text'
    });

    var TextFieldComponent = Widget.extend({
        ttype: 'text',
        label: 'MultilineText'
    });

    var IntegerFieldComponent = Widget.extend({
        ttype: 'integer',
        label: 'IntegerNumber'
    });
    var DecimalFieldComponent = Widget.extend({
        ttype: 'float',
        label: 'DecimalNumber'
    });
    var HtmlFieldComponent = Widget.extend({
        ttype: 'html',
        label: 'Html'
    });
    var MonetaryFieldComponent = Widget.extend({
        ttype: 'monetary',
        label: 'Monetary'
    });
    var DateFieldComponent = Widget.extend({
        ttype: 'date',
        label: 'Date'
    });
    var DatetimeFieldComponent = Widget.extend({
        ttype: 'datetime',
        label: 'DateTime'
    });
    var BooleanFieldComponent = Widget.extend({
        ttype: 'boolean',
        label: 'Checkbox'
    });
    var SelectionFieldComponent = Widget.extend({
        ttype: 'selection',
        label: 'Select'
    });
    var BinaryFieldComponent = Widget.extend({
        ttype: 'binary',
        label: 'File'
    });

    var Many2manyFieldComponent = Widget.extend({
        ttype: 'many2many',
        label: 'Many2many'
    });
    var One2manyFieldComponent = Widget.extend({
        ttype: 'one2many',
        label: 'One2many'
    });
    var Many2oneFieldComponent = Widget.extend({
        ttype: 'many2one',
        label: 'Many2one'
    });


    new_fields.push(
        BinaryFieldComponent,
        BooleanFieldComponent,
        CharFieldComponent,
        DateFieldComponent,
        DatetimeFieldComponent,
        DecimalFieldComponent,
        HtmlFieldComponent,
        IntegerFieldComponent,
        MonetaryFieldComponent,
        Many2manyFieldComponent,
        Many2oneFieldComponent,
        One2manyFieldComponent,
        SelectionFieldComponent,
        TextFieldComponent
    );
    return {new_fields: new_fields}
});