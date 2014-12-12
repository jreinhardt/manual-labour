# Manual labour - a library for step-by-step instructions
# Copyright (C) 2014 Johannes Reinhardt <jreinhardt@ist-dein-freund.de>
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#  USA

"""
This module defines common classes and interfaces for manual labour
"""

import json
import pkg_resources
import hashlib
import base64
from os.path import join
from datetime import timedelta
from copy import deepcopy

import jsonschema

SCHEMA_DIR =  pkg_resources.resource_filename('manuallabour.core','schema')

def calculate_blob_checksum(fid):
    """
    Calculate a checksum over a file like object. Seeks back to the start
    after finished. Useful to use as (a part of) a blob_id. Uses sha512
    checksum encoded to base64.

    :param File fid: open file descriptor of the blob
    :return: the blob id
    :rtype: str
    """
    fid.seek(0)

    check = hashlib.sha512()
    #use chunking to avoid excessive memory use on large files
    for chunk in iter(lambda: fid.read(8192), b''):
        check.update(chunk)
    fid.seek(0)
    return base64.urlsafe_b64encode(check.digest())[:-2]

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
    elif isinstance(kwargs,str) or isinstance(kwargs,unicode):
        check.update(kwargs)
    elif isinstance(kwargs,int):
        check.update(str(kwargs))
    else:
        raise ValueError("Unknown type in checksum calculation: %s" % \
            type(kwargs))

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

def add_ids(ids1,ids2):
    """
    add ids2 to ids1, where they are both dicts of sets used to collect ids
    for access to stored items.
    """
    for key,val in ids2.iteritems():
        if key in ids1:
            ids1[key].update(val)
        else:
            ids1[key] = val

