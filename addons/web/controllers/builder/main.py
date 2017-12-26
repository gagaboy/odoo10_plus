from flectra import http, _
from flectra.http import content_disposition, request
from flectra.exceptions import UserError
from flectra.tools import topological_sort, pycompat
from flectra.osv.expression import OR
from collections import OrderedDict
from lxml import etree
from lxml.builder import E
import io
import json
import os.path
import zipfile


class FlectraAppBuilder(http.Controller):
    def calendar_view(self, expr, position, attr_name, attr_value):
        xpath = etree.Element('xpath')
        expr = expr
        xpath.set('expr', expr)
        xpath.set('position', position)
        if position == 'attributes':
            attribute = etree.Element('attribute')
            xpath.append(attribute)
            attribute.set('name', attr_name)
            attribute.text = attr_value
        return etree.tostring(xpath).decode("utf-8")

    def add_button(self, expr, position, icon, name, action_id, label):
        xpath = etree.Element('xpath')
        expr = expr
        xpath.set('expr', expr)
        xpath.set('position', position)
        button = etree.Element('button')
        xpath.append(button)
        button.set('class', 'oe_stat_button')
        button.set('icon', icon)
        button.set('name', action_id)
        button.set('type', 'action')
        field = etree.Element('field')
        button.append(field)
        field.set('name', name)
        field.set('string', label)
        field.set('widget', 'statinfo')
        return etree.tostring(xpath).decode("utf-8")

    def field_arch(self, name, xpath_field, position,
                   attr_name, attr_value):
        xpath = etree.Element('xpath')
        if name == 'form' or name == 'tree':
            expr = "//" + name + "[not(ancestor::field)]"
        else:
            expr = '//field[@name="' + name + '"][not(ancestor::field)]'
        xpath.set('expr', expr)
        xpath.set('position', position)
        if position == 'after' or position == 'before':
            expr = "//field[@name='" + xpath_field + "'][not(ancestor::field)]"
            xpath.set('expr', expr)
            field = etree.Element('field')
            xpath.append(field)
            field.set('name', name)
        elif position == 'attributes':
            attribute = etree.Element('attribute')
            xpath.append(attribute)
            attribute.set('name', attr_name)
            attribute.text = attr_value
        return etree.tostring(xpath).decode("utf-8")

    def group_by_arch(self, expr, name, xpath_field,
                      position, attributes, tag):
        xpath = etree.Element('xpath')
        xpath.set('expr', expr)
        xpath.set('position', position)
        filter = etree.Element('filter')
        if tag == 'add_group':
            filter.set('context', "{'group_by': '" + name + "'}")
            filter.set('label', attributes.get('string'))
            filter.set('store', str(attributes.get('store')))
            filter.set('ttype', attributes.get('type'))
            filter.set('string', attributes.get('string'))
            filter.set('name', name)
            xpath.append(filter)
        elif tag == 'add_filter':
            filter.set('string', name)
            filter.set('domain', '[["id","=","8"]]')
            filter.set('name', name)
            xpath.append(filter)
        else:
            separator = etree.Element('separator')
            separator.set('name', name)
            xpath.append(separator)
        return etree.tostring(xpath).decode("utf-8")

    def set_search_view_attr(self, expr, value, position, attrfor, attr_name):
        xpath = etree.Element('xpath')
        xpath.set('expr', expr)
        xpath.set('position', position)
        if position == 'attributes':
            attribute = etree.Element('attribute')
            attribute.set('name', attr_name)
            attribute.text = value
            xpath.append(attribute)
        return etree.tostring(xpath).decode("utf-8")

    def page_arch(self, id, expr, group_name,
                  name, tab_name, position, attr_name):
        if group_name:
            xpath = etree.Element('xpath')
            expr = "//group[@name='" + group_name \
                   + "'][not(ancestor::field)]"
            xpath.set('expr', expr)
            xpath.set('position', position)
            field = etree.Element('field')
            xpath.append(field)
            field.set('name', name)
            return etree.tostring(xpath).decode("utf-8")
        if tab_name and not position == 'attributes':
            return self.notebook_arch(id, expr, position, tab_name, 'page')
        if position == 'replace':
            xpath = etree.Element('xpath')
            xpath.set('expr', expr)
            xpath.set('position', position)
            return etree.tostring(xpath).decode("utf-8")
        if position == 'attributes':
            xpath = etree.Element('xpath')
            xpath.set('expr', expr)
            xpath.set('position', position)
            attribute = etree.Element('attribute')
            xpath.append(attribute)
            attribute.set('name', attr_name)
            attribute.text = tab_name
            return etree.tostring(xpath).decode("utf-8")

    def notebook_arch(self, id, expr, position, tab_name, operation):
        xpath = etree.Element('xpath')
        xpath.set('expr', expr)
        xpath.set('position', position)
        if operation == "notebook":
            notebook = etree.SubElement(xpath, 'notebook')
            notebook.set('name', id)
            page = etree.SubElement(notebook, 'page')
        else:
            page = etree.SubElement(xpath, 'page')
        page.set('name', id)
        page.set('string', tab_name)
        group_parent = etree.SubElement(page, 'group')
        group_parent.set('name', id)
        group_child_left = etree.SubElement(group_parent, 'group')
        group_child_left.set('name', id + '_left')
        group_child_right = etree.SubElement(group_parent, 'group')
        group_child_right.set('name', id + '_right')
        return etree.tostring(xpath).decode("utf-8")

    def add_db_new_field(self, options, model):
        values = {}
        model_obj = request.env['ir.model'].search([('model', '=', model)])
        ttype = options.get('field_type')

        if ttype == 'selection':
            values.update({
                'selection': str(options.get('selection_list'))})

        if ttype == 'many2many' or ttype == 'many2one':
            if options.get('rel_id'):
                values.update({
                    'relation': request.env[
                        'ir.model'].browse(options.get('rel_id')).model
                })

        if ttype == 'one2many':
            if options.get('rel_id'):
                field = request.env[
                    'ir.model.fields'].browse(options.get('rel_id'))
                values.update({
                    'relation': field.model_id.model,
                    'relation_field': field.name,
                })

        values.update({
            'model_id': model_obj.id,
            'ttype': ttype,
            'name': options.get('field_name'),
            'field_description': 'New ' + options.get('label'),
            'model': model
        })
        return request.env['ir.model.fields'] \
            .with_context({'app_builder': True}).create(values)

    def create_action_button(self, m, field_id, btn_name):
        ir_model_field = request.env['ir.model.fields'].browse(field_id)
        m = request.env['ir.model']. \
            search([('model', '=', m)], limit=1)
        btn_fname = 'x_' + ir_model_field.name + '_count'
        new_button_field = request.env['ir.model.fields'].search(
            [('name', '=', btn_fname), ('model_id', '=', m.id)])

        if not new_button_field:
            cmp = """
                    results = self.env['%(model)s'].read_group([
                    ('%(field)s', 'in', self.ids)],'%(field)s', '%(field)s')
                    dat = {}
                    for x in results: dat[x['%(field)s'][0]
                    ] = x['%(field)s_count']
                    for rec in self: rec['%(count_field)s'
                    ] = dat.get(rec.id, 0)
                """ % {
                'model': ir_model_field.model,
                'field': ir_model_field.name,
                'count_field': btn_fname,
            }
            new_button_field = request.env['ir.model.fields'].with_context(
                {'app_builder': True}).create(
                {
                    'name': btn_fname,
                    'field_description': ir_model_field.field_description + ' count',
                    'model': m.model,
                    'model_id': m.id,
                    'ttype': 'integer',
                    'store': False,
                    'compute': cmp.replace('    ', ''),
                })

        domain_active_id = "[('%s', '=', active_id)]" % (ir_model_field.name)
        btn_ctx = "{'search_default_%s': active_id," \
                  "'default_%s': active_id}" % \
                  (ir_model_field.name, ir_model_field.name)
        btn_act = request.env['ir.actions.act_window'].search([
            ('name', '=', btn_name), ('res_model', '=', ir_model_field.model),
            ('domain', '=', domain_active_id),
            ('context', '=', btn_ctx),
        ])

        if not btn_act:
            btn_act = request.env['ir.actions.act_window'].with_context(
                {'app_builder': True}).create(
                {
                    'name': btn_name,
                    'res_model': ir_model_field.model,
                    'view_mode': 'tree,form',
                    'view_type': 'form',
                    'domain': domain_active_id,
                    'context': btn_ctx,
                })

        return new_button_field.name, btn_act.id

    @http.route('/web/default_value', type='json', auth="user")
    def set_or_get_default_value(self, options):
        if options.get('op') == 'set':
            request.env['ir.default'].set(options.get('model'),
                                          options.get('field_name'),
                                          options.get('value'),
                                          company_id=True)
        else:
            return request.env[options.get('model')]. \
                default_get([options.get('field_name')])

    @http.route('/web/update_view', type='json', auth="user")
    def update_view(self, options=None):
        base_view = request.env['ir.ui.view'].search(
            [('id', '=', int(options.get('view_id')))], limit=1)
        model = base_view.model
        view_type = base_view.type
        app_builder_xml = request.env['ir.ui.view'].search(
            [('inherit_id', '=', int(options.get('view_id'))),
             ('name', 'ilike', '%Flectra%App%Builder%Customization%')],
            limit=1)
        arch = None
        IrModelFields = request.env['ir.model.fields']

        if options.get('tag_operation') == 'field':
            field = IrModelFields.search([
                ('name', '=', options.get('field_name')),
                ('model', '=', model),
            ], limit=1)
            if field or options.get('field_name') == 'form':
                arch = self.field_arch(options.get('field_name'),
                                       options.get('xpath_field'),
                                       options.get('pos'),
                                       options.get('attr_name'),
                                       options.get('tab_string'))
            else:
                self.add_db_new_field(options, model)
                arch = self.field_arch(options.get('field_name'),
                                       options.get('xpath_field'),
                                       options.get('pos'),
                                       options.get('attr_name'),
                                       options.get('tab_string'))
        elif options.get('tag_operation') == 'page':
            if options.get('group_name'):
                arch = self.page_arch(None, None,
                                      options.get('group_name'),
                                      options.get('field_name'),
                                      options.get('tab_name'),
                                      options.get('pos'),
                                      None)
            elif options.get('tab_name'):
                xpath_str = "//notebook[" + str(
                    options.get('notebook_id')
                ) + "]/page[last()][not(ancestor::field)]"
                arch = self.page_arch(options.get('group_id'),
                                      xpath_str, None,
                                      None,
                                      options.get('tab_string'),
                                      options.get('pos'),
                                      None)
            if options.get('pos') == 'replace':
                if options.get('total_page') == 0:
                    xpath_str = "//notebook[" + \
                                str(options.get('notebook_id')) + "]"
                    arch = self.page_arch(None,
                                          xpath_str,
                                          None, None, None,
                                          options.get('pos'),
                                          None)
                else:
                    xpath_str = "//page[@name='" + \
                                options.get('field_name') + "']"
                    arch = self.page_arch(None,
                                          xpath_str, None, None,
                                          None, options.get('pos'),
                                          None)
            if options.get('pos') == 'attributes':
                xpath_str = "//page[@name='" + \
                            options.get('field_name') + \
                            "'][not(ancestor::field)]"
                arch = self.page_arch(None, xpath_str,
                                      None, None,
                                      options.get('tab_string'),
                                      options.get('pos'),
                                      options.get('attr_name'))

        elif options.get('tag_operation') == 'notebook':
            expr = "//sheet[last()]"
            arch = self.notebook_arch(options.get('group_id'),
                                      expr, options.get('pos'),
                                      'New Page',
                                      options.get('tag_operation'))

        elif options.get('tag_operation') == 'calendar':
            expr = "//calendar[not(ancestor::field)]"
            arch = self.calendar_view(expr,
                                      options.get('pos'),
                                      options.get('attr_name'),
                                      str(options.get('attr_value')))
        elif options.get('tag_operation') == 'pivot':
            expr = "//pivot[not(ancestor::field)]"
            arch = self.calendar_view(expr, options.get('pos'),
                                      options.get('attr_name'),
                                      str(options.get('attr_value')))
        elif options.get('tag_operation') == 'gantt':
            expr = "//gantt[not(ancestor::field)]"
            arch = self.calendar_view(expr,
                                      options.get('pos'),
                                      options.get('attr_name'),
                                      str(options.get('attr_value')))

        elif options.get('tag_operation') == 'add_button':
            expr = "//div[contains(@class,'oe_button_box')]" \
                   "[not(ancestor::field)]"

            data = self.create_action_button(model,
                                             options.get('rel_id'),
                                             options.get('btn_name'))

            arch = self.add_button(expr, options.get('pos'),
                                   options.get('icon'),
                                   data[0],
                                   str(data[1]),
                                   options.get('btn_name'))

        return self.create_app_builder_view(app_builder_xml, arch,
                                            model, options, view_type)

    def create_app_builder_view(self, app_builder_xml, arch,
                                model, options, view_type):
        if app_builder_xml:
            xml = etree.fromstring('<?xml version="1.0"?><data></data>')
            old_xml = etree.fromstring(app_builder_xml.arch_db)
            old_xml_child = old_xml.findall("./")
            for node in old_xml_child:
                xml.append(node)
            new_xml = etree.fromstring(arch)
            new_xml_child = new_xml.findall(".")
            for node in new_xml_child:
                xml.append(node)
            new_arch = etree.tostring(xml)
            app_builder_xml.sudo().with_context({'app_builder': True}).write({
                'arch_db': new_arch,
            })
        else:
            arch = '<?xml version="1.0"?><data>' + str(arch) + '</data>'
            request.env['ir.ui.view'].sudo().with_context(
                {'app_builder': True}).create(
                {
                    'type': view_type,
                    'model': model,
                    'inherit_id': options['view_id'],
                    'mode': 'extension',
                    'priority': 9999,
                    'arch_base': arch,
                    'name': "Flectra App Builder Customization",
                })

    @http.route('/web/update_list_view',
                type='json', auth="user")
    def update_list_view(self, options=None):

        base_view_id = request.env['ir.ui.view'].search(
            [('id', '=', int(options.get('view_id')))], limit=1)
        model = base_view_id.model
        view_type = base_view_id.type
        app_builder_xml = request.env['ir.ui.view'].search(
            [('inherit_id', '=', int(options.get('view_id'))),
             ('name', 'ilike', '%Flectra%app_builder%Customization%')],
            limit=1)
        IrModelFields = request.env['ir.model.fields']
        arch = None
        print('====',options)
        if options.get('tag_operation') == 'add_field':
            field = IrModelFields.search([
                ('name', '=', options.get('field_name')),
                ('model', '=', model),
            ], limit=1)
            if field:
                arch = self.field_arch(options.get('field_name'),
                                       options.get('xpath_field_name'),
                                       'before', '', '')
            else:
                self.add_db_new_field(options, model)
                arch = self.field_arch(options.get('field_name'),
                                       options.get('xpath_field_name'),
                                       'before', '', '')
        elif options.get('tag_operation') == 'delete_field':
            arch = self.field_arch(options.get('xpath_field_name'),
                                   '', 'replace', '', '')

        elif options.get('tag_operation') == 'change_field_attrs':
            arch = self.field_arch(options.get('xpath_field_name'),
                                   '', 'attributes',
                                   options.get('attr_type'),
                                   str(options.get('attr_value')))

        return self.create_app_builder_view(app_builder_xml, arch, model,
                                            options, view_type)

    @http.route('/web/update_search_view', type='json',
                auth="user")
    def update_search_view(self, options=None):

        base_view_id = request.env['ir.ui.view'].search(
            [('id', '=', int(options.get('view_id')))], limit=1)
        model = base_view_id.model
        view_type = base_view_id.type
        app_builder_xml = request.env['ir.ui.view'].search(
            [('inherit_id', '=', int(options.get('view_id'))),
             ('name', 'ilike', '%Flectra%app_builder%Customization%')],
            limit=1)

        arch = None

        if options.get('tag_operation') == 'add_field':
            arch = self.field_arch(options.get('field_name'),
                                   options.get('xpath_field_name'),
                                   options.get('pos'), '', '')

        if options.get('tag_operation') == 'add_group':
            arch = self.group_by_arch(options.get('expr'),
                                      options.get('field_name'),
                                      options.get('xpath_field_name'),
                                      options.get('pos'),
                                      options.get('attributes'),
                                      options.get('tag_operation'))
        if options.get('tag_operation') == 'add_filter' \
                or options.get('tag_operation') == 'add_separator':
            arch = self.group_by_arch(options.get('expr'),
                                      options.get('field_name'),
                                      None,
                                      options.get('pos'), None,
                                      options.get('tag_operation'))
        if options.get('tag_operation') == 'attributes':
            arch = self.set_search_view_attr(options.get('expr'),
                                             options.get('value'),
                                             options.get('pos'),
                                             options.get('attrfor'),
                                             options.get('attr_name'))

        return self.create_app_builder_view(app_builder_xml, arch,
                                            model, options, view_type)

    @http.route('/web/create_new_app', type='json',
                auth='user')
    def create_new_app(self, data=None, attachment_id=None, is_app=False,
                       group_id=None):
        attachment = request.env['ir.attachment'].browse(attachment_id)
        app_name = data[0]
        menu_name = data[1]
        icon = data[2]
        category = data[3]
        ver = data[4]
        desc = data[5]
        licence = data[6]
        is_binary_icon = data[7]

        if is_app:
            reborn_obj_name = 'x_' + menu_name
            reborn_app_name = app_name
            app_data = request.env['app.creator.data']
            app_data.create(
                {'app_name': reborn_app_name,
                 'author': request.env.user.name,
                 'obj_name': reborn_obj_name,
                 'description': desc, 'version': ver, 'category': category,
                 'licence': licence})
            model = request.env['ir.model'] \
                .with_context({'app_builder': True}).model_create(menu_name)
            if model:
                model_name = model.model
                request.env[model_name].with_context({'app_builder': True}) \
                    .create(
                    {'x_name': 'Demo Name'})

                action_obj = self.create_action(menu_name, model_name)
                d = {
                    'name': app_name.title().replace('_', ' '),
                    'child_id': [(0, 0, {
                        'name': menu_name.title().replace('_', ' '),
                        'action': action_obj['action_ref']
                    })]
                }

                views = self._get_app_builder_default_arch_view(
                    model_name, group_id)
                for i in views:
                    v = request.env[
                        'ir.actions.act_window.view'].create(
                        {'view_mode': i.type,
                         'act_window_id': action_obj['action_obj'].id})
                    v.view_id = i.id

                if is_binary_icon:
                    d['web_icon_data'] = attachment.datas
                elif icon and len(icon) == 3:
                    d['web_icon'] = ','.join(icon)

                reborn_context = dict(request.context)
                reborn_context.update({'app_builder': True})
                reborn_context.update({
                    'ir.ui.menu.full_list': True})
                reborn_menu = request.env['ir.ui.menu'].with_context(
                    reborn_context).create(d)

                return {
                    'menu_id': reborn_menu.id,
                    'action_id': action_obj['action_obj'].id,
                    'model_name': model_name
                }

    def create_form_arch(self, string, field_name, group_id):
        form = etree.Element('form')
        sheet = etree.Element('sheet')
        sheet.set('string', string)
        form.append(sheet)
        button_box = etree.Element('div')
        button_box.set('class', 'oe_button_box')
        button_box.set('name', 'button_box')
        sheet.append(button_box)
        div = etree.Element('div')
        div.set('class', 'oe_title')
        sheet.append(div)
        h1 = etree.Element('h1')
        field = etree.Element('field')
        field.set('name', field_name)
        field.set('modifier', '{required:True}')
        h1.append(field)
        div.append(h1)
        group = etree.Element('group')
        group.set('name', group_id)
        group_l = etree.Element('group')
        group_l.set('name', 'app_builder_group' + group_id + '_left')
        field_id = etree.Element('field')
        field_id.set('name', 'id')
        group_l.append(field_id)
        group_r = etree.Element('group')
        group_r.set('name', 'app_builder_group' + group_id + '_right')
        field_d = etree.Element('field')
        field_d.set('name', 'display_name')
        group_r.append(field_d)
        group.append(group_l)
        group.append(group_r)
        sheet.append(group)
        return etree.tostring(form)

    def _get_app_builder_default_arch_view(self, model_name, group_id):
        views = ['tree', 'form']
        view_arch = []
        for i in views:
            arch = \
                request.env[model_name].fields_view_get(
                    False, i)['arch']

            if i == 'form':
                root = etree.fromstring(arch)
                field = root.findall('.//field')
                sheet = root.findall('.//sheet')
                sheet_string = sheet[0].attrib['string']
                field_name = field[0].attrib['name']
                arch = self.create_form_arch(sheet_string,
                                             field_name, group_id)

            view = request.env['ir.ui.view'].with_context(
                {'app_builder': True}).create(
                {
                    'type': i,
                    'model': model_name,
                    'arch': arch,
                    'name': "Default %s view for %s" % (i, model_name),
                })

            view_arch.append(view)
        return view_arch

    def create_action(self, menu_name, model_name):
        action = request.env['ir.actions.act_window'].with_context(
            {'app_builder': True}).create(
            {
                'name': menu_name.title().replace('_', ' '),
                'res_model': model_name,
                'help': """
                    <p>
                        Generated Action Has a Default list & form view.
                    </p>
                    <p>
                        You can start modifying these views
                        with the help of app builder.
                    </p>
                """
            })
        action_ref = 'ir.actions.act_window,' + str(action.id)
        return {'action_obj': action, 'action_ref': action_ref}

    @http.route('/web/get_model', type='json', auth='user')
    def get_web_action(self, model):
        model = request.env['ir.model'].search(
            [('model', '=', model)], limit=1)
        return {
            'id': model.id,
            'model': model.model
        }

    @http.route('/web/create_report_from_xml',
                type='json', auth='user')
    def create_report(self, db_model, xml):
        model = request.env['ir.model'].search([('model',
                                                 '=', db_model)])

        fields = request.env['ir.model.fields'].search(
            [('model', '=', db_model), ('ttype', 'in',
                                        ['char', 'text', 'integer'])],
            limit=10)
        if xml == 'blank_report':
            arch_db = self.blank_report_arch()
        else:
            arch_db = self.commercial_report_arch(fields)
        ir_view = request.env['ir.ui.view'].with_context(
            {'app_builder': True}).create(
            {'name': 'report',
             'arch': arch_db,
             'type': 'qweb', })
        _view = ir_view.get_external_id()[ir_view.id]
        ir_view.name = _view
        ir_view.key = _view

        # Create report
        report_dat = {
            'model': model.model,
            'name': _(model.name + ' Report'),
            'report_name': ir_view.name,
            'report_type': 'qweb-pdf',
        }
        report = request.env['ir.actions.report'].with_context(
            {'app_builder': True}).create(
            report_dat)

        report.create_action()
        return {'report_id': report.id, 'view_id': ir_view.id}

    def commercial_report_arch(self, fields):
        p_tag = ""
        for field in fields:
            desc = field.field_description
            name = field.name
            p_tag = p_tag + """<p>
            <b>""" + desc + """: </b>
                <span t-field = "o.""" + name + """"/>
            </p>"""
        xml = """
                <t t-name="report_commercial">
                    <t t-call="web.html_container">
                        <t t-foreach="docs" t-as="o">
                            <t t-call="web.external_layout">
                                <div class="page">
                                    <div class="row">
                                        <h2>
                                            <strong>
                                                <span t-field="o.display_name"/>
                                            </strong>
                                        </h2>
                                        """ + p_tag + """
                                    </div>
                                </div>
                            </t>
                        </t>
                    </t>
                </t>
                """
        arch = etree.fromstring(xml)
        return etree.tostring(arch, encoding='utf-8', pretty_print=True)

    def blank_report_arch(self):
        xml = """<t t-name="report_blank">
                        <t t-call="web.html_container">
                            <t t-foreach="docs" t-as="o">
                                <t t-call="web.external_layout">
                                    <div class="page"/>
                                </t>
                            </t>
                        </t>
                    </t>
                """
        arch = etree.fromstring(xml)
        return etree.tostring(arch, encoding='utf-8', pretty_print=True)

    @http.route('/web/generate_report_action', type='json',
                auth='user')
    def generate_report_action(self, id, config):
        report = request.env['ir.actions.report'].browse(id)
        if report:
            if 'groups_id' in config:
                config['groups_id'] = list(list(map(int, config['groups_id']
                                                    .split(',')
                                                    )))
                config['groups_id'] = [(6, 0, config['groups_id'])]
            if 'ir_values_id' in config:
                if config['ir_values_id']:
                    report.create_action()
                else:
                    report.unlink_action()
                config.pop('ir_values_id')
            report.write(config)

    @http.route('/web/set_update_action', type='json',
                auth='user')
    def set_update_action(self, type, id, attrs):
        action = request.env[type].browse(id)
        if action:
            if 'groups_id' in attrs:
                attrs['groups_id'] = [
                    (6, 0, list(list(map(int, attrs['groups_id'].split(',')
                                         )
                                     )
                                )
                     )
                ]
            action.write(attrs)
            return True

    @http.route('/web/check_obj_name', type='json',
                auth='user')
    def check_obj_name(self, model_name):
        model = request.env['ir.model'].search(
            [('model', '=', 'x_' + model_name)])
        if model:
            return True
        else:
            return False

    @http.route('/web/activate_new_view', type='json',
                auth='user')
    def activate_new_view(self, action_type, action_id, model,
                          view_t, view_mode, options):
        view = view_t
        if view_t == 'list':
            view = 'tree'

        if view == 'calendar' or view == 'pivot' \
                or view == 'graph' or view == 'gantt':
            self.create_def_view(view, model, options)
        else:
            try:
                request.env[model].fields_view_get(view_type=view)
            except UserError as e:
                return e.name
        action = request.env[action_type].browse(action_id)
        view_modes = view_mode.split(',')
        view_modes[view_modes.index('list')] = 'tree'
        if action.view_ids:
            aid = request.env['ir.actions.act_window.view'].create(
                {'view_mode': view, 'act_window_id': action.id})
            for id in action.view_ids:
                if id.view_mode in view_modes:
                    id.sequence = view_modes.index(id.view_mode)
                else:
                    id.unlink()
            action.write({'view_mode': ",".join(view_modes)})
            return True

    def create_def_view(self, view_type, model, options):
        options['string'] = "Default %s view for %s" % (view_type, model)
        arch = self.obtain_default_view(view_type, options)
        request.env['ir.ui.view'].with_context({'app_builder': True}).create({
            'type': view_type,
            'model': model,
            'arch': arch,
            'name': options['string'],
        })

    def obtain_default_view(self, type, options):
        from_xml = etree.Element(type, options)
        return etree.tostring(from_xml, encoding='utf-8',
                              pretty_print=True, method='html')

    @http.route('/web/get_background', type='json',
                auth='user')
    def get_background(self, file_name, base_64_data):
        Model = request.env['ir.attachment']
        ir_attachment = Model.create({
            'name': file_name,
            'datas': base_64_data,
            'datas_fname': file_name,
            'res_model': 'res.company',
            'res_id': int(1)
        })
        attachment = request.env['ir.attachment'].browse(ir_attachment.id)
        if attachment:
            return attachment.id

    def get_xml_id(self, record):
        cache = {}
        rec = record.browse(record._prefetch[record._name])
        for rid, val in rec.get_external_id().items():
            cache[rec.browse(rid)] = val
        return cache

    @http.route('/web/export_from_app_builder',
                type='http', auth='user')
    def export_from_app_builder(self, data, token):
        app_data_id = json.loads(data)[4]
        app_builder = request.env['ir.module.module'] \
            .search([('name', '=', 'web')])
        ir_model_data = request.env['ir.model.data'] \
            .search(
            [('is_app_builder', '=', True),
             ('app_data_id', '=', int(app_data_id))])
        app_model_data = request.env['app.creator.data'] \
            .search(
            [('id', '=', int(app_data_id))])
        zip_data_content = self.archieve_content(app_builder, ir_model_data,
                                                 data,
                                                 app_model_data)
        return request.make_response(zip_data_content, headers=[
            ('Content-Disposition', content_disposition(
                app_model_data.app_name + '.zip')),
            ('Content-Type', 'application/zip'),
            ('Content-Length', len(zip_data_content)),
        ], cookies={'fileToken': token})

    def archieve_content(self, module, ir_model_data, data, app_data):
        mf = io.BytesIO()
        generator = self.make_manifest(module, ir_model_data, data, app_data)
        with zipfile.ZipFile(mf, mode='w',
                             compression=zipfile.ZIP_DEFLATED) as zf:
            for i in generator:
                file_name = i[0]
                file_content = i[1]
                zf.writestr(os.path.join('web', file_name),
                            file_content)
        return mf.getvalue()

    def make_manifest(self, module, ir_model_data, data, app_data):
        depends = []
        files = []
        SEQ_MODEL = json.loads(data)[0].get('SEQ_MODEL')
        WHITELIST_FIELDS = json.loads(data)[1]
        CDATA_FIELDS = json.loads(data)[2].get('CDATA_FIELDS')
        XML_FIELDS = json.loads(data)[3].get('XML_FIELDS')

        for i in SEQ_MODEL:
            model_data = ir_model_data.filtered(lambda r: r.model == i)
            records = ir_model_data.env[i].browse(
                model_data.mapped('res_id')).exists()
            field_names = records._fields
            deps = OrderedDict.fromkeys(records, records.browse())
            self.find_dependent_module(depends, records, field_names, module)
            yield self.make_nodes_xml(
                files, i, deps, WHITELIST_FIELDS, CDATA_FIELDS, XML_FIELDS)
        depends = set(depends)
        __manifest__ = """# -*- coding: utf-8 -*-
{{
    'name': '{}',
    'version': '{}',
    'category': '{}',
    'description': {},
    'author': '{}',
    'depends': [{}
    ],
    'data': [{}
    ],
    'application': {},
    'license': '{}'
}}
""".format(
            app_data.app_name,
            app_data.version,
            app_data.category,
            'u"""\n{}\n"""'.format(app_data.description),
            app_data.author,
            ''.join("\n        '{}',".format(d) for d in sorted(depends)),
            ''.join("\n        '{}',".format(f) for f in files),
            'True',
            app_data.licence)
        __manifest__ = __manifest__.encode('utf-8')
        yield ('__manifest__.py', __manifest__)
        yield ('__init__.py', b'')

    def make_nodes_xml(self, files, model, deps,
                       WHITELIST_FIELDS, CDATA_FIELDS, XML_FIELDS):
        sorted_rec = topological_sort(deps)
        root = []
        for xml_rec in sorted_rec:
            rec_node = self.get_xml_rec(
                xml_rec, WHITELIST_FIELDS, CDATA_FIELDS, XML_FIELDS)
            root.append(rec_node)
        xml_data = E.flectra(*root)
        fnam = os.path.join('data', '%s.xml' % model.replace('.', '_'))
        files.append(fnam)
        return (fnam, etree.tostring(
            xml_data, pretty_print=True,
            encoding='UTF-8', xml_declaration=True))

    def find_dependent_module(self, depends, records, field_names, module):
        for record in records:
            for name in field_names:
                field = records._fields[name]
                rel_records = self.render_xml_relation_field(record, field)
                if not rel_records:
                    continue
                for rel_record in rel_records:
                    cache = self.get_xml_id(rel_record)
                    dependable = cache[rel_record].split('.')[0]
                    if dependable != module.name:
                        if dependable != '':
                            depends.append(dependable)

    def get_ir_model_fields_for_xml(self, xml_rec, xml_field):
        if xml_field.name in ('depends', 'related'):
            deps = set()
            for name in xml_rec[xml_field.name].split(','):
                model = xml_rec.env[xml_rec.model]
                for n in name.strip().split('.'):
                    field = model._fields[n]
                    if not field.automatic:
                        deps.add(field)
                    if field.relational:
                        model = xml_rec.env[field.comodel_name]
            if deps:
                return xml_rec.search(OR([
                    ['&', ('model', '=', field.model_name),
                     ('name', '=', field.name)]
                    for field in deps
                ]))
        elif xml_field.name == 'relation_field':
            return xml_rec.search([('model', '=', xml_rec.relation),
                                   ('name', '=', xml_rec.relation_field)])

    def get_xml_field(self, record, field, id,
                      WHITELIST_FIELDS, CDATA_FIELDS, XML_FIELDS):
        value = record[field.name]
        if field.type == 'boolean':
            node = etree.Element('field')
            node.set('name', field.name)
            node.set('eval', pycompat.text_type(value))
            return node

        elif field.type in ('many2one', 'reference'):
            if value and value._name not in [
                'ir.model.data', 'res.users', 'ir.actions.act_window.view'
            ]:
                cache = self.get_xml_id(value)
                ref = cache[value]
                node = etree.Element('field')
                node.set('name', field.name)
                node.set('ref', ref)
                return node
            else:
                node = etree.Element('field')
                node.set('name', field.name)
                node.set('eval', u"False")
                return node

        elif field.type in ('many2many', 'one2many'):
            if field.name in WHITELIST_FIELDS[field.model_name]:
                if value and value._name not in ['ir.model.data', 'res.users',
                                                 'ir.actions.act_window.view']:
                    cache = self.get_xml_id(value)
                    temp_lst = []
                    ev = '[(6, 0, %s)]'
                    for v in value:
                        if cache[v]:
                            temp_lst.append("ref('%s')" % (cache[v]))
                    eval = ev % (temp_lst)
                    node = etree.Element('field')
                    node.set('name', field.name)
                    node.set('eval', eval)
                    return node

        else:
            if not value:
                node = etree.Element('field')
                node.set('name', field.name)
                node.set('eval', u"False")
                return node
            elif (field.model_name, field.name) in CDATA_FIELDS:
                node = etree.Element('field')
                node.set('name', field.name)
                node.text = etree.CDATA(pycompat.text_type(value))
                return node
            elif (field.model_name, field.name) in XML_FIELDS:
                parser = etree.XMLParser(remove_blank_text=True)
                return E.field(etree.XML(value, parser), name=field.name,
                               type='xml')
            else:
                node = etree.Element('field')
                node.set('name', field.name)
                node.text = pycompat.text_type(value)
                return node

    def render_xml_relation_field(self, xml_rec, xml_field):
        if not xml_rec[xml_field.name]:
            return

        if xml_field.type in (
                'one2many', 'many2many', 'many2one', 'reference'):
            return xml_rec[xml_field.name]

        if xml_field.model_name == 'ir.actions.act_window' and xml_field.name in \
                ('res_model', 'src_model'):
            return xml_rec.env['ir.model'].search(
                [('model', '=', xml_rec[xml_field.name])])

        if xml_field.model_name == 'ir.actions.report' and xml_field.name == 'model':
            return xml_rec.env['ir.model'].search(
                [('model', '=', xml_rec.model)])

        if xml_field.model_name == 'ir.model.fields':
            return self.get_ir_model_fields_for_xml(xml_rec, xml_field)

    def get_xml_rec(self, record, WHITELIST_FIELDS, CDATA_FIELDS, XML_FIELDS):
        for rid in record.get_external_id().items():
            id = rid[1]
            node = etree.Element('record')
            node.set('id', id)
            node.set('model', record._name)
            node.set('context', "{'app_buider': True}")
            field_name = record._fields
            for name in field_name:
                field = record._fields[name]
                xml_field = self.get_xml_field(
                    record, field, id, WHITELIST_FIELDS,
                    CDATA_FIELDS, XML_FIELDS)
                if xml_field is not None:
                    node.append(xml_field)
            return node
