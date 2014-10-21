import unittest
from urllib import urlopen
from datetime import timedelta

from jsonschema import ValidationError

from manuallabour.core import *

class TestStep(unittest.TestCase):
    def test_BaseStep(self):
        StepBase('a')
        self.assertRaises(ValueError,lambda: StepBase('9'))

    def test_GraphStep(self):
        self.assertRaises(ValidationError,lambda: GraphStep('a'))
        self.assertRaises(ValueError,lambda: GraphStep('9'))

        params = {'title' : 'TestStep', 'description' : 'asd'}
        step = GraphStep('a',**params)
        self.assertEqual(step.title,"TestStep")

        params['parts'] = [ObjectReference('nut')]
        self.assertRaises(ValidationError,lambda: GraphStep('a',**params))

        params['parts'] = {'nut' : ObjectReference('nut')}
        step = GraphStep('a',**params)
        self.assertEqual(len(step.parts),1)

        params['duration'] = timedelta(minutes=5)
        step = GraphStep('a',**params)
        self.assertEqual(step.duration.total_seconds(),300)

        data = step.as_dict()
        self.assertEqual(data['duration'].total_seconds(),300)
        self.assertEqual(data['title'],'TestStep')

        params['waiting'] = timedelta(minutes=5)
        step = GraphStep('a',**params)
        data = step.as_dict()
        self.assertEqual(data['waiting'].total_seconds(),300)

        params['waiting'] = 21
        self.assertRaises(ValidationError,lambda: GraphStep('a',**params))

class TestResources(unittest.TestCase):
    def test_File(self):
        f = File('asbd',filename="test.file")
        self.assertEqual(f.res_id,'asbd')

        self.assertRaises(ValueError,lambda: File('*'))

        self.assertRaises(ValidationError,lambda: File('bsd'))
        self.assertRaises(ValidationError,lambda: File('bsd',foo=2))

    def test_Image(self):
        i = Image('asbf',alt='a test image',extension='.png')
        self.assertEqual(i.res_id,'asbf')

        self.assertRaises(ValueError,lambda: Image('*'))

        self.assertRaises(ValidationError, lambda: Image('sda'))
        self.assertRaises(ValidationError, lambda: Image('sda',foo=2))

class TestObjects(unittest.TestCase):
    def test_init(self):
        Object('eimer',name="Eimer")
        self.assertRaises(ValidationError,lambda:
            Object('eimer')
        )

    def test_image(self):
        o = Object('eimer',name="Eimer",images=[ResourceReference('asdf')])
        self.assertEqual(len(o.images),1)

class TestObjRefs(unittest.TestCase):
    def test_init(self):
        obr = ObjectReference('nut')
        self.assertEqual(obr.optional,False)
        self.assertEqual(obr.quantity,1)
        obr = ObjectReference('nut',quantity=2,optional=True)
        self.assertEqual(obr.optional,True)
        self.assertEqual(obr.quantity,2)

class TestStores(unittest.TestCase):
    def test_localmemory(self):
        m = LocalMemoryStore()

        self.assertFalse(m.has_obj('asdf'))
        m.add_obj(Object('asdf',name='FooBar'))
        self.assertTrue(m.has_obj('asdf'))
        self.assertEqual(m.get_obj('asdf').name,'FooBar')

        self.assertEqual(len(list(m.iter_obj())),1)

        self.assertFalse(m.has_res('asdf'))
        m.add_res(File('asdf',filename='test_core.py'),'tests/test_core.py')
        self.assertTrue(m.has_res('asdf'))
        self.assertEqual(m.get_res('asdf').filename,'test_core.py')
        fid = urlopen(m.get_res_url('asdf'))
        fid.close()

        self.assertEqual(len(list(m.iter_res())),1)