class DataStruct(object):
    """
    A container for named data. Offers validation, convenient access and
    utility functionality. Serves as basis for many of the classes holding
    data.

    DataStructs and all derived classes are initialized by providing the data
    as key-value arguments which are automatically validated.
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
                self._calculated[field] = deepcopy(schema["default"])
    def __getattr__(self,name):
        if name in self._calculated:
            return self._calculated.get(name)
        elif name in self._kwargs:
            return self._kwargs.get(name)
        else:
            raise AttributeError('Class %s has no attribute %s' %\
                (type(self),name))
    @classmethod
    def validate(cls,**kwargs):
        """
        Validate the arguments against the schema of this class.

        :raises: :class:`jsonschema.ValidationError`
        """
        cls._validator.validate(kwargs)

    def as_dict(self):
        """
        Return the constructor parameters (including defaults) of this
        instance, this can be used to recreate the instance.

        :rtype: :class:`dict`
        """
        res = deepcopy(self._kwargs)
        for field, schema in self._schema["properties"].iteritems():
            if (not field in res) and "default" in schema:
                res[field] = deepcopy(schema["default"])
        return res
    def dereference(self,_store):
        """
        Collect the content of this element as a dict. References are
        recursively dereferenced against store.

        :rtype: :class:`dict`
        """
        res = {}
        res.update(deepcopy(self._kwargs))
        res.update(deepcopy(self._calculated))
        return res
    def collect_ids(self,_store):
        """
        Recursively collect the ids of all elements required for this one

        :rtype: :class:`dict`
        """
        raise NotImplementedError

class ReferenceBase(DataStruct):
    """
    A reference links to something in a store and can hold additional
    information. When dereferenced, the additional data from the reference
    and the data from the object in the store are combined.
    """
    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)
    def collect_ids(self,_store):
        raise NotImplementedError

class ResourceReferenceBase(ReferenceBase):
    """
    A reference to something with an associated blob.
    """
    def __init__(self,**kwargs):
        ReferenceBase.__init__(self,**kwargs)
    def dereference(self,store):
        res = ReferenceBase.dereference(self,store)
        res["url"] = store.get_blob_url(self.blob_id)
        for src in res["sourcefiles"]:
            src["url"] = store.get_blob_url(src["blob_id"])
        return res
    def collect_ids(self,_store):
        res = dict(blob_ids=set([]))
        res["blob_ids"].add(self.blob_id)
        for src in self.sourcefiles:
            res["blob_ids"].add(src["blob_id"])
        return res

class FileReference(ResourceReferenceBase):
    """
    A File is a resource that has a only a filename as metadata.

    {{references.json#/file_ref}}
    """
    _schema = load_schema(SCHEMA_DIR,'references.json')['file_ref']
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        ResourceReferenceBase.__init__(self,**kwargs)

class ImageReference(ResourceReferenceBase):
    """
    An Image is a resource that has as metadata an alternative description
    and a filename extension indicating the format of the image.

    {{references.json#/img_ref}}
    """
    _schema = load_schema(SCHEMA_DIR,'references.json')['img_ref']
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        ResourceReferenceBase.__init__(self,**kwargs)

class ObjectReference(ReferenceBase):
    """
    A reference to an object. An object can not be created and optional at
    the same time.

    {{references.json#/obj_ref}}
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

    def collect_ids(self,store):
        res = dict(obj_ids=set([]))
        res["obj_ids"].add(self.obj_id)
        obj = store.get_obj(self.obj_id)
        for img in obj.images:
            add_ids(res,img.collect_ids(store))
        return res

class ComponentBase(DataStruct):
    """
    Base class for compontents that are stored in a Store and have an id to
    identify themselves.
    """
    _id = None
    @classmethod
    def calculate_checksum(cls,**kwargs):
        """
        Utility function for calculating a sha512 checksum over the keyword
        arguments (excluding the id). This can be useful to use as an obj_id
        or a part of if. Uses base64 encoding.

        Returns a string
        """
        #Add the defaults, to make the result for kwargs be the same as for
        #the dict returned by calculate_checksum(ComponentBase.as_dict())
        res = deepcopy(kwargs)
        for field, schema in cls._schema["properties"].iteritems():
            if (not field in res) and "default" in schema:
                res[field] = deepcopy(schema["default"])
        if not cls._id in res:
            res[cls._id] = "dummy"
        cls._validator.validate(res)
        res.pop(cls._id)

        check = hashlib.sha512()
        calculate_kwargs_checksum(check,res)
        return base64.urlsafe_b64encode(check.digest())[:-2]
    def collect_ids(self,_store):
        raise NotImplementedError

class Object(ComponentBase):
    """
    Description of physical object that is in some sense relevant to the
    assembly process. It can be either a part that is consumed in a step, a
    tool that isn't, or a result that is created in a step.

    {{object.json}}

    :Calculated:
        * images (:class:`list` of
          :class:`~manuallabour.core.common.ImageReference`),
          A list of images that illustrate this object

    """
    _schema = load_schema(SCHEMA_DIR,'object.json')
    _validator = jsonschema.Draft4Validator(_schema)
    _id = "obj_id"

    def __init__(self,**kwargs):
        ComponentBase.__init__(self,**kwargs)

        if "images" in self._kwargs:
            self._calculated["images"] = []
            for img in self._kwargs["images"]:
                self._calculated["images"].append(ImageReference(**img))

    def dereference(self,store):
        res = DataStruct.dereference(self,store)
        for i,img in enumerate(res["images"]):
            res["images"][i] = img.dereference(store)
        return res

    def collect_ids(self,store):
        res = dict(obj_ids=set([self.obj_id]))
        for img in self.images:
            add_ids(res,img.collect_ids(store))
        return res

class Step(ComponentBase):
    """
    Description of the action required to transform parts into
    results with the help of tools.

    {{step.json}}

    :Calculated:
        * duration (:class:`~datetime.timedelta`),
          Time of acivity required for this step
        * waiting (:class:`~datetime.timedelta`),
          Waiting time necessary for this step
        * parts (:class:`dict` of
          :class:`~manuallabour.core.common.ObjectReference`),
          Local aliases of parts used in this step
        * tools (:class:`dict` of
          :class:`~manuallabour.core.common.ObjectReference`),
          Local aliases of tools used in this step
        * results (:class:`dict` of
          :class:`~manuallabour.core.common.ObjectReference`),
          Local aliases of results used in this step
        * files (:class:`dict` of
          :class:`~manuallabour.core.common.FileReference`),
          Local aliases of files used in this step
        * images (:class:`dict` of
          :class:`~manuallabour.core.common.ImageReference`),
          Local aliases of images used in this step
    """
    _schema = load_schema(SCHEMA_DIR,'step.json')
    _validator = jsonschema.Draft4Validator(_schema)
    _id = "step_id"

    def __init__(self,**kwargs):
        ComponentBase.__init__(self,**kwargs)

        for time in ["duration","waiting"]:
            if time in kwargs and kwargs[time]:
                self._calculated[time] = timedelta(**kwargs[time])
            else:
                self._calculated[time] = None

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

    def collect_ids(self,store):
        res = dict(step_ids=set([self.step_id]))
        for img in self.images.values():
            add_ids(res,img.collect_ids(store))
        for fil in self.files.values():
            add_ids(res,fil.collect_ids(store))
        for objs in [self.parts,self.tools,self.results]:
            for part in objs.values():
                add_ids(res,part.collect_ids(store))
        return res
