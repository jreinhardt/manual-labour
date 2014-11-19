"""
This module defines common classes and interfaces for manual labour
"""

import json
import pkg_resources
import hashlib
from copy import copy
from os.path import join
from datetime import timedelta

import jsonschema

SCHEMA_DIR =  pkg_resources.resource_filename('manuallabour.core','schema')

def calculate_blob_checksum(fid):
    """
    Calculate a checksum over a file like object. Seeks back to the start
    after finished. Useful to use as (a part of) a blob_id.
    """
    fid.seek(0)

    check = hashlib.sha512()
    #use chunking to avoid excessive memory use on large files
    for chunk in iter(lambda: fid.read(8192), b''):
        check.update(chunk)
    fid.seek(0)
    return check.hexdigest()

def calculate_kwargs_checksum(check,kwargs):
    """
    Recursively calculate a checksum for the dictionary kwargs. Sort
    dictionary keys to get a reliable and reproducible checksum.
    """
    if isinstance(kwargs,dict):
        for key,val in sorted(kwargs.iteritems(),key=lambda x: x[0]):
            check.update(key)
            calculate_kwargs_checksum(check,val)
    elif isinstance(kwargs,list):
        for val in kwargs:
            calculate_kwargs_checksum(check,val)
    elif isinstance(kwargs,str):
        check.update(kwargs)
    elif isinstance(kwargs,int):
        check.update(str(kwargs))
    else:
        raise ValueError("Unknown type in checksum calculation: %s" % kwargs)

def dereference_schema(schema_dir,schema):
    """
    Dereference JSON references.

    Only works for relative filesystem references like
    "$ref" : "sibling.json#/schemaname"
    """
    for key,val in schema.iteritems():
        if key == "$ref":
            fname,sname = val.split('#/')
            with open(join(schema_dir,fname)) as fid:
                ref_schema = json.loads(fid.read())
            schema.update(ref_schema[sname])
            schema.pop("$ref")
            dereference_schema(schema_dir,schema)
            return
        elif isinstance(val,dict):
            dereference_schema(schema_dir,val)
        elif isinstance(val,list):
            for sub in val:
                if isinstance(sub,dict):
                    dereference_schema(schema_dir,sub)

def load_schema(schema_dir,schema_name):
    """
    Load a jsonschema and dereferences JSON references by substitution.

    This allows to utilize references for mantainability and get a complete
    schema that can be used for e.g. default handling.
    """
    with open(join(schema_dir,schema_name)) as fid:
        schema = json.loads(fid.read())
    dereference_schema(schema_dir,schema)
    return schema

class DataStruct(object):
    """
    A container for named data. Offers validation, convenient access and
    utility functionality. Serves as basis for many of the classes holding
    data.
    """
    _schema = None
    """JSON schema for the input of this class"""
    _validator = None
    """Validator for the schema of this class"""
    def __init__(self,**kwargs):
        self.validate(**kwargs)
        #used to store the values as passed to the constructor
        self._kwargs = kwargs
        #used to store calulated values, defaults and processed values,
        #overlays _kwargs at access
        self._calculated = {}
        for field, schema in self._schema["properties"].iteritems():
            #check for missing defaults
            if (not field in self._schema.get("required",[])) and \
                not "default" in schema:
                raise ValueError("No default given for %s" % field)
            #apply defaults
            if (not field in kwargs) and "default" in schema:
                self._calculated[field] = copy(schema["default"])
    def __getattr__(self,name):
        if name in self._calculated:
            return self._calculated.get(name)
        elif name in self._kwargs:
            return self._kwargs.get(name)
        else:
            raise AttributeError('Class %s has no attribute %s' %\
                (type(self),name))
    def validate(self,**kwargs):
        """
        Validate the arguments against the schema of this class.
        """
        self._validator.validate(kwargs)

    def as_dict(self):
        """
        Return the constructor parameters of this instance as a dict, this can
        be used to recreate it.
        """
        return self._kwargs
    def dereference(self,store):
        """
        Return the content of this instance as a dict. References are
        recursively dereferenced against store.
        """
        res = {}
        res.update(self._kwargs)
        res.update(self._calculated)
        return res

class ReferenceBase(DataStruct):
    """
    A reference links to something in a store and can hold additional
    information. When dereferenced, the additional data from the reference
    and the data from the object in the store are combined.
    """
    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)

class ResourceReferenceBase(ReferenceBase):
    """
    A reference to something with an associated blob.
    """
    def __init__(self,**kwargs):
        ReferenceBase.__init__(self,**kwargs)
    def dereference(self,store):
        res = ReferenceBase.dereference(self,store)
        res["url"] = store.get_blob_url(self.blob_id)
        return res

