"""
This module defines common classes and interfaces for manual labour
"""

import pkgutil
import json
import re
from datetime import timedelta

import jsonschema

OBJ_ID = '^[a-zA-Z0-9_]*$'
RES_ID = '^[a-zA-Z0-9_]*$'

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

class Object(object):
    """
    An object is a physical object that is in some sense relevant to the
    assembly process. It can be either a part that is consumed in a step, a
    tool that isn't, or a result that is created in a step.
    """
    def __init__(self,obj_id,**kwargs):
        if re.match(OBJ_ID,obj_id) is None:
            raise ValueError('Invalid obj_id: %s' % obj_id)
        self.obj_id = obj_id

        validate(kwargs,'object.json')

        self.name = kwargs["name"]
        self.description = kwargs.get("description","")
        self.images = kwargs.get("images",[])

class ObjectReference(object):
    """
    A reference to an object that is stored by its obj_id in an object store.

    A object can not be created and optional at the same time.
    """
    def __init__(self,obj_id,**kwargs):
        if re.match(OBJ_ID,obj_id) is None:
            raise ValueError('Invalid obj_id: %s' % obj_id)
        self.obj_id = obj_id

        validate(kwargs,'obj_ref.json')

        self.optional = kwargs.get("optional",False)
        self.created = kwargs.get("created",False)
        self.quantity = kwargs.get("quantity",1)
        assert not (self.created and self.optional)

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

