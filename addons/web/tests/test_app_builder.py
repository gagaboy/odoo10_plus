from flectra.tests.common import TransactionCase
from flectra.http import _request_stack
from flectra.addons.web.controllers.builder.main import \
    FlectraAppBuilder


class AppBuilderTest(TransactionCase):

    def setUp(self):
        super(AppBuilderTest, self).setUp()
        _request_stack.push(self)
        self.app_data = self.env['app.creator.data']
        self.app_builder_controller = FlectraAppBuilder()
        self.base_view = self.env.ref('base.view_partner_form')
        self.arch_base = self.base_view.arch_base
        self.view = self.base_view.create(
            {'arch_base': self.arch_base, 'model': 'res.partner'})
        self.builder = FlectraAppBuilder()

    def _test_app_builder(self, arch):
        arch = '<?xml version="1.0"?><data>' + str(arch) + '</data>'
        new_view = self.env['ir.ui.view'].sudo().with_context(
            {'app_builder': True}).create(
            {
                'type': 'form',
                'model': 'res.partner',
                'inherit_id': self.view.id,
                'mode': 'extension',
                'priority': 9999,
                'arch_base': arch,
                'name': "Flectra App Builder Customization",
            })

        self.assertEqual(arch, new_view.arch_base)

    # TEST1 : Add A field with xpath
    def test_app_builder_00(self):
        arch = """<xpath expr="//field[@name='phone'][not(ancestor::field)]" 
        position="after"><field name="barcode"/></xpath>"""
        self._test_app_builder(arch)

    # TEST2 : remove A field with xpath
    def test_app_builder_01(self):
        arch = """<xpath expr="//field[@name='phone'][not(ancestor::field)]" 
                position="after"><field name="barcode"/></xpath>
                <xpath expr="//field[@name='barcode'][not(ancestor::field)]" 
                position="replace"/>
                """
        self._test_app_builder(arch)

    # TEST3 : Adding A notebook page with xpath
    def test_app_builder_02(self):
        arch = """<data>
          <xpath expr="//notebook[1]/page[last()][not(ancestor::field)]"
           position="after">
           <page name="app_builder_group_lrl1" string="New Tab g5tk">
              <group name="app_builder_group_lrl1">
                 <group name="app_builder_group_lrl1_left" />
                 <group name="app_builder_group_lrl1_right" />
              </group>
           </page>
        </xpath>
        </data>"""
        self._test_app_builder(arch)

    # TEST4 : Rename A notebook page with xpath
    def test_app_builder_03(self):
        arch = """
        <xpath expr="//notebook[1]/page[last()][not(ancestor::field)]" 
        position="after">
           <page name="app_builder_group_lrl1" string="New Tab g5tk">
              <group name="app_builder_group_lrl1">
                 <group name="app_builder_group_lrl1_left" />
                 <group name="app_builder_group_lrl1_right" />
              </group>
           </page>
        </xpath>
        <xpath expr="//page[@name='app_builder_group_lrl1']
        [not(ancestor::field)]" position="attributes">
           <attribute name="string">New Page</attribute>
        </xpath>
        """
        self._test_app_builder(arch)

    # TEST5 : Replace A notebook page with xpath
    def test_app_builder_04(self):
        arch = """
        <xpath expr="//notebook[1]/page[last()][not(ancestor::field)]" 
        position="after">
                   <page name="app_builder_group_lrl1" string="New Tab g5tk">
                      <group name="app_builder_group_lrl1">
                         <group name="app_builder_group_lrl1_left"/>
                         <group name="app_builder_group_lrl1_right"/>
                      </group>
                   </page>
                </xpath>
                <xpath expr="//page[@name='app_builder_group_lrl1']
                [not(ancestor::field)]" position="attributes">
                   <attribute name="string">New Page</attribute>
                </xpath>  
        <xpath expr="//page[@name='app_builder_group_lrl1']" 
        position="replace"/>
        """
        self._test_app_builder(arch)

    # TEST6 : Add A notebook and add two fields with xpath
    def test_app_builder_05(self):
        arch = """
         <xpath expr="//sheet[last()]" position="inside">
          <notebook name="app_builder_group_mtd9">
             <page name="app_builder_group_mtd9" string="New Page">
                <group name="app_builder_group_mtd9">
                   <group name="app_builder_group_mtd9_left" />
                   <group name="app_builder_group_mtd9_right" />
                </group>
             </page>
          </notebook>
       </xpath>
       <xpath expr="//page[@name='app_builder_group_mtd9']
       [not(ancestor::field)]" position="attributes">
          <attribute name="string">Page 1</attribute>
       </xpath>
       <xpath expr="//group[@name='app_builder_group_mtd9_left']
       [not(ancestor::field)]" position="inside">
          <field name="color" />
       </xpath>
       <xpath expr="//group[@name='app_builder_group_mtd9_right']
       [not(ancestor::field)]" position="inside">
          <field name="barcode" />
       </xpath>
        """
        self._test_app_builder(arch)

    # TEST7 : Changing field String Attrs with xpath
    def test_app_builder_06(self):
        arch = """
         <xpath expr="//field[@name=&quot;phone&quot;][not(ancestor::field)]" 
         position="attributes">
           <attribute name="string">Phone Number</attribute>
        </xpath>
        """
        self._test_app_builder(arch)

    # TEST8 : Changing field Hint Attrs with xpath
    def test_app_builder_07(self):
        arch = """
         <xpath expr="//field[@name=&quot;phone&quot;][not(ancestor::field)]" 
         position="attributes">
           <attribute name="help">This is Phone Number Field.</attribute>
        </xpath>
        """
        self._test_app_builder(arch)

    # TEST9 : Changing field Placeholder Attrs with xpath
    def test_app_builder_08(self):
        arch = """
         <xpath expr="//field[@name=&quot;phone&quot;][not(ancestor::field)]" 
         position="attributes">
           <attribute name="placeholder">Phone number with special symbols 
           allowed.</attribute>
        </xpath>
        """
        self._test_app_builder(arch)

    # TEST10 : Changing field Widget Attrs with xpath
    def test_app_builder_09(self):
        arch = """
         <xpath expr="//field[@name=&quot;website&quot;][not(ancestor::field)]"
          position="attributes">
         <attribute name="widget">url</attribute>
         </xpath>
        """
        self._test_app_builder(arch)

    # TEST11 : Testing Default value of fields.
    def test_app_builder_10(self):
        options = {'op': 'set', 'model': 'res.partner',
                   'field_name': 'website',
                   'value': 'www.google.com'}
        self.builder.set_or_get_default_value(options)
        options = {'op': 'get', 'model': 'res.partner',
                   'field_name': 'website',
                   'value': 'www.google.com'}
        value = self.builder.set_or_get_default_value(options)
        self.assertEqual({'website': 'www.google.com'}, value)

    # TEST12 : Testing Custom Text Fields On View.
    def test_app_builder_11(self):
        options = {'field_type': 'text', 'field_name': 'x_crazy',
                   'label': 'Crazy'}
        self.builder.add_db_new_field(options, 'res.partner')
        arch = """
                 <xpath expr="//field[@name=&quot;phone&quot;]
                 [not(ancestor::field)]"
                  position="after">
                 <field name="x_crazy" />
                 </xpath>
                """
        self._test_app_builder(arch)

    # TEST13 : Testing Custom Selection Fields On View.
    def test_app_builder_12(self):
        options = {'field_type': 'selection',
                   'selection_list': [['0', 'Red'], ['1', 'Green'],
                                      ['2', 'Blue']],
                   'field_name': 'x_color_choices',
                   'label': 'Color Selection'}

        self.builder.add_db_new_field(options, 'res.partner')
        arch = """
                 <xpath expr="//field[@name=&quot;phone&quot;]
                 [not(ancestor::field)]"
                  position="after">
                 <field name="x_color_choices" />
                 </xpath>
                """
        self._test_app_builder(arch)
