"""
This module defines the Store interface and provides various implementations
"""

from os.path import abspath


class Store(object):
    """
    Interface for data structures that can be used to lookup blobs, resources
    and objects. The interface does not specify how to add content, as this
    can be specific to the requirements of the application.
    """
    def has_blob(self,blob_id):
        """
        Return whether a blob with the given blob_id is stored in this Store
        """
        raise NotImplementedError
    def get_blob_url(self,blob_id):
        """
        Return an URL for the blob with the given blob_id. Raise KeyError if
        blob_id is not known.
        """
        raise NotImplementedError
    def iter_blob(self):
        """
        Return an iterator over all blob ids
        """
    def has_obj(self,obj_id):
        """
        Return whether an object with the given obj_id is stored in this Store
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
    def has_step(self,step_id):
        """
        Return whether a step with the given step_id is stored in this Store.
        """
    def get_step(self,step_id):
        """
        Return the Step for this key. Raise KeyError if key is not known.
        """
        raise NotImplementedError
    def iter_step(self):
        """
        Iterate over all (step_id,step) tuples
        """
        raise NotImplementedError


class LocalMemoryStore(Store):
    """
    Store that stores resource and object data in memory and the local file
    system for files.
    """
    def __init__(self):
        self.objects = {}
        self.paths = {}
        self.steps = {}
    def has_blob(self,blob_id):
        return blob_id in self.paths
    def iter_blob(self):
        for blob_id in self.paths:
            yield blob_id
    def get_blob_url(self,blob_id):
        return "file://%s" % self.paths[blob_id]
    def add_blob(self,blob_id,path):
        """
        Add a blob by its path
        """
        if blob_id in self.paths:
            raise KeyError('BlobID already found in Store: %s' % blob_id)
        self.paths[blob_id] = abspath(path)
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

    def has_step(self,key):
        return key in self.steps
    def get_step(self,key):
        return self.steps[key]
    def iter_step(self):
        return self.steps.iteritems()
    def add_step(self,step):
        """
        Add a new step to the store. Checks for collisions
        """
        if step.step_id in self.steps:
            raise KeyError('StepID already found in store: %s' % step.step_id)
        self.steps[step.step_id] = step
