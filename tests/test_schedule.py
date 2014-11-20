import unittest

from jsonschema import ValidationError

import manuallabour.core.common as common
from manuallabour.core.graph import Graph
from manuallabour.core.stores import LocalMemoryStore

from manuallabour.core.schedule import *

def schedule_example(store):
    store.add_blob('imb','foo.png')
    store.add_blob('fb','../t.tmp')
    store.add_blob('imb2','b.png')

    store.add_obj(common.Object(obj_id='ta',name='Tool A'))
    store.add_obj(common.Object(
        obj_id='pa',
        name='Part A',
        images=[dict(blob_id='imb2',alt="boo",extension=".png")]
    ))
    store.add_obj(common.Object(obj_id='ra',name='Result A'))

    store.add_step(common.Step(
        step_id='a',
        title="First",
        description="Whack {{part(a)}} with {{tool(a)}} to get {{result(a)}}",
        duration=dict(minutes=15),
        images = {'t_imag' : dict(blob_id='imb',extension='.png',alt='Foo')},
        tools={'a' : dict(obj_id='ta')},
        parts={'a' : dict(obj_id='pa',quantity=2)},
        results={'a' : dict(obj_id='ra',created=True)}
    ))
    store.add_step(common.Step(
        step_id='b',
        title="Second",
        description="Use all {{tool(a)}} to fix {{part(a)}} to {{part(b)}}",
        duration=dict(minutes=15),
        files = {'t_imag' : dict(blob_id='fb',filename='test.tmp')},
        tools={'a' : dict(obj_id='ta',quantity=3)},
        parts={
            'b' : dict(obj_id='ra'),
            'a' : dict( obj_id='pa',optional=True)
        }
    ))
    store.add_step(common.Step(
        step_id='c',
        title="Third",
        description="Add {{part(a)}}",
        duration=dict(minutes=15),
        parts={'a' : dict(obj_id='pa',quantity=3)}
    ))
    store.add_step(common.Step(
        step_id='d',
        title="Third",
        description="Add {{part(a)}}",
        parts={'a' : dict(obj_id='pa',quantity=3)}
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
                start=dict(hours=2)
            )
        )
        s=ScheduleStep(
            step_id='rs9',
            step_idx=0,
            start=dict(minutes=4),
            stop=dict(minutes=24)
        )
        self.assertEqual(s.start.total_seconds(),240)
    def test_dereference(self):
        store = LocalMemoryStore()
        schedule_example(store)

        step = ScheduleStep(
            step_id='a',
            step_idx=0,
            start=dict(hours=2),
            stop=dict(hours=2,minutes=15),
        )
        step_dict = step.dereference(store)
        self.assertEqual(step_dict["step_idx"],0)
        self.assertEqual(step_dict["title"],"First")
        self.assertEqual(step_dict["images"]["t_imag"]["extension"],".png")

        step = ScheduleStep(step_id='b',step_idx=2)
        step_dict = step.dereference(store)
        self.assertEqual(step_dict["step_nr"],3)
        self.assertEqual(step_dict["images"],{})
        self.assertTrue(step_dict["stop"] is None)

class TestSchedule(unittest.TestCase):
    def test_bom(self):
        store = LocalMemoryStore()
        schedule_example(store)

        steps = [
            dict(step_id='a',step_idx=0),
            dict(step_id='b',step_idx=1),
            dict(step_id='c',step_idx=2),
        ]

        s = Schedule(sched_id="foobar",steps=steps)
        bom = s.collect_bom(store)

        self.assertEqual(bom["tools"]['ta'].quantity,3)
        self.assertEqual(bom["tools"]['ta'].optional,0)

        self.assertFalse('ra' in bom["parts"])
        self.assertEqual(bom["parts"]['pa'].quantity,5)
        self.assertEqual(bom["parts"]['pa'].optional,1)

class TestSchedulers(unittest.TestCase):
    def setUp(self):
        self.store = LocalMemoryStore()
        schedule_example(self.store)

        self.steps_timed = {
            's1' : dict(step_id='a'),
            'b1' : dict(step_id='b',requires=['s1']),
            's2' : dict(step_id='c',requires=['b1'])
        }

        self.steps_untimed = {
            's1' : dict(step_id='a'),
            'b1' : dict(step_id='b',requires=['s1']),
            's2' : dict(step_id='d',requires=['s1'])
        }

    def test_greedy_timed(self):
        g = Graph(graph_id="foobar",steps=self.steps_timed)
        steps = schedule_greedy(g,self.store)

        ids = [step["step_id"] for step in steps]

        self.assertTrue(ids.index('b') > ids.index('a'))
        self.assertTrue(ids.index('c') > ids.index('b'))

        Schedule(sched_id="boofar",steps=steps)

    def test_greedy_untimed(self):
        g = Graph(graph_id="foobar",steps=self.steps_untimed)
        self.assertRaises(ValueError,lambda: schedule_greedy(g, self.store))