class TestGraph(unittest.TestCase):
    def test_add_steps(self):
        g = Graph(LocalMemoryStore())

        params = {'title' : 'TestStep', 'description' : 'asd'}
        g.add_step(GraphStep('a',**params),[])
        g.add_step(GraphStep('b',**params),['a'])
        self.assertRaises(KeyError, lambda:
            g.add_step(GraphStep('a',**params),[])
        )

        self.assertEqual(g.children['a'],['b'])
        self.assertEqual(g.parents['b'],['a'])

    def test_timing(self):
        g = Graph(LocalMemoryStore())

        params = {'title' : 'TS', 'description' : ''}
        params['duration'] = timedelta(minutes=4)
        g.add_step(GraphStep('a',**params),[])
        self.assertTrue(g.timing)

        params.pop('duration')
        g.add_step(GraphStep('b',**params),['a'])
        self.assertFalse(g.timing)

    def test_add_objects(self):
        store = LocalMemoryStore()
        g = Graph(store)

        store.add_obj(Object('a',name="Nut"))
        store.add_obj(Object('b',name="Wrench"))

        s = GraphStep('b',
            title='With objects',
            description='Step with objects',
            parts = {'nut' : ObjectReference('a')},
            tools = {'wr' : ObjectReference('b')}
        )

        g.add_step(s,[])

    def test_add_resources(self):
        store = LocalMemoryStore()
        g = Graph(store)

        img = Image('wds',alt="foo",extension=".png")
        store.add_res(img,'wds.png')
        self.assertRaises(KeyError,
            lambda: store.add_res(File('wds',filename="foo"),'a.tmp')
        )
        store.add_res(File('kds',filename="foo"),'a.tmp')

        s = GraphStep('b',
            title='With objects',
            description='Step with objects',
            files = {'l_kds' : ResourceReference('kds')},
            images = {'l_wds' : ResourceReference('wds')}
        )

        g.add_step(s,[])


    def test_graph(self):
        store = LocalMemoryStore()
        g = Graph(store)

        store.add_obj(Object('nut',name="Nut"))
        store.add_obj(Object('b',name="Wrench"))

        img = Image('wds',alt="foo",extension=".png")
        store.add_res(img,'a.png')
        store.add_res(File('kds',filename="foo"),'a.tmp')

        g.add_step(GraphStep('a',
            title='First Step',
            description='Do this',
            parts = {'nut' : ObjectReference('nut',optional=True)},
            images = {'res1' : ResourceReference('wds')}
        ),[])
        g.add_step(GraphStep('b',
            title='Second Step',
            description='Do that',
            parts = {'nut' : ObjectReference('nut',quantity=2)},
            tools = {'wr' : ObjectReference('b',)},
            files = {'res2' : ResourceReference('kds')}
        ),['a'])

        g.to_svg('tests/output/graph.svg')

class TestSchedule(unittest.TestCase):
    def test_untimed(self):
        store = LocalMemoryStore()
        steps = [
            GraphStep('a',title="First",description="Do this"),
            GraphStep('b',title="Second",description="Do that")
        ]
        s = Schedule(steps,store)

        self.assertEqual(s.steps[0].step_idx,0)
        self.assertEqual(s.steps[0].step_nr,1)

        s.to_svg('tests/output/schedule_untimed.svg')

    def test_timed(self):
        store = LocalMemoryStore()
        steps = [
            GraphStep('a',title="First",description="Do this",duration=timedelta(minutes=5)),
            GraphStep('b',title="Second",description="Do that",duration=timedelta(minutes=8))
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
            GraphStep('a',title="First",description="Do this",
                tools={'a' : ObjectReference('ta')},
                parts={'a' : ObjectReference('pa',quantity=2)}
            ),
            GraphStep('b',title="Second",description="Do that",
                tools={'a' : ObjectReference('ta',quantity=3)},
                parts={'a' : ObjectReference('pa',quantity=2,optional=True)}
            ),
            GraphStep('c',title="Third",description="And this",
                parts={'a' : ObjectReference('pa',quantity=3)}
            )
        ]

        s = Schedule(steps,store)
        self.assertEqual(s.tools[0].quantity,3)

        self.assertEqual(s.parts[0].quantity,5)
        self.assertEqual(s.parts[0].optional,2)

class TestSchedulers(unittest.TestCase):
    def setUp(self):
        store = LocalMemoryStore()
        self.g = Graph(store)

        self.g.add_step(GraphStep('a',
            title='First Step',
            duration=timedelta(minutes=5),
            description='Do this'
        ),[])
        self.g.add_step(GraphStep('b',
            title='Second Step',
            duration=timedelta(minutes=5),
            description='Do that'
        ),['a'])
        self.g.add_step(GraphStep('c',
            title='Something completely unrelated',
            duration=timedelta(minutes=5),
            description='Is not required for b'
        ),['a'])
    def test_greedy(self):
        steps,start = schedule_greedy(self.g)
        ids = [s.step_id for s in steps]

        self.assertTrue(ids.index('b') > ids.index('a'))
        self.assertTrue(ids.index('c') > ids.index('a'))

        steps,start = schedule_greedy(self.g,['b'])
        ids = [s.step_id for s in steps]

        self.assertTrue(ids.index('b') > ids.index('a'))
        self.assertFalse('c' in ids)



