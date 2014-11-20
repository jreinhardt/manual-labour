import unittest
from datetime import timedelta

import manuallabour.core.common as common
from manuallabour.core.graph import Graph
from manuallabour.core.schedule import Schedule
from manuallabour.core.stores import LocalMemoryStore

from manuallabour.exporters.html import SinglePageHTMLExporter
from manuallabour.exporters.svg import GraphSVGExporter, ScheduleSVGExporter

from test_schedule import schedule_example

class TestExporter(unittest.TestCase):
    def setUp(self):
        self.data = dict(title="Title export",author="John Doe")
        self.store = LocalMemoryStore()
        schedule_example(self.store)

        t1 = dict()
        t2 = dict(minutes=25)
        t3 = dict(minutes=45)
        t4 = dict(minutes=90)

        steps_graph = {
            's1' : dict(step_id='a'),
            'b1' : dict(step_id='b',requires=['s1']),
            's2' : dict(step_id='c',requires=['b1']),
            's3' : dict(step_id='d',requires=['b1'])
        }
        self.graph = Graph(graph_id="foobar",steps=steps_graph)

        steps = [
            dict(step_id='a',step_idx=0),
            dict(step_id='b',step_idx=1),
            dict(step_id='c',step_idx=2)
        ]
        steps_timed = [
            dict(step_id='a',step_idx=0,start=t1,stop=t2),
            dict(step_id='b',step_idx=1,start=t2,stop=t3),
            dict(step_id='c',step_idx=2,start=t3,stop=t4)
        ]

        self.schedule = Schedule(sched_id="foobar",steps=steps)
        self.schedule_timed = Schedule(sched_id="foobar",steps=steps_timed)
    def test_html_single(self):
        e = SinglePageHTMLExporter('basic')

        e.export(
            self.schedule,
            self.store,
            'tests/output/html_single',
            **self.data
        )
        e.export(
            self.schedule_timed,
            self.store,
            'tests/output/html_single_timed',
            **self.data
        )

    def test_graph_svg(self):
        GraphSVGExporter().export(
            self.graph,
            self.store,
            'tests/output/graph.svg',
            **self.data
        )

        GraphSVGExporter(with_objects=True).export(
            self.graph,
            self.store,
            'tests/output/graph_obj.svg',
            **self.data
        )

        GraphSVGExporter(with_resources=True).export(
            self.graph,
            self.store,
            'tests/output/graph_res.svg',
            **self.data
        )

        GraphSVGExporter(with_objects=True,with_resources=True).export(
            self.graph,
            self.store,
            'tests/output/graph_all.svg',
            **self.data
        )

    def test_schedule_svg(self):
        ScheduleSVGExporter().export(
            self.schedule,
            self.store,
            'tests/output/schedule.svg',
            **self.data
        )

        ScheduleSVGExporter(with_objects=True).export(
            self.schedule_timed,
            self.store,
            'tests/output/schedule_obj.svg',
            **self.data
        )

        ScheduleSVGExporter(with_resources=True).export(
            self.schedule_timed,
            self.store,
            'tests/output/schedule_res.svg',
            **self.data
        )

        ScheduleSVGExporter(with_objects=True,with_resources=True).export(
            self.schedule,
            self.store,
            'tests/output/schedule_all.svg',
            **self.data
        )

