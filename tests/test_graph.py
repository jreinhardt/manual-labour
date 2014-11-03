import unittest
from datetime import timedelta

from jsonschema import ValidationError

import manuallabour.core.common as common
from manuallabour.core.stores import LocalMemoryStore
from manuallabour.core.graph import *

from test_schedule import schedule_example


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

        schedule_example(store)

        steps = {
            's1' : GraphStep(step_id='a'),
            'b1' : GraphStep(step_id='b',requires=['s1']),
            's2' : GraphStep(step_id='c',requires=['b1']),
            's3' : GraphStep(step_id='d',requires=['b1'])
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

