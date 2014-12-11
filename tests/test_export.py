# Manual labour - a library for step-by-step instructions
# Copyright (C) 2014 Johannes Reinhardt <jreinhardt@ist-dein-freund.de>
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#  USA

import unittest
from datetime import timedelta
import pkg_resources

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

        steps_graph = [
            dict(step_id='a'),
            dict(step_id='b',requires=['a']),
            dict(step_id='c',requires=['b']),
            dict(step_id='d',requires=['b'])
        ]
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
        layout_path = pkg_resources.resource_filename(
            'manuallabour.layouts.html_single.basic',
            'template')
        e = SinglePageHTMLExporter(layout_path)

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

