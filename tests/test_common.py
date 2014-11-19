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

class MockStore(object):
    def get_blob_url(self,blob_id):
        return "http://url.com"
    def get_obj(self,obj_id):
        return Object(
            obj_id=obj_id,
            name="Testobject",
            images=[dict(blob_id="asd",alt="Foo",extension=".png")]
        )

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
        one = self.one.dereference(MockStore())
        self.assertEqual(one['name'],'Foo')
        self.assertEqual(one['description'],'')

        two = self.two.dereference(MockStore())
        self.assertEqual(two['name'],'Foo')
        self.assertEqual(two['description'],'Bar')

class TestReferences(unittest.TestCase):
    def test_file_ref(self):
        self.assertRaises(ValidationError,
            lambda: FileReference(blob_id='*'))
        self.assertRaises(ValidationError,
            lambda: FileReference(blob_id='bsd'))
        self.assertRaises(ValidationError,
            lambda: FileReference(blob_id='bsd',foo=2))

        f = FileReference(blob_id='asafb',filename="test.file")
        res = f.dereference(MockStore())
        self.assertEqual(res["url"],"http://url.com")
        self.assertEqual(res["filename"],"test.file")

    def test_image_ref(self):
        self.assertRaises(ValidationError,
            lambda: ImageReference(blob_id='*'))
        self.assertRaises(ValidationError,
            lambda: ImageReference(blob_id='sda'))
        self.assertRaises(ValidationError,
            lambda: ImageReference(blob_id='sda',foo=2))

        i = ImageReference(blob_id='a',alt='test image',extension='.png')
        res = i.dereference(MockStore())
        self.assertEqual(res["url"],'http://url.com')
        self.assertEqual(res["alt"],"test image")

    def test_object_ref(self):
        self.assertRaises(ValidationError,lambda: ObjectReference(obj_id='*'))

        obr = ObjectReference(obj_id='nut')
        self.assertEqual(obr.optional,False)
        self.assertEqual(obr.quantity,1)

        obr = ObjectReference(obj_id='nut',quantity=2,optional=True)
        self.assertEqual(obr.optional,True)
        self.assertEqual(obr.quantity,2)

        res = obr.dereference(MockStore())
        self.assertTrue("quantity" in res)
        self.assertTrue("optional" in res)
        self.assertEqual(res["images"][0]["url"],"http://url.com")

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
            dict(blob_id='asdf',extension=".png",alt="an image")
        ])
        self.assertEqual(len(o.images),1)

    def test_checksum(self):
        kwargs = dict(obj_id='foo',name="Bar")
        check1 = Object.calculate_checksum(**kwargs)

        kwargs['obj_id'] = 'Foo'
        self.assertEqual(check1,Object.calculate_checksum(**kwargs))

        kwargs['name'] = 'bar'
        check2 = Object.calculate_checksum(**kwargs)
        self.assertNotEqual(check1,check2)

        kwargs['description'] = 'Foobar'
        check3 = Object.calculate_checksum(**kwargs)
        self.assertNotEqual(check1,check3)
        self.assertNotEqual(check2,check3)

        kwargs['images'] = [dict(blob_id="asd",extension='.png',alt='Foobar')]
        check4 = Object.calculate_checksum(**kwargs)
        self.assertNotEqual(check1,check4)
        self.assertNotEqual(check2,check4)
        self.assertNotEqual(check3,check4)

    def tets_dereference(self):
        o = Object(obj_id='foo',name="Bar",images=[
            dict(blob_id='asdf',extension=".png",alt="an image")
        ])

        res = o.dereference(MockStore())

        self.assertEqual(res["name"],"Bar")
        self.assertEqual(res["images"][0]["alt"],"an image")
        self.assertEqual(res["images"][0]["url"],"http://url.com")

        self.assertTrue(isinstance(o.images[0],ImageReference))


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
            files = {'l_kds' : dict(blob_id='kds',filename='test.file')},
            images = {'l_wds' : dict(blob_id='ws',alt='Foo',extension='.png')}
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

    def test_checksum(self):
        kwargs = dict(step_id="asdf",title="Foobar",description="A foo step")
        check1 = Step.calculate_checksum(**kwargs)

        kwargs["step_id"] = 'bsdf'
        self.assertEqual(check1,Step.calculate_checksum(**kwargs))

        kwargs['title'] = 'foobar'
        check2 = Step.calculate_checksum(**kwargs)
        self.assertNotEqual(check1,check2)

        kwargs['description'] = 'A foobar step'
        check3 = Step.calculate_checksum(**kwargs)
        self.assertNotEqual(check1,check3)
        self.assertNotEqual(check2,check3)

        kwargs['assertions'] = ['take care']
        check4 = Step.calculate_checksum(**kwargs)
        self.assertNotEqual(check1,check4)
        self.assertNotEqual(check2,check4)
        self.assertNotEqual(check3,check4)

        kwargs['duration'] = dict(minutes=2,seconds=30)
        check5 = Step.calculate_checksum(**kwargs)
        self.assertNotEqual(check1,check5)
        self.assertNotEqual(check2,check5)
        self.assertNotEqual(check3,check5)
        self.assertNotEqual(check4,check5)

    def test_dereference(self):
        step = Step(
            step_id='b',
            title='With objects',
            description='Step with objects',
            files = {'l_kds' : dict(blob_id='kds',filename='test.file')},
            images = {'l_wds' : dict(blob_id='ws',alt='Foo',extension='.png')}
        )

        res = step.dereference(MockStore())

        self.assertEqual(res['step_id'],'b')
        self.assertEqual(res['files']['l_kds']["filename"],'test.file')
        self.assertEqual(res['files']['l_kds']["url"],'http://url.com')
