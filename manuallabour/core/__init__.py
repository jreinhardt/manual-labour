from datetime import timedelta
import pkgutil
import json
import jsonschema
import re
from os.path import abspath

STEP_ID = '^[a-z-A-Z][a-zA-Z0-9]*$'
OBJ_ID = '^[a-zA-Z0-9_]*$'
RES_ID = '^[a-zA-Z0-9_]*$'

def validate(inst,schema_name):
    schema = json.loads(pkgutil.get_data('manuallabour.core','schema/%s' % schema_name))
    jsonschema.validate(inst,schema)

class Resource(object):
    def __init__(self, res_id):
        if re.match(RES_ID,res_id) is None:
            raise ValueError('Invalid res_id: %s' % res_id)
        self.res_id = res_id

class File(Resource):
    def __init__(self,res_id,**kwargs):
        Resource.__init__(self,res_id)
        validate(kwargs,'file.json')
        self.filename = kwargs["filename"]

class Image(Resource):
    def __init__(self,res_id,**kwargs):
        Resource.__init__(self,res_id)
        validate(kwargs,'image.json')
        self.alt = kwargs["alt"]
        self.ext = kwargs["extension"]

class ResourceReference(object):
    """
    A reference to a resource that is stored by res_id in a resource store.
    """
    def __init__(self,res_id,**kwargs):
        if re.match(RES_ID,res_id) is None:
            raise ValueError('Invalid res_id: %s' % res_id)
        self.res_id = res_id

        validate(kwargs,'res_ref.json')

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
        for id,res in self.resources.iteritems():
            yield (id,res,self.paths[id])
    def add_res(self,res,path):
        """
        Add a new resource to the store. Checks for collisions
        """
        res_id = res.res_id
        if res_id in self.resources:
            raise KeyError('ResourceID already found in Store: %s' % id)
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
    """
    def __init__(self,obj_id,**kwargs):
        if re.match(OBJ_ID,obj_id) is None:
            raise ValueError('Invalid obj_id: %s' % obj_id)
        self.obj_id = obj_id

        validate(kwargs,'obj_ref.json')

        self.optional = kwargs.get("optional",False)
        self.quantity = kwargs.get("quantity",1)


class StepBase(object):
    """
    Baseclass for a step. It has only a single required parameter, the step_id
    which is used to uniquely refer to this step.
    """
    def __init__(self,step_id):
        if re.match(STEP_ID,step_id) is None:
            raise ValueError('Invalid step_id: %s' % step_id)
        self.step_id = step_id

class GraphStep(StepBase):
    """
    Step used in a Graph.
    """
    def __init__(self,step_id,**kwargs):
        """parameters: see schema + 
        parts: list of ObjectReferences
        tools: list of ObjectReferences
        """
        StepBase.__init__(self,step_id)

        #local namespaces. not easily validated by schema
        self.parts = kwargs.pop("parts",{})
        self.tools = kwargs.pop("tools",{})

        self.files = kwargs.pop("files",{})
        self.images = kwargs.pop("images",{})

        self.duration = kwargs.pop("duration",None)
        self.waiting = kwargs.pop("waiting",timedelta())

        validate(kwargs,'step.json')

        #required
        self.title = kwargs["title"]
        self.description = kwargs["description"]

        #optional
        self.attention = kwargs.get("attention",None)
        self.assertions = kwargs.get("assertions",[])

class Graph(object):
    """
    Class to hold a set of dependent steps
    """
    def __init__(self,store):
        self.steps = {}

        #dependency graph
        self.children = {}
        self.parents = {}

        self.store = store
        """A datastructure to store object and resource data"""

        self.timing = True
        """Indicates, whether all steps in this graph contain timing infos"""

    def add_step(self,step,requirements):
        id = step.step_id
        if id in self.steps:
            raise KeyError('StepID already found in graph: %s' % id)
        self.steps[id] = step

        #update dependency graph in a way that order of step insertions
        #doesn't mattern
        self.parents[id] = requirements

        if not id in self.children:
            self.children[id] = []
        for req in requirements:
            if not req in self.children:
                self.children[req] = [id]
            else:
                self.children[req].append(id)

        if step.duration is None:
            self.timing = False

    def to_svg(self,path):
        """
        Render graph structure to svg file
        """
        import pygraphviz as pgv

        graph = pgv.AGraph(directed=True)

        #Add objects
        for id, obj in self.store.iter_obj():
            graph.add_node('o_' + id,label=obj.name,shape='rectangle')

        for id, res, _ in self.store.iter_res():
            graph.add_node('r_' + id,label=res.res_id[:6],shape='diamond')

        #Add nodes
        for id,step in self.steps.iteritems():
            graph.add_node('s_' + id,label=step.title)

            #add object dependencies
            for obj in step.parts.values():
                attr = {'color' : 'blue','label' : obj.quantity}
                if obj.optional:
                    attr['style'] = 'dashed'
                graph.add_edge('o_' + obj.obj_id,'s_' + id,**attr)

                for img in self.store.get_obj(obj.obj_id).images:
                    graph.add_edge('r_' + img.res_id,'o_' + obj.obj_id)
            for obj in step.tools.values():
                attr = {'color' : 'red','label' : obj.quantity}
                if obj.optional:
                    attr['style'] = 'dashed'
                graph.add_edge('o_' + obj.obj_id,'s_' + id,**attr)

                for img in self.store.get_obj(obj.obj_id).images:
                    graph.add_edge('r_' + img.res_id,'o_' + obj.obj_id)

            #add resource dependencies
            for res in step.files.values():
                graph.add_edge('r_' + res.res_id,'s_' + id,color='orange')
            for res in step.images.values():
                graph.add_edge('r_' + res.res_id,'s_' + id,color='green')


        #Add step dependencies
        for id in self.steps:
            for child in self.children[id]:
                graph.add_edge('s_' + id,'s_' + child)

        graph.draw(path,prog='dot')
