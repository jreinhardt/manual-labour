import unittest
from datetime import timedelta

from jsonschema import ValidationError

import manuallabour.core.common as common
from manuallabour.core.graph import Graph, GraphStep
from manuallabour.core.stores import LocalMemoryStore

from manuallabour.core.schedule import *

def schedule_example(store):
    store.add_obj(common.Object(obj_id='ta',name='Tool A'))
    store.add_obj(common.Object(obj_id='pa',name='Part A'))
    store.add_obj(common.Object(obj_id='ra',name='Result A'))

    store.add_res(
        common.Image(res_id='im',extension='.png',alt='Foo'),
        'foo.png'
    )
    store.add_res(common.File(res_id='f',filename='test.tmp'),'../t.tmp')

    store.add_step(common.Step(
        step_id='a',
        title="First",
        description="Whack {{part(a)}} with {{tool(a)}} to get {{result(a)}}",
        duration=timedelta(minutes=15),
        images = {'t_imag' : common.ResourceReference(res_id='im')},
        tools={'a' : common.ObjectReference(obj_id='ta')},
        parts={'a' : common.ObjectReference(obj_id='pa',quantity=2)},
        results={'a' : common.ObjectReference(obj_id='ra',created=True)}
    ))
    store.add_step(common.Step(
        step_id='b',
        title="Second",
        description="Use all {{tool(a)}} to fix {{part(a)}} to {{part(b)}}",
        duration=timedelta(minutes=15),
        files = {'t_imag' : common.ResourceReference(res_id='f')},
        tools={'a' : common.ObjectReference(obj_id='ta',quantity=3)},
        parts={
            'b' : common.ObjectReference(obj_id='ra'),
            'a' : common.ObjectReference( obj_id='pa',optional=True)
        }
    ))
    store.add_step(common.Step(
        step_id='c',
        title="Third",
        description="Add {{part(a)}}",
        duration=timedelta(minutes=15),
        parts={'a' : common.ObjectReference(obj_id='pa',quantity=3)}
    ))
    store.add_step(common.Step(
        step_id='d',
        title="Third",
        description="Add {{part(a)}}",
        parts={'a' : common.ObjectReference(obj_id='pa',quantity=3)}
    ))


class TestScheduleStep(unittest.TestCase):
    def test_init(self):
        self.assertRaises(
            ValidationError,
            lambda: ScheduleStep(step_id='a')
        )
        s = ScheduleStep(step_id='9',step_idx=0)
        self.assertEqual(s.step_id,'9')
        self.assertEqual(s.step_nr,1)

        self.assertRaises(
            ValueError,
            lambda: ScheduleStep(
                step_id='a'
                ,step_idx=0,
                start=timedelta(hours=2)
            )
        )
        s=ScheduleStep(
            step_id='rs9',
            step_idx=0,
            start=timedelta(minutes=4),
            stop=timedelta(minutes=24)
        )
        self.assertEqual(s.start.total_seconds(),240)
    def test_dereference(self):
        store = LocalMemoryStore()
        schedule_example(store)

        step = ScheduleStep(
            step_id='a',
            step_idx=0,
            start=timedelta(hours=2),
            stop=timedelta(hours=2,minutes=15),
        )
        step_dict = step.dereference(store)
        self.assertEqual(step_dict["step_idx"],0)
        self.assertEqual(step_dict["title"],"First")
        self.assertEqual(step_dict["images"][0]["extension"],".png")

        step = ScheduleStep(step_id='b',step_idx=2)
        step_dict = step.dereference(store)
        self.assertEqual(step_dict["step_nr"],3)
        self.assertEqual(step_dict["images"],[])
        self.assertTrue(step_dict["stop"] is None)

class TestSchedule(unittest.TestCase):
    def test_bom(self):
        store = LocalMemoryStore()
        schedule_example(store)

        steps = [
            ScheduleStep(step_id='a',step_idx=0),
            ScheduleStep(step_id='b',step_idx=1),
            ScheduleStep(step_id='c',step_idx=2),
        ]

        s = Schedule(steps,store)
        self.assertEqual(s.tools['ta'].quantity,3)

        self.assertFalse('ra' in s.parts)
        self.assertEqual(s.parts['pa'].quantity,5)
        self.assertEqual(s.parts['pa'].optional,1)

class TestSchedulers(unittest.TestCase):
    def setUp(self):
        self.store = LocalMemoryStore()
        schedule_example(self.store)

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

    def test_greedy_timed(self):
        g = Graph(self.steps_timed,self.store)
        steps = schedule_greedy(g)

        ids = [step.step_id for step in steps]

        self.assertTrue(ids.index('b') > ids.index('a'))
        self.assertTrue(ids.index('c') > ids.index('b'))

        Schedule(steps,self.store)

    def test_greedy_untimed(self):
        g = Graph(self.steps_untimed,self.store)
        self.assertRaises(ValueError,lambda: schedule_greedy(g))
