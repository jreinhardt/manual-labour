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

Manuallabour provides one implementation of a Store that stores data in
memory and looks up blobs on the filesystem.

.. autoclass:: manuallabour.core.stores.LocalMemoryStore
   :members:

.. _blob_api:

Blob
----

For manual labour a blob is opaque, there is no need to inspect the contents
of the blob. The only thing manual labour does with a blob is refer to it and
write or publish it for export. For this reason only a
:ref:`jsonschema-common-json_blob_id` is needed to be able to refer to them.
Everything else is taken care by the :ref:`store <store_api>`.

Components
----------

Everything that is stored in a :ref:`store_api` and that has an id is called
a component.

.. autoclass:: manuallabour.core.common.Object
   :members:

.. autoclass:: manuallabour.core.common.Step
   :members:

.. autoclass:: manuallabour.core.graph.Graph
   :members:

.. autoclass:: manuallabour.core.schedule.Schedule
   :members:


Common datastructures
---------------------

The keyword arguments for initializing DataStructs are sometimes compound data, in the form of a :class:`dict` with several fields. The most common combinations of fields will be listed here.

{{common.json#/timedelta}}
{{common.json#/object_namespace}}
{{common.json#/image_namespace}}
{{common.json#/file_namespace}}
{{common.json#/blob_id}}
{{common.json#/obj_id}}
{{common.json#/step_id}}
{{references.json#/img_ref}}
{{references.json#/obj_ref}}
{{references.json#/file_ref}}
{{references.json#/source_file_ref}}

Schedulers
----------

Exporters
---------




Base Classes
------------

DataStruct
^^^^^^^^^^

Validation and access to the data is managed by functionality implemented in
the abstract base class :class:`~manuallabour.core.common.DataStruct`, from
which most components are derived.

.. autoclass:: manuallabour.core.common.DataStruct
   :members:

References
^^^^^^^^^^

Many of the components of a instruction are in some way connected to other
components. These relations are realized by storing ids along with additional
data in the component. The id and the additional data together are called a
reference.

References are special in the sense that they are only used internally, and
that a user of manual labour won't have to deal with them.

.. autoclass:: manuallabour.core.common.ReferenceBase
   :members:
   :inherited-members:

One frequent type of references are references to a :ref:`blob`, which have
their own base class

.. autoclass:: manuallabour.core.common.ResourceReferenceBase
   :members:
   :inherited-members:

Another frequent type of references are references to an
:class:`~manuallabour.core.common.Object`.

