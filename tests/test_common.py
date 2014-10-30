import unittest

import json
from os.path import join
from jsonschema import ValidationError,Draft4Validator

from manuallabour.core.common import *

SCHEMA_DIR = 'tests/schema'

class JSONTest(unittest.TestCase):
    def test_noref(self):
        self.assertEqual(
            load_schema(SCHEMA_DIR,'noref.json'),
            json.loads(open(join(SCHEMA_DIR,'noref.json')).read())
        )

    def test_ref(self):
        self.assertEqual(
            load_schema(SCHEMA_DIR,'noref.json'),
            load_schema(SCHEMA_DIR,'ref.json')
        )
    def test_nested(self):
        schema = load_schema(SCHEMA_DIR,'nested.json'),
        self.assertTrue("required" in schema[0]["properties"]["neighbour"])
    def test_oneOf(self):
        schema = load_schema(SCHEMA_DIR,'OneOf.json'),
        self.assertTrue("required" in schema[0]["properties"]["state"]["oneOf"][1])

class DataStructTest(DataStruct):
    _schema = {"type" : "object",
        "properties" : {
            "name" : {"type" : "string"},
            "description" : {"type" : "string","default" : ""}
        },
        "required" : ["name"]
    }
    _validator = jsonschema.Draft4Validator(_schema,)
    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)
        self._calculated["title"] = self.name.title()

class TestDataStruct(unittest.TestCase):
    def test_init(self):
        a = DataStructTest(name="Test")
        self.assertRaises(ValidationError,lambda: DataStructTest(mame="Test"))
        self.assertRaises(ValidationError,lambda: DataStructTest())
        self.assertRaises(ValidationError,lambda: DataStructTest(name=4))

    def test_defaults(self):
        a = DataStructTest(name="Test")
        self.assertEqual(a.description,"")

        b = DataStructTest(name="Test",description="foo")
        self.assertEqual(b.description,"foo")

    def test_calculated(self):
        a = DataStructTest(name="foo")
        self.assertEqual(a.title,"Foo")


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
        Object(obj_id='foo',name="Bar")
        self.assertRaises(ValidationError,lambda: Object(obj_id='foo'))
        self.assertRaises(ValidationError,
            lambda: Object(obj_id='*asd*',name="foo")
        )
    def test_default(self):
        o = Object(obj_id='foo',name="Bar")
        self.assertEqual(o.description,"")
        self.assertEqual(o.images,[])


    def test_image(self):
        o = Object(obj_id='foo',name="Bar",images=[
            ResourceReference(res_id='asdf')
        ])
        self.assertEqual(len(o.images),1)

class TestReferences(unittest.TestCase):
    def test_obj_ref(self):
        self.assertRaises(ValidationError,lambda: ObjectReference(obj_id='*'))

        obr = ObjectReference(obj_id='nut')
        self.assertEqual(obr.optional,False)
        self.assertEqual(obr.quantity,1)

        obr = ObjectReference(obj_id='nut',quantity=2,optional=True)
        self.assertEqual(obr.optional,True)
        self.assertEqual(obr.quantity,2)

    def test_res_ref(self):
        self.assertRaises(ValidationError,
            lambda: ResourceReference(res_id='*')
        )

        res = ResourceReference(res_id='nut')

    def test_bom_ref(self):
        self.assertRaises(ValidationError,lambda: BOMReference(obj_id='*'))

        bom = BOMReference(obj_id='nut')
        self.assertEqual(bom.optional,0)
        self.assertEqual(bom.quantity,1)

