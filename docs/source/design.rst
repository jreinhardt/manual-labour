Design Considerations
=====================

In the following sections topics are covered in a bit more detail that have no
other natural place.

History and Acknowledgements
----------------------------

Besides proprietary websites like `Thingiverse <http://www.thingiverse.com/>`_,
`Instructables <http://www.instructables.com/index>` or `Youmagine
<https://www.youmagine.com/>`_ there have been a few attempts to make the
documentation of hardware projects easier:

* `skdb <http://gnusha.org/skdb/>`_
* `thingdoc <https://github.com/josefprusa/ThingDoc>`_
* `OHAI <https://github.com/alephobjects/ohai-kit>`_

but none of these got a lot of traction. However, I believe that it is very
important for the maker, 3D printing and open hardware community to have means
of efficiently documenting projects. For software, documentation is a
precondition for code reuse, as writing code oneselves is often more effective
than understanding undocumented code to reuse it. For hardware projects, the
situation is very similar.

nophead has demonstrated several important ideas for effective documentation
with his `Mendel90 3D printer <https://github.com/nophead/Mendel90>`_. There
the bill of materials and illustrations of parts and assembly steps are
automatically generated from 3D Models. This has been a big inspiration for
manual labour.

The development of manual labour started, when I got a mail from Matt Maier
with a few ideas about how documentation of hardware projects could be handled.
He propsed to use a graph structure with state nodes and change nodes. A few
mails went back and forth and I got so interested in this problem that I worked
on it more seriously. I replaced state and change nodes by
:class:`~manuallabour.core.common.Object~` and
:class:`~manuallabour.core.common.Step` and tried to get everything
sufficiently well defined to be automatically processable.

I wanted to be able to have input in various forms, e.g. a GUI tool or a
written specification of the instructions. I also realized that there are
interesting synergies with my other projects `BOLTS
<http://www.bolts-library.org>`_ and `Cadinet
<https://github.com/jreinhardt/CADinet>`_, so I tried to design the code with
the requirement to work also in the context of a web app. Another requirement
for the fundamental data structure was to allow for easy and efficient
derivatives of a project, as this is something that happens a lot. Someone
makes a small improvement, which only affects a few parts. The goal was to be
able to get complete assembly instructions by only modifying a few steps. These
requirements eventually led to the current design and the use of
:ref:`content-addressing`. This has been used in a number of cases with very
similar requirements, most notably the `version control system git
<http://git-scm.org>`_.

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

   X9qPGeRPZ33UUB_CY2jeM4ctWkCSVlqlBV-Pt0EhimkNGm9_mYuzz91iHgBiDHQtAYiCalTAx_ohzMGnM50PMw


