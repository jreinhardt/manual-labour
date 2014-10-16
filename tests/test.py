import unittest
from datetime import timedelta

from jsonschema import ValidationError

import manuallabour

class TestStep(unittest.TestCase):
    def test_BaseStep(self):
        manuallabour.StepBase('a')
        self.assertRaises(ValueError,lambda: manuallabour.StepBase('9'))

    def test_GraphStep(self):
        self.assertRaises(ValidationError,lambda: manuallabour.GraphStep('a'))
        self.assertRaises(ValueError,lambda: manuallabour.GraphStep('9'))

        params = {'title' : 'TestStep', 'description' : 'asd'}
        step = manuallabour.GraphStep('a',**params)

        params['parts'] = [manuallabour.ObjectReference('nut')]

class TestObjects(unittest.TestCase):
    def test_init(self):
        manuallabour.Object('eimer',name="Eimer")
        self.assertRaises(ValidationError,lambda:
            manuallabour.Object('eimer')
        )

class TestObjRefs(unittest.TestCase):
    def test_init(self):
        obr = manuallabour.ObjectReference('nut')
        self.assertEqual(obr.optional,False)
        self.assertEqual(obr.quantity,1)
        obr = manuallabour.ObjectReference('nut',quantity=2,optional=True)
        self.assertEqual(obr.optional,True)
        self.assertEqual(obr.quantity,2)

class TestGraph(unittest.TestCase):
    def test_add_steps(self):
        g = manuallabour.Graph()

        params = {'title' : 'TestStep', 'description' : 'asd'}
        g.add_step(manuallabour.GraphStep('a',**params),[])
        g.add_step(manuallabour.GraphStep('b',**params),['a'])
        self.assertRaises(KeyError, lambda:
            g.add_step(manuallabour.GraphStep('a',**params),[])
        )

        self.assertEqual(g.children['a'],['b'])
        self.assertEqual(g.parents['b'],['a'])

    def test_timing(self):
        g = manuallabour.Graph()

        params = {'title' : 'TS', 'description' : ''}
        params['duration'] = timedelta(minutes=4)
        g.add_step(manuallabour.GraphStep('a',**params),[])
        self.assertTrue(g.timing)

        params.pop('duration')
        g.add_step(manuallabour.GraphStep('b',**params),['a'])
        self.assertFalse(g.timing)

    def test_add_objects(self):
        g = manuallabour.Graph()

        g.add_object(manuallabour.Object('a',name="Nut"))
        g.add_object(manuallabour.Object('b',name="Wrench"))

        s = manuallabour.GraphStep('b',
            title='With objects',
            description='Step with objects',
            parts = {'nut' : manuallabour.ObjectReference('nut')},
            tools = {'wr' : manuallabour.ObjectReference('wrench')}
        )

        g.add_step(s,[])

    def test_graph(self):
        g = manuallabour.Graph()

        g.add_object(manuallabour.Object('nut',name="Nut"))
        g.add_object(manuallabour.Object('b',name="Wrench"))

        g.add_step(manuallabour.GraphStep('a',
            title='First Step',
            description='Do this',
            parts = {'nut' : manuallabour.ObjectReference('nut',optional=True)}
        ),[])
        g.add_step(manuallabour.GraphStep('b',
            title='Second Step',
            description='Do that',
            parts = {'nut' : manuallabour.ObjectReference('nut',quantity=2)},
            tools = {'wr' : manuallabour.ObjectReference('b',)}
        ),['a'])

        g.to_svg('tests/output/test.svg')


