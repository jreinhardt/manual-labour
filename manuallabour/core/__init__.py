from datetime import timedelta
import pkgutil
import json
import jsonschema
import re

STEP_ID = '^[a-z-A-Z][a-zA-Z0-9]*$'
OBJ_ID = '^[a-zA-Z0-9_]*$'

def validate(inst,schema_name):
    schema = json.loads(pkgutil.get_data('manuallabour.core',schema_name))
    jsonschema.validate(inst,schema)

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

        self.duration = kwargs.pop("duration",None)
        self.waiting = kwargs.pop("waiting",timedelta())

        validate(kwargs,'schema/step.json')

        #required
        self.title = kwargs["title"]
        self.description = kwargs["description"]

        #optional
        self.attention = kwargs.get("attention",None)
        self.assertions = kwargs.get("assertions",[])

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

        validate(kwargs,'schema/object.json')

        self.name = kwargs["name"]
        self.description = kwargs.get("description","")

class ObjectReference(object):
    """
    A reference to an object that is stored by its obj_id in an object store.
    """
    def __init__(self,obj_id,**kwargs):
        if re.match(OBJ_ID,obj_id) is None:
            raise ValueError('Invalid obj_id: %s' % obj_id)
        self.obj_id = obj_id

        validate(kwargs,'schema/obj_ref.json')

        self.optional = kwargs.get("optional",False)
        self.quantity = kwargs.get("quantity",1)

class Graph(object):
    """
    Class to hold a set of dependent steps
    """
    def __init__(self):
        self.steps = {}

        #dependency graph
        self.children = {}
        self.parents = {}

        #object and resource stores
        self.objects = {}

        self.timing = True
        """Indicates, whether all steps in this graph contain timing infos"""

    def add_step(self,step,requirements):
        """
        Add a new step to the graph. Checks for collisions.
        """
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

    def add_object(self,obj):
        """
        Add a new object to the graph. Checks for collisions
        """
        if obj.obj_id in self.objects:
            raise KeyError('ObjectID already found in graph: %s' % obj.obj_id)
        self.objects[obj.obj_id] = obj

    def to_svg(self,path):
        import pygraphviz as pgv

        graph = pgv.AGraph(directed=True)

        #Add objects
        for id, obj in self.objects.iteritems():
            graph.add_node('o_' + id,label=obj.name,shape='rectangle')

        #Add nodes
        for id,step in self.steps.iteritems():
            graph.add_node('s_' + id,label=step.title)
            #add object dependencies
            for obj in step.parts.values():
                attr = {'color' : 'blue','label' : obj.quantity}
                if obj.optional:
                    attr['style'] = 'dashed'
                graph.add_edge('o_' + obj.obj_id,'s_' + id,**attr)
            for obj in step.tools.values():
                attr = {'color' : 'red','label' : obj.quantity}
                if obj.optional:
                    attr['style'] = 'dashed'
                graph.add_edge('o_' + obj.obj_id,'s_' + id,**attr)


        #Add step dependencies
        for id in self.steps:
            for child in self.children[id]:
                graph.add_edge('s_' + id,'s_' + child)

        graph.draw(path,prog='dot')
