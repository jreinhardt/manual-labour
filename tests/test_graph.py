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

        params['parts'] = [common.ObjectReference(obj_id='nut')]
        self.assertRaises(ValidationError,lambda: GraphStep('a',**params))

        params['parts'] = {'nut' : common.ObjectReference(obj_id='nut')}
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
        params = {'title' : 'TestStep', 'description' : 'asd'}
        steps = [
            GraphStep('a',**params),
            GraphStep('b',requires=['a'],**params)
        ]
        g = Graph(steps,LocalMemoryStore())

        steps.append(GraphStep('a',**params))
        self.assertRaises(KeyError, lambda: Graph(steps,LocalMemoryStore()))

        self.assertEqual(g.children['a'],['b'])
        self.assertEqual(g.parents['b'],['a'])

    def test_timing(self):
        params = {
            'title' : 'TS',
            'description' : '',
            'duration' : timedelta(minutes=4)
        }

        steps = [GraphStep('a',**params)]
        g = Graph(steps,LocalMemoryStore())
        self.assertTrue(g.timing)

        params.pop('duration')
        steps.append(GraphStep('b',requires=['a'],**params))
        g = Graph(steps,LocalMemoryStore())
        self.assertFalse(g.timing)

    def test_add_objects(self):
        store = LocalMemoryStore()

        store.add_obj(common.Object(obj_id='a',name="Nut"))
        store.add_obj(common.Object(obj_id='b',name="Wrench"))
        store.add_obj(common.Object(obj_id='c',name="Bolt"))
        store.add_obj(common.Object(obj_id='d',name="Tightened NutBolt"))

        steps = [GraphStep('b',
            title='With objects',
            description='Step with objects',
            parts = {
                'nut' : common.ObjectReference(obj_id='a'),
                'bolt' : common.ObjectReference(obj_id='c')
            },
            tools = {'wr' : common.ObjectReference(obj_id='b')},
            results = {
                'res' : common.ObjectReference(obj_id='d',created=True)
            }
        )]

        g = Graph(steps,store)

    def test_add_resources(self):
        store = LocalMemoryStore()

        img = common.Image('wds',alt="foo",extension=".png")
        store.add_res(img,'wds.png')
        self.assertRaises(KeyError,
            lambda: store.add_res(common.File('wds',filename="foo"),'a.tmp')
        )
        store.add_res(common.File('kds',filename="foo"),'a.tmp')

        steps = [GraphStep('b',
            title='With objects',
            description='Step with objects',
            files = {'l_kds' : common.ResourceReference('kds')},
            images = {'l_wds' : common.ResourceReference('wds')}
        )]

        g = Graph(steps,store)

    def test_graph(self):
        store = LocalMemoryStore()

        store.add_obj(common.Object(obj_id='nut',name="Nut"))
        store.add_obj(common.Object(obj_id='b',name="Wrench"))
        store.add_obj(common.Object(obj_id='resnut',name="Result with a nut"))

        img = common.Image('wds',alt="foo",extension=".png")
        store.add_res(img,'a.png')
        store.add_res(common.File('kds',filename="foo"),'a.tmp')

        steps = [GraphStep('a',
            title='First Step',
            description='Do this',
            parts = {
                'nut' : common.ObjectReference(obj_id='nut',optional=True)
            },
            images = {
                'res1' : common.ResourceReference('wds')
            },
            results = {
                'res' : common.ObjectReference(obj_id='resnut',created=True)
            }
        ),
        GraphStep('b',
            title='Second Step',
            description='Do that',
            requires=['a'],
            parts = {
                'nut' : common.ObjectReference(obj_id='nut',quantity=2),
                'cs' : common.ObjectReference(obj_id='resnut')
            },
            tools = {'wr' : common.ObjectReference(obj_id='b',)},
            files = {'res2' : common.ResourceReference('kds')}
        )]

        g = Graph(steps,store)

        g.to_svg('tests/output/graph.svg')

