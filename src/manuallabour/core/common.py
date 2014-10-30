"""
This module defines common classes and interfaces for manual labour
"""

import pkgutil
import json
import re
from copy import copy
from datetime import timedelta

import jsonschema

OBJ_ID = '^[a-zA-Z0-9_]*$'
RES_ID = '^[a-zA-Z0-9_]*$'

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
        for field, schema in self._schema["properties"].iteritems():
            if (not field in kwargs) and "default" in schema:
                self._kwargs[field] = copy(schema["default"])
        self._calculated = {}
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
    _schema = json.loads(
        pkgutil.get_data('manuallabour.core', 'schema/object.json')
    )
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)

class ObjectReference(DataStruct):
    """
    A reference to an object that is stored by its obj_id in an object store.

    A object can not be created and optional at the same time.
    """
    _schema = json.loads(
        pkgutil.get_data('manuallabour.core', 'schema/obj_ref.json')
    )
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)
        assert not (self.created and self.optional)

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


class BOMReference(object):
    """
    A reference to an object that is stored by its obj_id in an object store.
    """
    def __init__(self,obj_id,**kwargs):
        if re.match(OBJ_ID,obj_id) is None:
            raise ValueError('Invalid obj_id: %s' % obj_id)
        self.obj_id = obj_id

        validate(kwargs,'bom_ref.json')

        self.optional = kwargs.get("optional",0)
        self.quantity = kwargs.get("quantity",1)


class Resource(object):
    """ Base class for Resources

    A resource is something that has a file and metadata. A resource is
    identified by its resource id.
    """
    def __init__(self, res_id):
        if re.match(RES_ID,res_id) is None:
            raise ValueError('Invalid res_id: %s' % res_id)
        self.res_id = res_id

class ResourceReference(object):
    """
    A reference to a resource that is stored by res_id in a resource store.
    """
    def __init__(self,res_id,**kwargs):
        if re.match(RES_ID,res_id) is None:
            raise ValueError('Invalid res_id: %s' % res_id)
        self.res_id = res_id

        validate(kwargs,'res_ref.json')

class File(Resource):
    """ File resource

    A File is a resource that has a filename as metadata.
    """
    def __init__(self,res_id,**kwargs):
        Resource.__init__(self,res_id)

        validate(kwargs,'file.json')

        self.filename = kwargs["filename"]

class Image(Resource):
    """ Image resource

    An Image is a resource that has as metadata an alternative description
    and a filename extension indicating the format of the image.
    """
    def __init__(self,res_id,**kwargs):
        Resource.__init__(self,res_id)

        validate(kwargs,'image.json')

        self.alt = kwargs["alt"]
        self.ext = kwargs["extension"]

