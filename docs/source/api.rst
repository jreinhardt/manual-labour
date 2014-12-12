API Documentation
=================

Manual labour primarily provides a data structure for representing
step-by-step instruction and algorithms to operate on this datastructure.
This datastructure consists of :ref:`blob_api`,
:class:`~manuallabour.core.common.Object`,
:class:`~manuallabour.core.common.Step`,
:class:`~manuallabour.graph.common.Graph`,
:class:`~manuallabour.core.schedule.Schedule` that are stored in a
:class:`~manuallabour.core.stores.Store`.

.. _store_api:

Store
-----

.. autoclass:: manuallabour.core.stores.Store
   :members:

LocalMemoryStore
^^^^^^^^^^^^^^^^

Manuallabour provides one implementation of a Store that stores data in
memory and looks up blobs on the filesystem.

.. autoclass:: manuallabour.core.stores.LocalMemoryStore
   :members:

Components
----------

Everything that is stored in a :ref:`store_api` and that has an :ref:`id_api`
is called a component.

.. _blob_api:

Blob
^^^^

For manual labour a blob is opaque and its contents are not accessible (or
relevant). The only thing manual labour does with a blob is refer to it and
write or publish it for export. For this reason only a
:ref:`jsonschema-members-common-json-blob_id` is needed to be able to refer to
them.  Everything else is taken care by the :ref:`store <store_api>`.

To calculate a hash that can be used as an id (see :ref:`content-addressing`)
use :py:func:`~manuallabour.core.common.calculate_blob_checksum`:

.. autofunction:: manuallabour.core.common.calculate_blob_checksum

Object
^^^^^^

.. autoclass:: manuallabour.core.common.Object
   :members:

Step
^^^^

.. autoclass:: manuallabour.core.common.Step
   :members:

Graph
^^^^^

.. autoclass:: manuallabour.core.graph.Graph
   :members:

Schedule
^^^^^^^^

.. autoclass:: manuallabour.core.schedule.Schedule
   :members:

.. _scheduling_api:

Schedulers
----------

Manual labour provides different schedulers which take into account different aspects of a schedule:

.. autofunction:: manuallabour.core.schedule.schedule_topological

.. autofunction:: manuallabour.core.schedule.schedule_greedy

Exporters and markup
--------------------

Manual labour provides a number of classes to export a :class:`~manuallabour.core.graph.Graph` or :class:`~manuallabour.schedule.Schedule` into a different format or representation.

.. todo:: Markup
.. todo:: Baseclasses

HTML
^^^^

.. autoclass:: manuallabour.exporters.html.SinglePageHTMLExporter
   :members:
   :inherited-members:

SVG
^^^

.. autoclass:: manuallabour.exporters.svg.GraphSVGExporter
   :members:
   :inherited-members:

.. autoclass:: manuallabour.exporters.svg.ScheduleSVGExporter
   :members:
   :inherited-members:

Gantt
^^^^^

.. autoclass:: manuallabour.exporters.gantt.GanttExporter
   :members:
   :inherited-members:

Input datastructures
--------------------

The keyword arguments for initializing DataStructs are sometimes compound data, in the form of a :class:`dict` with several fields. The most common combinations of fields will be listed here.

Timedelta and Namespaces
^^^^^^^^^^^^^^^^^^^^^^^^

Namespaces define a local mapping between a short alias and an :class:`~manuallabour.core.common.Object`, image or file. This allows to conveniently refer to these without having to deal with long and complicated :ref:`id_api`.

