import unittest
from datetime import timedelta

from manuallabour.exporters.html import *
from manuallabour.core.graph import Graph,GraphStep
from manuallabour.core.schedule import Schedule, schedule_greedy
from manuallabour.core.stores import LocalMemoryStore

class TestExporter(unittest.TestCase):
    def test_html_single(self):
        dt = timedelta(minutes=4)
        steps = [
            GraphStep(
                step_id='a',
                title="First",
                description="Do this",
                duration=dt
            ),
            GraphStep(
                step_id='b',
                title="Second",
                description="Do that",
                duration=dt
            )
        ]
        g = Graph(steps,LocalMemoryStore())

        steps,start = schedule_greedy(g)
        s = Schedule(steps,g.store,start)
        e = SinglePageHTMLExporter('basic')

        e.export(s,'tests/output/html_single')

