Quick Start
===========

Example
-------

As an example lets look at a simple instruction for preparing pizza. To
prepare pizza one needs to put tomato sauce onto the dough, add mushrooms,
grate some cheese over everything and put it into the preheated oven for 20
minutes.

Now we try to distill a graph of steps and their dependencies from this. Lets
start with the objects involved. We need to talk about dough, tomato sauce,
mushrooms, cheese, raw and finished pizza and a cheese grater and oven.

All objects need an unique id. For this example we just choose them
ourselves, but in many cases it makes sense to use a hash over the contents
as an ID (:ref:`content-addressing`). So lets create them and add them to the
store.  The procedure of adding things to a store is dependent on the
specific kind of store (we use a
:class:`~manuallabour.core.stores.LocalMemoryStore`), while getting things
from a store is always the same.

.. testcode::

    from manuallabour.core.stores import LocalMemoryStore
    from manuallabour.core.common import Object, Step

    store = LocalMemoryStore()

    dough = Object(
        obj_id='d',
        name='Pizza dough'
    )
    store.add_obj(dough)

    sauce = Object(
        obj_id='s',
        name='Tomato Sauce',
        description='Delicious tomato sauce'
    )
    store.add_obj(sauce)

    mushrooms = Object(
        obj_id='mu',
        name='Mushrooms'
    )
    store.add_obj(mushrooms)

    cheese = Object(
        obj_id='c',
        name='Cheese',
        description='Cheese for the pizza, preferably Mozzarella'
    )
    store.add_obj(cheese)

    pizza_raw = Object(
        obj_id='rp',
        name='Raw Pizza'
    )
    store.add_obj(pizza_raw)

    pizza_fin = Object(
        obj_id='fp',
        name='Finished Pizza'
    )
    store.add_obj(pizza_fin)

    oven = Object(
        obj_id='o',
        name='Oven',
        description='An oven capable of reaching 230 degrees celsius'
    )
    store.add_obj(oven)

    grater = Object(
        obj_id='g',
        name='Cheese Grater'
    )
    store.add_obj(grater)

Next we setup the steps

.. testcode::

    a = Step(
        step_id='a',
        title='Add ingredients',
        description='Put {{part(sauce,text=tomato sauce)}} and if you want {{part(mushrooms)}} on the {{part(dough)}}',
        duration=dict(minutes=5),
        parts=dict(
            sauce=dict(obj_id='s'),
            mushrooms=dict(obj_id='mu',quantity=5, optional=True),
            dough=dict(obj_id='d')
        )
    )
    store.add_step(a)

    b = Step(
        step_id='b',
        title='Add cheese',
        description='Use the {{tool(grater)}} to distribute some {{part(cheese)}} over the pizza',
        duration=dict(minutes=5),
        parts=dict(
            cheese=dict(obj_id='c')
        ),
        tools=dict(
            grater=dict(obj_id='g')
        ),
        results=dict(
             pizza=dict(obj_id='rp',created=True)
        )
    )
    store.add_step(b)

    c = Step(
        step_id='c',
        title='Preheat oven',
        description='Preheate the {{tool(oven)}} to 230 degree C',
        duration=dict(minutes=1),
        waiting=dict(minutes=10),
        tools=dict(
            oven=dict(obj_id='o')
        )
    )
    store.add_step(c)

    d = Step(
        step_id='d',
        title='Bake it',
        description='Put the {{part(raw)}} in the {{tool(oven)}} and bake it',
        duration=dict(minutes=3),
        waiting=dict(minutes=20),
        tools=dict(
            oven=dict(obj_id='o')
        ),
        parts=dict(
            raw=dict(obj_id='rp')
        ),
        results=dict(
            fin=dict(obj_id='fp',created=True)
        )
    )
    store.add_step(d)


Now we can create the :class:`~manuallabour.core.graph.Graph` with the dependencies between the steps:

.. testcode::

    from manuallabour.core.graph import Graph, GraphStep

    steps = [
        dict(step_id='a'),
        dict(step_id='b',requires=['a']),
        dict(step_id='c'),
        dict(step_id='d',requires=['b','c'])
    ]

    graph = Graph(graph_id='dummy',steps=steps)

Now the graph is fully defined. Its structure looks like this

.. testcode::

    from manuallabour.exporters.svg import GraphSVGExporter

    exp = GraphSVGExporter(with_objects=True)
    exp.export(
        graph,
        store,
        'generated/quickstart_graph.svg',
        title='Example Graph',
        author='John Doe'
    )

.. image:: ../generated/quickstart_graph.svg

The oval nodes of the graph are steps, and the black arrows between them are a dependency. Rectangular nodes are objects and blue edges indicate that a certain amount (indicated by the edge label) is consumed in a step. Red edges denote the use of an object as a tool, i.e. it doesn't get consumed. If an object is created in a step, a brown arrow is used.

This description can now be used to create a schedule. As in this example all steps have information about their duration and waiting times, we can use :func:`~manuallabour.core.schedule.schedule_greedy`:

.. testcode::

    from manuallabour.core.schedule import Schedule, schedule_greedy

    steps = schedule_greedy(graph,store)

    schedule = Schedule(sched_id='dummy',steps=steps)

    for step in schedule.steps:
        step_dict = step.dereference(store)
        print step_dict["title"]

The scheduler found a sequence of steps that is compatible with the dependencies. He also arranged the steps in such a way, that the waiting time in the preheating step can be used to perform other steps

.. testoutput::

    Preheat oven
    Add ingredients
    Add cheese
    Bake it

This can be seen in the corresponding gantt chart to this schedule

.. testcode::

    from manuallabour.exporters.gantt import GanttExporter

    exp = GanttExporter()
    exp.export(
        schedule,
        store,
        'generated/quickstart_gantt.svg',
        title='Example Graph',
        author='John Doe'
    )

.. image:: ../generated/quickstart_gantt.svg

The :class:`~manuallabour.core.schedule.Schedule` gives easy access to the BOM:

.. testcode::

    bom = schedule.collect_bom(store)

    for obj_id, ref in sorted(bom["parts"].iteritems(),key=lambda x:x[0]):
        obj_dict = ref.dereference(store)
        print "%d (+%d) %s" % (
            obj_dict["quantity"],
            obj_dict["optional"],
            obj_dict["name"]
        )

This gives

.. testoutput::

    1 (+0) Cheese
    1 (+0) Pizza dough
    0 (+5) Mushrooms
    1 (+0) Tomato Sauce

Note that the raw pizza object doesn't appear in the BOM, as it is created in one step and consumed in another one.

The list of required tools can be obtained in a similar way

.. testcode::

    bom = schedule.collect_bom(store)

    for obj_id, ref in sorted(bom["tools"].iteritems(),key=lambda x:x[0]):
        obj_dict = ref.dereference(store)
        print "%d (+%d) %s" % (
            obj_dict["quantity"],
            obj_dict["optional"],
            obj_dict["name"]
        )

which yields

.. testoutput::

    1 (+0) Cheese Grater
    1 (+0) Oven

Even though the oven is used in two steps, only one oven is listed, as it is (in contrast to parts) not consumed and can be reused.
