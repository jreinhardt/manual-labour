import unittest
from datetime import timedelta

from manuallabour.exporters.html import *
import manuallabour.core.common as common
from manuallabour.core.graph import Graph,GraphStep
from manuallabour.core.schedule import Schedule, schedule_greedy
from manuallabour.core.stores import LocalMemoryStore

class TestExporter(unittest.TestCase):
    def setUp(self):
        self.store = LocalMemoryStore()
        self.store.add_step(common.Step(
            step_id='a',
            title="First",
            description="Do this",
            duration=timedelta(minutes=4)
        ))
        self.store.add_step(common.Step(
            step_id='b',
            title="Second",
            description="Do that",
            duration=timedelta(minutes=6)
        ))
        self.store.add_step(common.Step(
            step_id='c',
            title="Third",
            description="And this",
            duration=timedelta(minutes=4)
        ))
        self.store.add_step(common.Step(
            step_id='d',
            title="Fourth",
            description="or this",
        ))

        self.steps_timed = {
            's1' : GraphStep(step_id='a'),
            'b1' : GraphStep(step_id='b',requires=['s1']),
            's2' : GraphStep(step_id='c',requires=['b1'])
        }

        self.steps_untimed = {
            's1' : GraphStep(step_id='a'),
            'b1' : GraphStep(step_id='b',requires=['s1']),
            's2' : GraphStep(step_id='d',requires=['s1'])
        }

    def test_html_single(self):
        g = Graph(self.steps_timed,self.store)
        steps = schedule_greedy(g)

        s = Schedule(steps,g.store)
        e = SinglePageHTMLExporter('basic')

        e.export(s,'tests/output/html_single')

