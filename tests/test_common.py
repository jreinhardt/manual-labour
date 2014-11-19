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
        self._calculated["name"] = self.name.title()

class TestDataStruct(unittest.TestCase):
    def setUp(self):
        self.one = DataStructTest(name="foo")
        self.two = DataStructTest(name="Foo",description="Bar")

    def test_init(self):
        self.assertRaises(ValidationError,lambda: DataStructTest(mame="Test"))
        self.assertRaises(ValidationError,lambda: DataStructTest())
        self.assertRaises(ValidationError,lambda: DataStructTest(name=4))

    def test_defaults(self):
        self.assertEqual(self.one.description,"")
        self.assertEqual(self.two.description,"Bar")

    def test_calculated(self):
        self.assertEqual(self.one.name,"Foo")

    def test_as_dict(self):
        one = self.one.as_dict()
        self.assertEqual(one['name'],'foo')
        self.assertFalse('description' in one)

        two = self.two.as_dict()
        self.assertEqual(two['name'],'Foo')
        self.assertTrue('description' in two)

    def test_dereference(self):
        one = self.one.dereference(None)
        self.assertEqual(one['name'],'Foo')
        self.assertEqual(one['description'],'')

        two = self.two.dereference(None)
        self.assertEqual(two['name'],'Foo')
        self.assertEqual(two['description'],'Bar')

class TestResources(unittest.TestCase):
    def test_File(self):
        f = File(res_id='asbd',blob_id='asafb',filename="test.file")
        self.assertEqual(f.res_id,'asbd')

        self.assertRaises(ValidationError,lambda: File(res_id='*'))

        self.assertRaises(ValidationError,lambda: File(res_id='bsd'))
        self.assertRaises(ValidationError,lambda: File(res_id='bsd',foo=2))

    def test_Image(self):
        i = Image(res_id='asbf',blob_id='a',alt='test image',extension='.png')
        self.assertEqual(i.res_id,'asbf')

        self.assertRaises(ValidationError,lambda: Image(res_id='*'))

        self.assertRaises(ValidationError, lambda: Image(res_id='sda'))
        self.assertRaises(ValidationError, lambda: Image(res_id='sda',foo=2))

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
            dict(res_id='asdf')
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

class TestStep(unittest.TestCase):
    def setUp(self):
        self.params = {
            'step_id' : 'a',
            'title' : 'TestStep',
            'description' : 'asd'
        }
    def test_init(self):
        self.assertRaises(ValidationError,lambda: Step(step_id='a'))
        self.assertRaises(ValidationError,lambda: Step(step_id='9'))

        step = Step(**self.params)
        self.assertEqual(step.title,"TestStep")

    def test_objects(self):
        self.assertRaises(
            ValidationError,
            lambda: Step(parts=[dict(obj_id='nut')],**self.params)
        )

        step = Step(
            parts = {
                'nut' : dict(obj_id='a'),
                'bolt' : dict(obj_id='c')
            },
            tools = {'wr' : dict(obj_id='b')},
            results = {'res' : dict(obj_id='d',created=True)},
            **self.params
        )

        self.assertEqual(len(step.parts),2)
        self.assertEqual(len(step.tools),1)
        self.assertEqual(len(step.results),1)

    def test_resources(self):
        step = Step(
            step_id='b',
            title='With objects',
            description='Step with objects',
            files = {'l_kds' : dict(res_id='kds')},
            images = {'l_wds' : dict(res_id='wds')}
        )

        self.assertEqual(len(step.files),1)
        self.assertEqual(len(step.images),1)

    def test_time(self):
        step = Step(duration=dict(minutes=5),**self.params)
        self.assertEqual(step.duration.total_seconds(),300)

        self.assertRaises(
            ValidationError,
            lambda: Step(waiting=21,**self.params)
        )

    def test_dict(self):
        step = Step(duration=dict(minutes=5),**self.params)
        data = step.as_dict()

        self.assertEqual(data,Step(**data).as_dict())
        self.assertTrue('step_id' in data)
        self.assertEqual(timedelta(**data['duration']).total_seconds(),300)
        self.assertEqual(data['title'],'TestStep')

        step = Step(waiting=dict(minutes=5),**self.params)
        data = step.as_dict()
        self.assertEqual(timedelta(**data['waiting']).total_seconds(),300)
