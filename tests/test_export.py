import unittest
from datetime import timedelta

from manuallabour.exporters.html import *
import manuallabour.core.common as common
from manuallabour.core.graph import Graph,GraphStep
from manuallabour.core.schedule import Schedule, ScheduleStep
from manuallabour.core.stores import LocalMemoryStore

from test_schedule import schedule_example

class TestExporter(unittest.TestCase):
    def setUp(self):
        self.store = LocalMemoryStore()
        schedule_example(self.store)

        t1 = timedelta()
        t2 = timedelta(minutes=25)
        t3 = timedelta(minutes=45)
        t4 = timedelta(minutes=90)

        steps = [
            ScheduleStep(step_id='a',step_idx=0),
            ScheduleStep(step_id='b',step_idx=1),
            ScheduleStep(step_id='c',step_idx=2)
        ]
        steps_timed = [
            ScheduleStep(step_id='a',step_idx=0,start=t1,stop=t2),
            ScheduleStep(step_id='b',step_idx=1,start=t2,stop=t3),
            ScheduleStep(step_id='c',step_idx=2,start=t3,stop=t4)
        ]

        self.schedule = Schedule(steps,self.store)
        self.schedule_timed = Schedule(steps_timed,self.store)
    def test_html_single(self):
        e = SinglePageHTMLExporter('basic')

        data = dict(title="Title export",author="John Doe")

        e.export(self.schedule,'tests/output/html_single',**data)
        e.export(self.schedule_timed,'tests/output/html_single_timed',**data)

