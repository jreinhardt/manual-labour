import unittest

from jsonschema import ValidationError

import manuallabour.core.common as common
from manuallabour.core.stores import LocalMemoryStore
from manuallabour.core.graph import *

class TestGraphStep(unittest.TestCase):
    def test_graphstep(self):
        self.assertRaises(ValidationError,lambda: GraphStep('a'))
        self.assertRaises(ValueError,lambda: GraphStep('9'))

        params = {'title' : 'TestStep', 'description' : 'asd'}
        step = GraphStep('a',**params)
        self.assertEqual(step.title,"TestStep")

        params['parts'] = [common.ObjectReference('nut')]
        self.assertRaises(ValidationError,lambda: GraphStep('a',**params))

        params['parts'] = {'nut' : common.ObjectReference('nut')}
        step = GraphStep('a',**params)
        self.assertEqual(len(step.parts),1)

        params['duration'] = timedelta(minutes=5)
        step = GraphStep('a',**params)
        self.assertEqual(step.duration.total_seconds(),300)

        data = step.as_dict()
        self.assertEqual(step.as_dict(),GraphStep('a',**data).as_dict())
        self.assertEqual(data['duration'].total_seconds(),300)
        self.assertEqual(data['title'],'TestStep')

        params['waiting'] = timedelta(minutes=5)
        step = GraphStep('a',**params)
        data = step.as_dict()
        self.assertEqual(data['waiting'].total_seconds(),300)

        params['waiting'] = 21
        self.assertRaises(ValidationError,lambda: GraphStep('a',**params))

class TestGraph(unittest.TestCase):
    def test_add_steps(self):
        g = Graph(LocalMemoryStore())

        params = {'title' : 'TestStep', 'description' : 'asd'}
        g.add_step(GraphStep('a',**params))
        g.add_step(GraphStep('b',requires=['a'],**params))
        self.assertRaises(KeyError, lambda:
            g.add_step(GraphStep('a',**params))
        )

        self.assertEqual(g.children['a'],['b'])
        self.assertEqual(g.parents['b'],['a'])

    def test_timing(self):
        g = Graph(LocalMemoryStore())

        params = {'title' : 'TS', 'description' : ''}
        params['duration'] = timedelta(minutes=4)
        g.add_step(GraphStep('a',**params))
        self.assertTrue(g.timing)

        params.pop('duration')
        g.add_step(GraphStep('b',requires=['a'],**params))
        self.assertFalse(g.timing)

    def test_add_objects(self):
        store = LocalMemoryStore()
        g = Graph(store)

        store.add_obj(common.Object('a',name="Nut"))
        store.add_obj(common.Object('b',name="Wrench"))
        store.add_obj(common.Object('c',name="Bolt"))
        store.add_obj(common.Object('d',name="Tightened NutBolt"))

        s = GraphStep('b',
            title='With objects',
            description='Step with objects',
            parts = {
                'nut' : common.ObjectReference('a'),
                'bolt' : common.ObjectReference('c')
            },
            tools = {'wr' : common.ObjectReference('b')},
            results = {'res' : common.ObjectReference('d',created=True)}
        )

        g.add_step(s)

    def test_add_resources(self):
        store = LocalMemoryStore()
        g = Graph(store)

        img = common.Image('wds',alt="foo",extension=".png")
        store.add_res(img,'wds.png')
        self.assertRaises(KeyError,
            lambda: store.add_res(common.File('wds',filename="foo"),'a.tmp')
        )
        store.add_res(common.File('kds',filename="foo"),'a.tmp')

        s = GraphStep('b',
            title='With objects',
            description='Step with objects',
            files = {'l_kds' : common.ResourceReference('kds')},
            images = {'l_wds' : common.ResourceReference('wds')}
        )

        g.add_step(s)


    def test_graph(self):
        store = LocalMemoryStore()
        g = Graph(store)

        store.add_obj(common.Object('nut',name="Nut"))
        store.add_obj(common.Object('b',name="Wrench"))
        store.add_obj(common.Object('resnut',name="Result with a nut"))

        img = common.Image('wds',alt="foo",extension=".png")
        store.add_res(img,'a.png')
        store.add_res(common.File('kds',filename="foo"),'a.tmp')

        g.add_step(GraphStep('a',
            title='First Step',
            description='Do this',
            parts = {'nut' : common.ObjectReference('nut',optional=True)},
            images = {'res1' : common.ResourceReference('wds')},
            results = {'res' : common.ObjectReference('resnut',created=True)}
        ))
        g.add_step(GraphStep('b',
            title='Second Step',
            description='Do that',
            requires=['a'],
            parts = {
                'nut' : common.ObjectReference('nut',quantity=2),
                'cs' : common.ObjectReference('resnut')
            },
            tools = {'wr' : common.ObjectReference('b',)},
            files = {'res2' : common.ResourceReference('kds')}
        ))

        g.to_svg('tests/output/graph.svg')

