"""
This module defines common classes and interfaces for manual labour
"""

import pkgutil
import pkg_resources
import json
import re
from copy import copy
from datetime import timedelta
from os.path import join

import jsonschema

SCHEMA_DIR =  pkg_resources.resource_filename('manuallabour.core','schema')

def dereference_schema(schema_dir,schema):
    """
    Dereference JSON references.

    Only works for relative filesystem references like
    "$ref" : "sibling.json#/schemaname"
    and can not handle recursive references.
    """
    for k,v in schema.iteritems():
        if k == "$ref":
            fname,sname = v.split('#/')
            with open(join(schema_dir,fname)) as fid:
                ref_schema = json.loads(fid.read())
            schema.update(ref_schema[sname])
            schema.pop("$ref")
            return
        elif isinstance(v,dict):
            dereference_schema(schema_dir,v)
        elif isinstance(v,list):
            for s in v:
                if isinstance(s,dict):
                    dereference_schema(schema_dir,s)

def load_schema(schema_dir,schema_name):
    """
    Load a jsonschema and dereferences JSON references by substitution.
    """
    with open(join(schema_dir,schema_name)) as fid:
        schema = json.loads(fid.read())
    dereference_schema(schema_dir,schema)
    return schema

class DataStruct(object):
    """
    A validating convenience wrapper around a dictionary. Serves as basis for
    many of the classes holding data.
    """
    _schema = None
    """JSON schema for the input of this class"""
    _validator = None
    """Validator for the schema of this class"""
    def __init__(self,**kwargs):
        self._validator.validate(kwargs)
        self._kwargs = kwargs
        self._calculated = {}
        for field, schema in self._schema["properties"].iteritems():
            if (not field in kwargs) and "default" in schema:
                self._calculated[field] = copy(schema["default"])
    def __getattr__(self,name):
        if name in self._kwargs:
            return self._kwargs.get(name)
        elif name in self._calculated:
            return self._calculated.get(name)
        else:
            raise AttributeError('Class %s has no attribute %s' % (type(self),name))

    def as_dict(self):
        return self._kwargs


class Object(DataStruct):
    """
    An object is a physical object that is in some sense relevant to the
    assembly process. It can be either a part that is consumed in a step, a
    tool that isn't, or a result that is created in a step.
    """
    _schema = load_schema(SCHEMA_DIR,'object.json')
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)

class ObjectReference(DataStruct):
    """
    A reference to an object that is stored by its obj_id in an object store.

    A object can not be created and optional at the same time.
    """
    _schema = load_schema(SCHEMA_DIR,'obj_ref.json')
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)
        assert not (self.created and self.optional)

class BOMReference(DataStruct):
    """
    A reference to an object that is stored by its obj_id in an object store.
    """
    _schema = load_schema(SCHEMA_DIR,'bom_ref.json')
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)

class ResourceReference(DataStruct):
    """
    A reference to a resource that is stored by res_id in a resource store.
    """
    _schema = load_schema(SCHEMA_DIR,'res_ref.json')
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)

class File(DataStruct):
    """ File resource

    A File is a resource that has a filename as metadata.
    """
    _schema = load_schema(SCHEMA_DIR,'file.json')
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)

class Image(DataStruct):
    """ Image resource

    An Image is a resource that has as metadata an alternative description
    and a filename extension indicating the format of the image.
    """
    _schema = load_schema(SCHEMA_DIR,'image.json')
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)

def validate(inst,schema_name):
    """
    validate the contents of the dictionary inst against a schema as defined
    in the manuallabour.core schema directory.
    """
    schema = json.loads(
        pkgutil.get_data(
            'manuallabour.core',
            'schema/%s' % schema_name
        )
    )
    validator = jsonschema.Draft4Validator(
        schema,
        types={
            "timedelta" : (timedelta,),
            "objref" : (ObjectReference,),
            "resref" : (ResourceReference,)
        }
    )
    validator.validate(inst)
