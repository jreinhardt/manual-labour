import unittest
from urllib import urlopen

import manuallabour.core.common as common
from manuallabour.core.stores import *

class TestStores(unittest.TestCase):
    def test_localmemory(self):
        m = LocalMemoryStore()

        self.assertFalse(m.has_obj('asdf'))
        m.add_obj(common.Object(obj_id='asdf',name='FooBar'))
        self.assertTrue(m.has_obj('asdf'))
        self.assertEqual(m.get_obj('asdf').name,'FooBar')

        self.assertEqual(len(list(m.iter_obj())),1)

        m.add_blob('asg','tests/test_stores.py')

    def test_blobs(self):
        store = LocalMemoryStore()

        self.assertFalse(store.has_blob('afgda'))

        store.add_blob('afgda','tests/test_stores.py')

        self.assertTrue(store.has_blob('afgda'))

        fid = urlopen(store.get_blob_url('afgda'))
        fid.close()

    def test_add_objects(self):
        store = LocalMemoryStore()

        store.add_obj(common.Object(obj_id='a',name="Nut"))
        store.add_obj(common.Object(obj_id='b',name="Wrench"))
        store.add_obj(common.Object(obj_id='c',name="Bolt"))
        blt = common.Object(obj_id='d',name="Tightened NutBolt")
        store.add_obj(blt)

        self.assertTrue(store.has_obj('a'))
        self.assertFalse(store.has_obj('f'))
        self.assertEqual(blt,store.get_obj('d'))
        self.assertEqual(len(list(store.iter_obj())),4)

        self.assertRaises(KeyError,
            lambda: store.add_obj(
                (common.Object(obj_id='a',name="Smaller Nut"))
            )
        )
