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
            'a' : dict(step_id='xyz'),
            'b' : dict(step_id='yzx',requires=['a'])
        }
    def test_dependencies(self):
        g = Graph(graph_id="foobar",steps=self.steps)

        self.assertEqual(g.children['a'],['b'])
        self.assertEqual(g.parents['b'],['a'])

    def test_ancestors(self):
        g = Graph(graph_id="foobar",steps=self.steps)

        self.assertEqual(g.all_ancestors('a'),set([]))
        self.assertEqual(g.all_ancestors('b'),set(['a']))

    def test_svg(self):
        store = LocalMemoryStore()

        schedule_example(store)

        steps = {
            's1' : dict(step_id='a'),
            'b1' : dict(step_id='b',requires=['s1']),
            's2' : dict(step_id='c',requires=['b1']),
            's3' : dict(step_id='d',requires=['b1'])
        }
        g = Graph(graph_id="foobar",steps=steps)

        g.to_svg('tests/output/graph.svg')
        g.to_svg('tests/output/graph_obj.svg',with_objects=True)
        g.to_svg('tests/output/graph_res.svg',with_resources=True)
        g.to_svg(
            'tests/output/graph_all.svg',
            with_objects=True,
            with_resources=True
        )

    def test_collect_ids(self):
        store = LocalMemoryStore()

        schedule_example(store)

        steps = {
            's1' : dict(step_id='a'),
            'b1' : dict(step_id='b',requires=['s1']),
            's2' : dict(step_id='c',requires=['b1']),
            's3' : dict(step_id='d',requires=['b1'])
        }
        g = Graph(graph_id="foobar",steps=steps)

        res = g.collect_ids(store)

        self.assertEqual(res["step_ids"],set(["a","b","c","d"]))
        self.assertEqual(res["obj_ids"],set(["ta","pa","ra"]))
        self.assertEqual(res["blob_ids"],set(["imb","fb","imb2"]))
