import unittest
from datetime import timedelta

from jsonschema import ValidationError

import manuallabour.core.common as common
from manuallabour.core.stores import LocalMemoryStore
from manuallabour.core.graph import *


class TestGraph(unittest.TestCase):
    def setUp(self):
        self.steps = {
            'a' : GraphStep(step_id='xyz'),
            'b' : GraphStep(step_id='yzx',requires=['a'])
        }
    def test_dependencies(self):
        g = Graph(self.steps,LocalMemoryStore())

        self.assertEqual(g.children['a'],['b'])
        self.assertEqual(g.parents['b'],['a'])

    def test_ancestors(self):
        g = Graph(self.steps,LocalMemoryStore())

        self.assertEqual(g.all_ancestors('a'),set([]))
        self.assertEqual(g.all_ancestors('b'),set(['a']))

    def test_svg(self):
        store = LocalMemoryStore()

        store.add_res(
            common.Image(res_id='wds',alt="foo",extension=".png"),
            'a.png'
        )
        store.add_res(
            common.Image(res_id='hds',alt="boo",extension=".png"),
            'b.png'
        )
        store.add_res(common.File(res_id='kds',filename="foo"),'a.tmp')

        store.add_obj(common.Object(
            obj_id='nut',
            name="Nut",
            images=[common.ResourceReference(res_id='hds')]
        ))
        store.add_obj(common.Object(obj_id='b',name="Wrench"))
        store.add_obj(common.Object(obj_id='resnut',name="Result with a nut"))

        store.add_step(common.Step(
            step_id='a',
            title='First Step',
            description='Do this',
            parts = {
                'nut' : common.ObjectReference(obj_id='nut',optional=True)
            },
            images = {
                'res1' : common.ResourceReference(res_id='wds')
            },
            results = {
                'res' : common.ObjectReference(obj_id='resnut',created=True)
            }
        ))
        store.add_step(common.Step(
            step_id='b',
            title='Second Step',
            description='Do that',
            parts = {
                'nut' : common.ObjectReference(obj_id='nut',quantity=2),
                'cs' : common.ObjectReference(obj_id='resnut')
            },
            tools = {'wr' : common.ObjectReference(obj_id='b',)},
            files = {'res2' : common.ResourceReference(res_id='kds')}
        ))

        steps = {
            'first' : GraphStep(step_id='a'),
            'second' : GraphStep(step_id='b',requires=['first'])
        }

        g = Graph(steps,store)

        g.to_svg('tests/output/graph.svg')
        g.to_svg('tests/output/graph_obj.svg',with_objects=True)
        g.to_svg('tests/output/graph_res.svg',with_resources=True)
        g.to_svg(
            'tests/output/graph_all.svg',
            with_objects=True,
            with_resources=True
        )