{{common.json#/timedelta}}
{{common.json#/object_namespace}}
{{common.json#/image_namespace}}
{{common.json#/file_namespace}}

.. _id_api:

IDs
^^^

{{common.json#/blob_id}}
{{common.json#/obj_id}}
{{common.json#/step_id}}
{{common.json#/graph_id}}
{{common.json#/schedule_id}}

References
^^^^^^^^^^

{{references.json#/img_ref}}
{{references.json#/obj_ref}}
{{references.json#/bom_ref}}
{{references.json#/file_ref}}
{{references.json#/source_file_ref}}
{{references.json#/graph_step}}
{{references.json#/schedule_step}}

Base Classes
------------

The inheritance relation of the different elements that are used in manual labour is illustrated in this diagram

.. inheritance-diagram:: manuallabour.core.graph.Graph
   manuallabour.core.graph.GraphStep
   manuallabour.core.schedule.Schedule
   manuallabour.core.schedule.ScheduleStep
   manuallabour.core.schedule.BOMReference
   manuallabour.core.common.ImageReference
   manuallabour.core.common.FileReference
   manuallabour.core.common.Object
   manuallabour.core.common.ObjectReference
   manuallabour.core.common.Step

DataStruct
^^^^^^^^^^

Validation and access to the data is managed by functionality implemented in
the abstract base class :class:`~manuallabour.core.common.DataStruct`, from
which most components are derived.

DataStructs get initialized with keyword arguments, which are validated and can be accessed as attributes of the datastruct. Additional attributes can be available (calculated attributes), which overlay keyword attributes with the same name.

.. autoclass:: manuallabour.core.common.DataStruct
   :members:

ComponentBase
^^^^^^^^^^^^^

All elements that are stored in a :ref:`store_api` (except the
:ref:`blob_api`) and have a unique id are derived from the base class
:class:`~manuallabour.core.common.ComponentBase`

.. autoclass:: manuallabour.core.common.ComponentBase
   :members:

References
^^^^^^^^^^

Many of the elements of a instruction are in some way connected to other
elements. These relations are realized by storing their ids along with
additional data. This data is bundled up into a class derived from
:class:`~manuallabour.core.common.ReferenceBase`, which provides validation
and common tasks.

As a user of manual labour you usually won't have to create Reference
instances. You only need to use them as properties of
:class:`~manuallabour.core.common.Object`,
:class:`~manuallabour.core.common.Step`, :class:`~manuallabour.graph.Graph`
and :class:`~manuallabour.schedule.Schedule`.

.. autoclass:: manuallabour.core.common.ReferenceBase
   :members:
   :inherited-members:

ResourceReferences
""""""""""""""""""

One frequent type of references are references to a :ref:`blob`, which
therefore have a common base class.

.. autoclass:: manuallabour.core.common.ResourceReferenceBase
   :members:
   :inherited-members:

For specific purposes there are classes specialized from ResourceReferences.
As a user you won't have to instantiate these classes directly, just make sure
that the data you pass to an
:class:`~manuallabour.core.common.Object` or a
:class:`~manuallabour.core.common.Step` is appropriate for a
:ref:`jsonschema-members-references-json-file_ref` or an
:ref:`jsonschema-members-references-json-img_ref`.

If the blob of a ResourceReferences is automatically generated from another file, for example an image rendered from a 3D model, the Reference can also refer to the source files. They will be picked up when calling :meth:`~manuallabour.core.schedule.Schedule.collect_sourcefiles`.

.. autoclass:: manuallabour.core.common.FileReference

.. autoclass:: manuallabour.core.common.ImageReference

ObjectReference
"""""""""""""""

References to an :class:`~manuallabour.core.common.Object` that are used as a
part, tool or result in a :class:`~manuallabour.core.common.Step` are bundled
up in an :class:`~manuallabour.core.common.ObjectReference`. As a user of
manuallabour you will not have to instantiate this class directly, you only
have to make sure that the data is passed to a
:class:`~manuallabour.core.common.Step` is in an  :ref:`appropriate format
<jsonschema-members-references-json-obj_ref>`.

.. autoclass:: manuallabour.core.common.ObjectReference
   :members:
   :inherited-members:

BOM Reference
"""""""""""""""

BOM data, as returned by
:meth:`~manuallabour.core.schedule.Schedule.collect_bom` are references to an
:class:`~manuallabour.core.common.Object` with accumulated counts. As a user
of manuallabour you will not have to instantiate this class directly.

.. autoclass:: manuallabour.core.schedule.BOMReference
   :members:
   :inherited-members:

GraphStep
"""""""""

This class collects all the dependency information of the steps in a graph. You won't need to instantiate this class as a user, just make sure that the data passed to a :class:`~manuallabour.core.graph.Graph` is in an :ref:`appropriate format <jsonschema-members-references-json-graph_step>`.

.. autoclass:: manuallabour.core.graph.GraphStep
   :members:
   :inherited-members:

ScheduleStep
""""""""""""

This class collects order and timing informartion of the steps in a :class:`~manuallabour.core.schedule.Schedule`. You won't need to instantiate this class as a user, just make sure that the data passed to a :class:`~manuallabour.core.schedule.Schedule` is in an :ref:`appropriate format <jsonschema-members-references-json-schedule_step>`.

.. autoclass:: manuallabour.core.schedule.ScheduleStep
   :members:
   :inherited-members:
