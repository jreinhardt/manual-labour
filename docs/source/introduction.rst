Introduction
============

Manual labour is a python library that provides data structures and algorithms for the representation and manipulation of step-by-step instructions and rendering to various output formats.

.. _step:

Step
----

The step is the most basic building block of an instruction. It is a description of an action and can be illustrated by images or other media and require :ref:`physical objects <object>` by either consuming them (parts) or using them (tools). As its result it has one or more :ref:`physical objects <object>` (results) that can be used as tools or parts in other steps.

:API: :class:`~manuallabour.core.common.Step`


.. _blob:

Blob
----

A blob stores the contents of a file, without metadata like its name, which is uniquely identified by an id. If a :ref:`step` or an :ref:`object` reference a file, they refer to its contents by the id of the blob with the contents of the file.

:API: :ref:`blob_api`

.. _object:

Object
------

An object is a data structure describing a physical object that is somehow involved in an assembly process, either as a tool, a part that is consumed or as the result of a step. An object can be illustrated by images or other media.

:API: :class:`~manuallabour.core.common.Object`

.. _graph:

Graph
-----

The most basic representation of an instruction is in form of a direct acyclic :ref:`graph` of :ref:`steps <step>`, where edges indicate dependency information.

:API: :class:`~manuallabour.core.graph.Graph`

.. _schedule:

Schedule
--------

For human consumption this is linearized (:ref:`scheduled <scheduling>`) into a ordered sequence of steps called a :ref:`schedule`. This linearization can take into account factors like tool availability, waiting times or number of cooperating parties.

:API: :class:`~manuallabour.core.schedule.Schedule`

.. _store:

Store
-----

:ref:`Blobs <blob>`, :ref:`Objects <object>` and :ref:`Steps <step>` all
have unique ids by which they can be refered to. The functionality to map
these ids to the objects they refer to is provided by a store. The store
provides access to all the blobs, objects and steps for all algorithms (e.g.
:ref:`scheduling` or :ref:`exporting`).

:API: :ref:`store_api`

.. _scheduling:

Scheduling
----------

Scheduling is the transformation of a :ref:`graph` to a :ref:`schedule`. Usually there is no unique schedule to a graph, but many different possibilities. Manual labour offers different scheduling functions that try to optimize different properties of the resulting schedule.

.. _exporting:

Exporting
---------

Exporting is the transformation of a :ref:`schedule` or :ref:`graph` to another form, for example to a nicely formatted HTML or PDF. Manual labour provides a number of exporters to various output formats.

Some of these allow even more control about the appearance of the end result by supporting layouts.
