import unittest
from datetime import timedelta

from manuallabour.exporters.html import *
from manuallabour.core.graph import Graph,GraphStep
from manuallabour.core.schedule import Schedule, schedule_greedy
from manuallabour.core.stores import LocalMemoryStore

class TestExporter(unittest.TestCase):
    def test_html_single(self):
        g = Graph(LocalMemoryStore())
        dt = timedelta(minutes=4)
        g.add_step(
            GraphStep('a',title="First",description="Do this",duration=dt)
        )
        g.add_step(
            GraphStep('b',title="Second",description="Do that",duration=dt)
        )

        steps,start = schedule_greedy(g)
        s = Schedule(steps,g.store,start)
        e = SinglePageHTMLExporter('basic')

        e.export(s,'tests/output/html_single')

