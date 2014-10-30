import unittest
from datetime import timedelta

from jsonschema import ValidationError

import manuallabour.core.common as common
from manuallabour.core.graph import Graph
from manuallabour.core.stores import LocalMemoryStore

from manuallabour.core.schedule import *

class TestScheduleStep(unittest.TestCase):
    def test_schedulestep(self):
        self.assertRaises(ValidationError,lambda: ScheduleStep('a',step_idx=0))
        self.assertRaises(ValidationError,lambda: ScheduleStep('9',step_idx=0))

        params = {'title' : 'TestStep', 'description' : 'asd', 'step_idx' : 0}
        step = ScheduleStep('a',**params)
        self.assertEqual(step.title,"TestStep")

        params['parts'] = [common.ObjectReference(obj_id='nut')]
        self.assertRaises(ValidationError,lambda: ScheduleStep('a',**params))

        params['parts'] = {'nut' : common.ObjectReference(obj_id='nut')}
        step = ScheduleStep('a',**params)
        self.assertEqual(len(step.parts),1)

        params['duration'] = timedelta(minutes=5)
        step = ScheduleStep('a',**params)
        self.assertEqual(step.duration.total_seconds(),300)

        data = step.as_dict()
        self.assertEqual(step.as_dict(),ScheduleStep('a',**data).as_dict())
        self.assertEqual(data['duration'].total_seconds(),300)
        self.assertEqual(data['title'],'TestStep')

class TestSchedule(unittest.TestCase):
    def test_untimed(self):
        store = LocalMemoryStore()
        steps = [
            GraphStep(step_id='a',title="First",description="Do this"),
            GraphStep(step_id='b',title="Second",description="Do that")
        ]
        s = Schedule(steps,store)

        self.assertEqual(s.steps[0].step_idx,0)
        self.assertEqual(s.steps[0].step_nr,1)

        s.to_svg('tests/output/schedule_untimed.svg')

    def test_timed(self):
        store = LocalMemoryStore()
        steps = [
            GraphStep(
                step_id='a',
                title="First",
                description="Do this",
                duration=timedelta(minutes=5)
            ),
            GraphStep(
                step_id='b',
                title="Second",
                description="Do that",
                duration=timedelta(minutes=8)
            )
        ]
        start = {'a' : timedelta(), 'b' : timedelta(minutes=8)}
        s = Schedule(steps,store,start)

        self.assertEqual(len(s.id_to_nr),2)

        self.assertEqual(s.steps[0].start.seconds,0)
        self.assertEqual(s.steps[0].stop.seconds,300)
        self.assertEqual(s.steps[1].start.seconds,480)
        self.assertEqual(s.steps[1].stop.seconds,960)

        s.to_svg('tests/output/schedule_timed.svg')

    def test_bom(self):
        # don't need to actually fill the store, as bom and bot operate only
        # on the references
        store = LocalMemoryStore()
        steps = [
            GraphStep(
                step_id='a',
                title="First",
                description="Do this",
                tools={'a' : common.ObjectReference(obj_id='ta')},
                parts={'a' : common.ObjectReference(obj_id='pa',quantity=2)},
                results={'a' : common.ObjectReference(obj_id='ra',created=True)}
            ),
            GraphStep(
                step_id='b',
                title="Second",
                description="Do that",
                tools={'a' : common.ObjectReference(obj_id='ta',quantity=3)},
                parts={
                    'b' : common.ObjectReference(obj_id='ra'),
                    'a' : common.ObjectReference(
                        obj_id='pa',
                        quantity=2,
                        optional=True
                    )
                }
            ),
            GraphStep(
                step_id='c',
                title="Third",
                description="And this",
                parts={'a' : common.ObjectReference(obj_id='pa',quantity=3)}
            )
        ]

        s = Schedule(steps,store)
        self.assertEqual(s.tools['ta'].quantity,3)

        self.assertFalse('ra' in s.parts)
        self.assertEqual(s.parts['pa'].quantity,5)
        self.assertEqual(s.parts['pa'].optional,2)

class TestSchedulers(unittest.TestCase):
    def setUp(self):
        store = LocalMemoryStore()
        steps = [
        GraphStep(
            step_id='a',
            title='First Step',
            duration=timedelta(minutes=5),
            description='Do this'
        ),
        GraphStep(
            step_id='b',
            title='Second Step',
            duration=timedelta(minutes=5),
            requires=['a'],
            description='Do that'
        ),
        GraphStep(
            step_id='c',
            title='Something completely unrelated',
            duration=timedelta(minutes=5),
            requires=['a'],
            description='Is not required for b'
        )]
        self.g = Graph(steps,store)
    def test_greedy(self):
        steps,start = schedule_greedy(self.g)
        ids = [s.step_id for s in steps]

        self.assertTrue(ids.index('b') > ids.index('a'))
        self.assertTrue(ids.index('c') > ids.index('a'))

        steps,start = schedule_greedy(self.g,['b'])
        ids = [s.step_id for s in steps]

        self.assertTrue(ids.index('b') > ids.index('a'))
        self.assertFalse('c' in ids)

