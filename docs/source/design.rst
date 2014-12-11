Design Considerations
=====================

.. _content-addressing:

Content Addressing
------------------

To refer to objects (e.g. :ref:`Blobs <blob>`, :ref:`Objects <object>` and
:ref:`Steps <step>`)  in a :ref:`store`, they need a unique id. In prinicple
one can use every scheme that ensures unique ids, for example one could use
sequential integers. However, it turns out that there is a class of schemes
that has very nice properties. There a ID is created from a hash over the
contents. Although this generates not strictly unique ids, for sufficiently
long hash, they are unique for all practical purposes. As objects are
immutable, a modification creates a new object with a different id.

This scheme has several advantages:

:Uniqueness: Even with many independent parties involved (like in a
             distributed system), ids are automatically unique, something that
             is very difficult to achieve with other schemes.
:Deduplication: Identical objects have the same id and are therefore
                deduplicated without additional effort. For any other id
                scheme finding and deduplicating identical objects requires
                significant effort.
:Synchroning: In a server-client scenario the two parties can efficiently
              determine a list of objects that needs to be exchanged by
              comparing lists of ids.
:Dependencies: As objects are immutable and modification create a new object
               with a different id, dependencies are no problem, as an id
               always refers to the same object. It simply cannot happen that
               someone updates a :ref:`blob` and your instruction breaks,
               because you reference this blob. Your instruction still uses
               the version of the blob that you intended.

The same idea is used in other contexts as well with great success, for
example in the `git <http://git-scm.com/>`_ version control system, the `nix
<http://nixos.org/nix/>`_ package manager and the `ipfs <http://ipfs.io/>`_
distributed file system.

Manual labour makes it easy to use content addressing by providing the helper
functions :meth:`~manuallabour.core.common.ContentBase.calculate_checksum`
and :func:`~manuallabour.core.common.calculate_blob_checksum` to calculate
the hash.

This works for all objects like :class:`~manuallabour.core.common.Object`

.. testcode::

   from manuallabour.core.common import Object

   obj_dict = dict(name="M3 nut")
   obj_id = Object.calculate_checksum(**obj_dict)
   print obj_id

   obj = Object(obj_id=obj_id,**obj_dict)

Which gives as obj_id:

.. testoutput::

   HHnw9YgaPScykSzSphlSW9osif7RZeJdFUIh6aIyHdIX_wZKkhqC4XMpyY5SaPXQS4klbTAB_BWtgYIk9cmO9Q

Or for a :class:`~manuallabour.core.common.Step`

.. testcode::

   from manuallabour.core.common import Step

   step_dict = dict(
      title='Add nut',
      description='Tighten the foo to the bar with a nut',
      parts={'nut' : dict(obj_id=obj_id,quantity=1)},
      duration=dict(minutes=3)
   )
   step_id = Step.calculate_checksum(**step_dict)
   print step_id

   step = Step(step_id=step_id,**step_dict)

which gives as step id

.. testoutput::

   qk7NQnYnfZSk5xNzS_nab1FEddeDHYHhysLxT3GT-Wz4zleoUDplU7xwgPrRnaWRmV7pHziYWTZcfg2LVhValg

For a blob use

.. testsetup:: blob

   filename = 'Makefile'

.. testcode:: blob

   from manuallabour.core.common import calculate_blob_checksum

   with open(filename) as fid:
      blob_id = calculate_blob_checksum(fid)

   print blob_id

.. testoutput:: blob
   :hide:

   5OKPRNaESlhoGK169860YDRQAXgIM8vTu57ESGANIz6QXelyNZ6gboLafku_X7QuaBhXJ6iaDQE8Ip_-nOQGmQ


