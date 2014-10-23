"""
This module defines the Store interface and provides various implementations
"""

from os.path import abspath


class Store(object):
    """
    Interface for data structures that can be used to lookup resources and
    objects. The interface does not specify how to add content, as this can be
    specific to the requirements of the application.
    """
    def has_obj(self,obj_id):
        """
        Return whether an object with the given obj_id is stored in this Store.
        """
        raise NotImplementedError
    def get_obj(self,obj_id):
        """
        Return the object for this obj_id. Raise KeyError if key is not known.
        """
        raise NotImplementedError
    def iter_obj(self):
        """
        Iterate over all (obj_id,obj) tuples
        """
        raise NotImplementedError
    def has_res(self,res_id):
        """
        Return whether a resource with the given res_id is stored in this
        Store.
        """
        raise NotImplementedError
    def get_res(self,res_id):
        """
        Return the resource for this key. Raise KeyError if key is not known.
        """
        raise NotImplementedError
    def get_res_url(self,res_id):
        """
        Return a URL for the file associated with this resource. Raise KeyError
        if res_id is not known.
        """
        raise NotImplementedError
    def iter_res(self):
        """
        Iterate over all (res_id,res,url) tuples
        """
        raise NotImplementedError

class LocalMemoryStore(Store):
    """
    Store that stores resource and object data in memory and the local file
    system for files.
    """
    def __init__(self):
        self.objects = {}
        self.resources = {}
        self.paths = {}
    def has_res(self,key):
        return key in self.resources
    def get_res(self,key):
        return self.resources[key]
    def get_res_url(self,key):
        return "file://%s" % self.paths[key]
    def iter_res(self):
        for res_id,res in self.resources.iteritems():
            yield (res_id,res,self.paths[res_id])
    def add_res(self,res,path):
        """
        Add a new resource to the store. Checks for collisions
        """
        res_id = res.res_id
        if res_id in self.resources:
            raise KeyError('ResourceID already found in Store: %s' % res_id)
        self.resources[res_id] = res
        self.paths[res_id] = abspath(path)
    def has_obj(self,key):
        return key in self.objects
    def get_obj(self,key):
        return self.objects[key]
    def iter_obj(self):
        return self.objects.iteritems()
    def add_obj(self,obj):
        """
        Add a new object to the store. Checks for collisions
        """
        if obj.obj_id in self.objects:
            raise KeyError('ObjectID already found in store: %s' % obj.obj_id)
        self.objects[obj.obj_id] = obj
