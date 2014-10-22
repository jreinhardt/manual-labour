import unittest

from jsonschema import ValidationError

from manuallabour.core.common import *

class TestResources(unittest.TestCase):
    def test_File(self):
        f = File('asbd',filename="test.file")
        self.assertEqual(f.res_id,'asbd')

        self.assertRaises(ValueError,lambda: File('*'))

        self.assertRaises(ValidationError,lambda: File('bsd'))
        self.assertRaises(ValidationError,lambda: File('bsd',foo=2))

    def test_Image(self):
        i = Image('asbf',alt='a test image',extension='.png')
        self.assertEqual(i.res_id,'asbf')

        self.assertRaises(ValueError,lambda: Image('*'))

        self.assertRaises(ValidationError, lambda: Image('sda'))
        self.assertRaises(ValidationError, lambda: Image('sda',foo=2))

class TestObjects(unittest.TestCase):
    def test_init(self):
        Object('eimer',name="Eimer")
        self.assertRaises(ValidationError,lambda:
            Object('eimer')
        )

    def test_image(self):
        o = Object('eimer',name="Eimer",images=[ResourceReference('asdf')])
        self.assertEqual(len(o.images),1)

class TestReferences(unittest.TestCase):
    def test_obj_ref(self):
        self.assertRaises(ValueError,lambda: ObjectReference('*'))

        obr = ObjectReference('nut')
        self.assertEqual(obr.optional,False)
        self.assertEqual(obr.quantity,1)

        obr = ObjectReference('nut',quantity=2,optional=True)
        self.assertEqual(obr.optional,True)
        self.assertEqual(obr.quantity,2)

    def test_res_ref(self):
        self.assertRaises(ValueError,lambda: ResourceReference('*'))

        res = ResourceReference('nut')

    def test_bom_ref(self):
        self.assertRaises(ValueError,lambda: BOMReference('*'))

        bom = BOMReference('nut')
        self.assertEqual(bom.optional,0)
        self.assertEqual(bom.quantity,1)

