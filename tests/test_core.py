import unittest
from datetime import timedelta

from jsonschema import ValidationError

from manuallabour.core import *

class TestStep(unittest.TestCase):
    def test_BaseStep(self):
        StepBase('a')
        self.assertRaises(ValueError,lambda: StepBase('9'))

    def test_GraphStep(self):
        self.assertRaises(ValidationError,lambda: GraphStep('a'))
        self.assertRaises(ValueError,lambda: GraphStep('9'))

        params = {'title' : 'TestStep', 'description' : 'asd'}
        step = GraphStep('a',**params)

        params['parts'] = [ObjectReference('nut')]

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

class TestObjRefs(unittest.TestCase):
    def test_init(self):
        obr = ObjectReference('nut')
        self.assertEqual(obr.optional,False)
        self.assertEqual(obr.quantity,1)
        obr = ObjectReference('nut',quantity=2,optional=True)
        self.assertEqual(obr.optional,True)
        self.assertEqual(obr.quantity,2)

class TestGraph(unittest.TestCase):
    def test_add_steps(self):
        g = Graph()

        params = {'title' : 'TestStep', 'description' : 'asd'}
        g.add_step(GraphStep('a',**params),[])
        g.add_step(GraphStep('b',**params),['a'])
        self.assertRaises(KeyError, lambda:
            g.add_step(GraphStep('a',**params),[])
        )

        self.assertEqual(g.children['a'],['b'])
        self.assertEqual(g.parents['b'],['a'])

    def test_timing(self):
        g = Graph()

        params = {'title' : 'TS', 'description' : ''}
        params['duration'] = timedelta(minutes=4)
        g.add_step(GraphStep('a',**params),[])
        self.assertTrue(g.timing)

        params.pop('duration')
        g.add_step(GraphStep('b',**params),['a'])
        self.assertFalse(g.timing)

    def test_add_objects(self):
        g = Graph()

        g.add_object(Object('a',name="Nut"))
        g.add_object(Object('b',name="Wrench"))

        s = GraphStep('b',
            title='With objects',
            description='Step with objects',
            parts = {'nut' : ObjectReference('nut')},
            tools = {'wr' : ObjectReference('wrench')}
        )

        g.add_step(s,[])

    def test_add_resources(self):
        g = Graph()

        g.add_resource(Image('wds',alt="foo",extension=".png"))
        self.assertRaises(KeyError,
            lambda: g.add_resource(File('wds',filename="foo"))
        )
        g.add_resource(File('kds',filename="foo"))

        s = GraphStep('b',
            title='With objects',
            description='Step with objects',
            files = {'l_kds' : ObjectReference('kds')},
            images = {'l_wds' : ObjectReference('wds')}
        )

        g.add_step(s,[])


    def test_graph(self):
        g = Graph()

        g.add_object(Object('nut',name="Nut"))
        g.add_object(Object('b',name="Wrench"))

        g.add_resource(Image('wds',alt="foo",extension=".png"))
        g.add_resource(File('kds',filename="foo"))

        g.add_step(GraphStep('a',
            title='First Step',
            description='Do this',
            parts = {'nut' : ObjectReference('nut',optional=True)},
            images = {'res1' : ResourceReference('wds')}
        ),[])
        g.add_step(GraphStep('b',
            title='Second Step',
            description='Do that',
            parts = {'nut' : ObjectReference('nut',quantity=2)},
            tools = {'wr' : ObjectReference('b',)},
            files = {'res2' : ResourceReference('kds')}
        ),['a'])

        g.to_svg('tests/output/test.svg')


