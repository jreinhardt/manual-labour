import unittest
from datetime import timedelta

from jsonschema import ValidationError

import manuallabour.core.common as common
from manuallabour.core.stores import LocalMemoryStore
from manuallabour.core.graph import *

from test_schedule import schedule_example


class TestGraph(unittest.TestCase):
    def setUp(self):
        self.steps = [
            dict(step_id='xyz'),
            dict(step_id='yzx',requires=['xyz'])
        ]
    def test_dependencies(self):
        g = Graph(graph_id="foobar",steps=self.steps)

        self.assertEqual(g.children['xyz'],['yzx'])
        self.assertEqual(g.parents['yzx'],['xyz'])

    def test_ancestors(self):
        g = Graph(graph_id="foobar",steps=self.steps)

        self.assertEqual(g.all_ancestors('xyz'),set([]))
        self.assertEqual(g.all_ancestors('yzx'),set(['xyz']))

    def test_collect_ids(self):
        store = LocalMemoryStore()

        schedule_example(store)

        steps = [
            dict(step_id='a'),
            dict(step_id='b',requires=['a']),
            dict(step_id='c',requires=['b']),
            dict(step_id='d',requires=['a'])
        ]
        g = Graph(graph_id="foobar",steps=steps)

        res = g.collect_ids(store)

        self.assertEqual(res["graph_ids"],set(["foobar"]))
        self.assertEqual(res["step_ids"],set(["a","b","c","d"]))
        self.assertEqual(res["obj_ids"],set(["ta","pa","ra"]))
        self.assertEqual(res["blob_ids"],set(["imb","fb","imb2"]))
