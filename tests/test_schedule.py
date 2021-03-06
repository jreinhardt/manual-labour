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

from jsonschema import ValidationError

import manuallabour.core.common as common
from manuallabour.core.graph import Graph
from manuallabour.core.stores import LocalMemoryStore

from manuallabour.core.schedule import *
from itertools import tee, izip

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

def schedule_example(store):
    #bogus file names, store doesn't check
    store.add_blob('imb','foo.png')
    store.add_blob('fb','../t.tmp')
    store.add_blob('imb2','b.png')
    store.add_blob('rwth','source.src')

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
        images = {'t_imag' : dict(
            blob_id='imb',
            extension='.png',
            alt='Foo',
            sourcefiles=[dict(blob_id='rwth',filename='source.src')]
            )
        },
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
    def test_collect_ids(self):
        store = LocalMemoryStore()
        schedule_example(store)

        steps = [
            dict(step_id='a',step_idx=0),
            dict(step_id='b',step_idx=1),
        ]

        s = Schedule(sched_id="foobar",steps=steps)

        res = s.collect_ids(store)
        self.assertEqual(len(res["sched_ids"]),1)
        self.assertEqual(len(res["step_ids"]),2)
        self.assertEqual(len(res["blob_ids"]),4)
        self.assertEqual(len(res["obj_ids"]),3)

    def test_collect_sourcefiles(self):
        store = LocalMemoryStore()
        schedule_example(store)

        steps = [
            dict(step_id='a',step_idx=0),
            dict(step_id='b',step_idx=1),
        ]
        s = Schedule(sched_id="foobar",steps=steps)

        res = s.collect_sourcefiles(store)
        self.assertEqual(len(res),1)
        self.assertEqual(res[0]["blob_id"],'rwth')
        self.assertEqual(res[0]["filename"],'source.src')
        self.assertTrue("url" in res[0])

class TestSchedulers(unittest.TestCase):
    def setUp(self):
        self.store = LocalMemoryStore()
        schedule_example(self.store)

        self.steps_timed = [
            dict(step_id='a'),
            dict(step_id='b',requires=['a']),
            dict(step_id='c',requires=['b'])
        ]

        self.steps_untimed = [
            dict(step_id='a'),
            dict(step_id='b',requires=['a']),
            dict(step_id='d',requires=['a'])
        ]
        self.result_timed = None
        self.result_untimed = None

    def tearDown(self):
        if not self.result_timed is None:
            ids = [step["step_id"] for step in self.result_timed]
            self.assertTrue(ids.index('b') > ids.index('a'))
            self.assertTrue(ids.index('c') > ids.index('b'))

            for s1,s2 in pairwise(self.result_timed):
                self.assertTrue(timedelta(**s1["stop"]) <= timedelta(**s2["start"]))
            Schedule(sched_id="boofar",steps=self.result_timed)
        elif not self.result_untimed is None:
            ids = [step["step_id"] for step in self.result_untimed]
            self.assertTrue(ids.index('b') > ids.index('a'))
            self.assertTrue(ids.index('d') > ids.index('b'))

            Schedule(sched_id="boofar",steps=self.result_untimed)

    def test_greedy_timed(self):
        g = Graph(graph_id="foobar",steps=self.steps_timed)
        self.result_timed = schedule_greedy(g,self.store)

    def test_greedy_untimed(self):
        g = Graph(graph_id="foobar",steps=self.steps_untimed)
        self.assertRaises(ValueError,lambda: schedule_greedy(g, self.store))

    def test_topo_timed(self):
        g = Graph(graph_id="foobar",steps=self.steps_timed)
        self.result_timed = schedule_topological(g,self.store)

    def test_topo_untimed(self):
        g = Graph(graph_id="foobar",steps=self.steps_untimed)
        self.result_untimed = schedule_topological(g,self.store)