class FileReference(ResourceReferenceBase):
    """
    A File is a resource that has a only a filename as metadata.
    """
    _schema = load_schema(SCHEMA_DIR,'references.json')['file_ref']
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        ResourceReferenceBase.__init__(self,**kwargs)

class ImageReference(ResourceReferenceBase):
    """
    An Image is a resource that has as metadata an alternative description
    and a filename extension indicating the format of the image.
    """
    _schema = load_schema(SCHEMA_DIR,'references.json')['img_ref']
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        ResourceReferenceBase.__init__(self,**kwargs)

class ObjectReference(ReferenceBase):
    """
    A reference to an object that is stored by its obj_id in an object store.

    A object can not be created and optional at the same time.
    """
    _schema = load_schema(SCHEMA_DIR,'references.json')["obj_ref"]
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        ReferenceBase.__init__(self,**kwargs)
        assert not (self.created and self.optional)

    def dereference(self,store):
        res = ReferenceBase.dereference(self,store)
        obj = store.get_obj(self.obj_id)
        res.update(obj.dereference(store))
        return res

class ContentBase(DataStruct):
    """
    Base class for things that are stored in a Store and have an id to
    identify themselves.
    """
    _id = None
    @classmethod
    def calculate_checksum(cls,**kwargs):
        """
        Utility function for calculating a sha512 checksum over the keyword
        arguments (excluding the id). This can be useful to use as an obj_id
        or a part of if.

        Returns a string
        """
        if not cls._id in kwargs:
            kwargs[cls._id] = "dummy"
        cls._validator.validate(kwargs)
        kwargs.pop(cls._id)

        check = hashlib.sha512()
        calculate_kwargs_checksum(check,kwargs)
        return check.hexdigest()

class Object(ContentBase):
    """
    An object is a physical object that is in some sense relevant to the
    assembly process. It can be either a part that is consumed in a step, a
    tool that isn't, or a result that is created in a step.
    """
    _schema = load_schema(SCHEMA_DIR,'object.json')
    _validator = jsonschema.Draft4Validator(_schema)
    _id = "obj_id"

    def __init__(self,**kwargs):
        ContentBase.__init__(self,**kwargs)

        if "images" in self._kwargs:
            self._calculated["images"] = []
            for img in self._kwargs["images"]:
                self._calculated["images"].append(ImageReference(**img))

    def dereference(self,store):
        res = DataStruct.dereference(self,store)
        for i,img in enumerate(res["images"]):
            res["images"][i] = img.dereference(store)
        return res

class Step(ContentBase):
    """
    One Step of the instructions
    """
    _schema = load_schema(SCHEMA_DIR,'step.json')
    _validator = jsonschema.Draft4Validator(_schema)
    _id = "step_id"

    def __init__(self,**kwargs):
        ContentBase.__init__(self,**kwargs)

        for time in ["duration","waiting"]:
            if time in kwargs:
                self._calculated[time] = timedelta(**kwargs[time])

        for nsp in ["parts","tools","results"]:
            if nsp in self._kwargs:
                self._calculated[nsp] = {}
                for alias, objref in self._kwargs[nsp].iteritems():
                    self._calculated[nsp][alias] = ObjectReference(**objref)

        for res in self.results.values():
            assert res.created

        if "files" in self._kwargs:
            self._calculated["files"] = {}
            for alias, resref in self._kwargs["files"].iteritems():
                self._calculated["files"][alias] = FileReference(**resref)

        if "images" in self._kwargs:
            self._calculated["images"] = {}
            for alias, resref in self._kwargs["images"].iteritems():
                self._calculated["images"][alias] = ImageReference(**resref)

    def dereference(self,store):
        res = DataStruct.dereference(self,store)
        for nspace in ["images","files","parts","tools","results"]:
            for alias,val in res[nspace].iteritems():
                res[nspace][alias] = val.dereference(store)
        return res

def graphviz_add_obj_edges(graph,s_id,objs,**kwargs):
    """
    add objects in the list objs to graph.

    kwargs:
    attr: dict of edge attributes
    opt: additional edge attributes for optional objects
    res: also add links to resources referenced by this object
    """
    for obj in objs:
        o_id = 'o_' + obj["obj_id"]
        if obj["optional"] and "opt" in kwargs:
            kwargs["attr"].update(kwargs["opt"])
        kwargs["attr"]["label"] = obj["quantity"]
        if obj["created"]:
            graph.add_edge(s_id,o_id,**kwargs["attr"])
        else:
            graph.add_edge(o_id,s_id,**kwargs["attr"])
        if kwargs["res"]:
            for img in obj["images"]:
                graph.add_edge('r_' + img["res_id"],o_id)

