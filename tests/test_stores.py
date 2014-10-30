import unittest
from urllib import urlopen

from manuallabour.core.common import Object, File
from manuallabour.core.stores import *

class TestStores(unittest.TestCase):
    def test_localmemory(self):
        m = LocalMemoryStore()

        self.assertFalse(m.has_obj('asdf'))
        m.add_obj(Object(obj_id='asdf',name='FooBar'))
        self.assertTrue(m.has_obj('asdf'))
        self.assertEqual(m.get_obj('asdf').name,'FooBar')

        self.assertEqual(len(list(m.iter_obj())),1)

        self.assertFalse(m.has_res('adf'))
        m.add_res(File('adf',filename='test_stores.py'),'tests/test_stores.py')
        self.assertTrue(m.has_res('adf'))
        self.assertEqual(m.get_res('adf').filename,'test_stores.py')
        fid = urlopen(m.get_res_url('adf'))
        fid.close()

        self.assertEqual(len(list(m.iter_res())),1)



