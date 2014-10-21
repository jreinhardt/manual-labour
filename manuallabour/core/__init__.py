"""
This module defines common classes and interfaces for manual labour
"""
from datetime import timedelta
import pkgutil
import json
import jsonschema
import re
from os.path import abspath
from copy import copy

STEP_ID = '^[a-z-A-Z][a-zA-Z0-9]*$'
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
    jsonschema.validate(inst,schema)

class Resource(object):
    """ Base class for Resources

    A resource is something that has a file and metadata. A resource is
    identified by its resource id.
    """
    def __init__(self, res_id):
        if re.match(RES_ID,res_id) is None:
            raise ValueError('Invalid res_id: %s' % res_id)
        self.res_id = res_id

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
    def as_dict(self):
        """ Return contents as dict

        This method returns the contents of this step as a dict (without the
        step_id), such that the step can be recreated from this dict. This is
        useful for serialisation.
        """
        res = copy(self.__dict__)
        res.pop('step_id')
        if self.duration is None:
            res.pop('duration')
        if self.waiting.total_seconds() == 0:
            res.pop('waiting')
        if self.attention is None:
            res.pop('attention')
        return res

class Graph(object):
    """
    Container to hold a set of dependent steps
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
        """ Add a step to graph

        Adds a new step to the graph and registers the dependencies expressed
        by a list of step_ids of steps that are required by this step.
        """
        step_id = step.step_id
        if step_id in self.steps:
            raise KeyError('StepID already found in graph: %s' % step_id)
        self.steps[step_id] = step

        #update dependency graph in a way that order of step insertions
        #doesn't mattern
        self.parents[step_id] = requirements

        if not step_id in self.children:
            self.children[step_id] = []
        for req in requirements:
            if not req in self.children:
                self.children[req] = [step_id]
            else:
                self.children[req].append(step_id)

        if step.duration is None:
            self.timing = False

    def all_ancestors(self,step_id):
        """ Return set of all ancestor steps

        Returns a set with all steps that are a direct or indirect
        prerequisite for the step with the id step_id.
        """
        res = set([])
        for parent in self.parents[step_id]:
            res.add(parent)
            res.update(self.all_ancestors(parent))
        return res

    def to_svg(self,path):
        """
        Render graph structure to svg file
        """
        import pygraphviz as pgv

        graph = pgv.AGraph(directed=True)

        #Add objects
        for o_id, obj in self.store.iter_obj():
            o_id = 'o_' + o_id
            graph.add_node(o_id,label=obj.name,shape='rectangle')

        for r_id, res, _ in self.store.iter_res():
            r_id = 'r_' + r_id
            graph.add_node(r_id,label=res.res_id[:6],shape='diamond')

        #Add nodes
        for s_id,step in self.steps.iteritems():
            s_id = 's_' + s_id
            graph.add_node(s_id,label=step.title)

            #add object dependencies
            for obj in step.parts.values():
                o_id = 'o_' + obj.obj_id
                attr = {'color' : 'blue','label' : obj.quantity}
                if obj.optional:
                    attr['style'] = 'dashed'
                graph.add_edge(o_id,s_id,**attr)

                for img in self.store.get_obj(obj.obj_id).images:
                    graph.add_edge('r_' + img.res_id,o_id)
            for obj in step.tools.values():
                o_id = 'o_' + obj.obj_id
                attr = {'color' : 'red','label' : obj.quantity}
                if obj.optional:
                    attr['style'] = 'dashed'
                graph.add_edge(o_id,s_id,**attr)

                for img in self.store.get_obj(obj.obj_id).images:
                    graph.add_edge('r_' + img.res_id,o_id)

            #add resource dependencies
            for res in step.files.values():
                graph.add_edge('r_' + res.res_id,s_id,color='orange')
            for res in step.images.values():
                graph.add_edge('r_' + res.res_id,s_id,color='green')


        #Add step dependencies
        for s_id in self.steps:
            for child in self.children[s_id]:
                graph.add_edge('s_' + s_id,'s_' + child)

        graph.draw(path,prog='dot')

class ScheduleStep(GraphStep):
    """
    Step used in a Schedule
    """
    def __init__(self,step_id,**kwargs):

        self.step_idx = kwargs.pop("step_idx")
        """ Index of this step, starting with 0"""
        self.step_nr = self.step_idx + 1
        """ Number of this step, starting with 1"""

        self.start = kwargs.pop("start",None)
        """ Time when the active part of the step starts"""
        self.stop = kwargs.pop("stop",None)
        """ Time when the active part of the step stops"""
        self.waiting = kwargs.pop("waiting",None)
        """ Time when the waiting part of the step ends"""

        GraphStep.__init__(self,step_id,**kwargs)

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

class Schedule(object):
    """
    Container to hold a sequence of steps
    """
    def __init__(self,steps,store,start=None):
        """
        Initialize the Schedule with a sequence of Graph Steps and a store
        for all needed objects and resources.  If it is a timed schedule, a
        dict mapping ids to start timedeltas must be given
        """
        self.store = store

        self.steps = []
        i = 0
        for step in steps:
            if start is None:
                self.steps.append(
                    ScheduleStep(
                        step.step_id,
                        step_idx = i,
                        **step.as_dict()
                    )
                )
            else:
                step_id = step.step_id
                t_start = start[step_id]
                self.steps.append(
                    ScheduleStep(
                        step_id,
                        step_idx = i,
                        start = t_start,
                        stop = t_start + step.duration,
                        waiting = t_start + step.duration + step.waiting,
                        **step.as_dict()
                    )
                )
            i += 1

        #reverse lookup
        self.id_to_nr = {}
        for step in self.steps:
            self.id_to_nr[step.step_id] = step.step_nr

        #list of tools and parts
        self.tools = []
        self.parts = []
        tools = {}
        parts = {}
        for step in self.steps:
            for tool in step.tools.values():
                if not tool.obj_id in tools:
                    tools[tool.obj_id] = {"quantity" : 0 }
                if not tool.optional:
                    tools[tool.obj_id]["quantity"] = \
                        max(tool.quantity,tools[tool.obj_id]["quantity"])
            for part in step.parts.values():
                if not part.obj_id in parts:
                    parts[part.obj_id] = {
                        "optional" : 0,
                        "quantity" : 0
                    }
                if part.optional:
                    parts[part.obj_id]["optional"] += part.quantity
                else:
                    parts[part.obj_id]["quantity"] += part.quantity

        for o_id,args in tools.iteritems():
            self.tools.append(BOMReference(o_id,**args))

        for o_id,args in parts.iteritems():
            self.parts.append(BOMReference(o_id,**args))

    def to_svg(self,path):
        """
        Render schedule structure to svg file
        """
        import pygraphviz as pgv

        graph = pgv.AGraph(directed=True)

        #Add objects
        for o_id, obj in self.store.iter_obj():
            graph.add_node('o_' + o_id,label=obj.name,shape='rectangle')

        for r_id, res, _ in self.store.iter_res():
            graph.add_node('r_' + r_id,label=r_id[:6],shape='diamond')

        #Add nodes
        for step in self.steps:
            nr = step.step_nr
            graph.add_node('s_%d' % nr,label=step.title)

            #add object dependencies
            for obj in step.parts.values():
                attr = {'color' : 'blue','label' : obj.quantity}
                if obj.optional:
                    attr['style'] = 'dashed'
                graph.add_edge('o_' + obj.obj_id,'s_%d' % nr,**attr)

                for img in self.store.get_obj(obj.obj_id).images:
                    graph.add_edge('r_' + img.res_id,'o_' + obj.obj_id)
            for obj in step.tools.values():
                attr = {'color' : 'red','label' : obj.quantity}
                if obj.optional:
                    attr['style'] = 'dashed'
                graph.add_edge('o_' + obj.obj_id,'s_%d' % nr,**attr)

                for img in self.store.get_obj(obj.obj_id).images:
                    graph.add_edge('r_' + img.res_id,'o_' + obj.obj_id)

            #add resource dependencies
            for res in step.files.values():
                graph.add_edge('r_' + res.res_id,'s_%d' % nr,color='orange')
            for res in step.images.values():
                graph.add_edge('r_' + res.res_id,'s_%d' % nr,color='green')

        for step in self.steps:
            #Add step dependencies
            nr = step.step_nr
            if nr > 1:
                graph.add_edge('s_%d' % (nr-1),'s_%d' % nr)

        graph.draw(path,prog='dot')

def schedule_greedy(graph, targets = None):
    """
    Scheduler that always chooses the next step such that its finish time
    is minimized. Does not take into account limited availability of tools.

    if targets is not given, schedules full graph
    """

    if not graph.timing:
        raise ValueError(
            "This graph can not be scheduled greedily due to "
            "missing timing information"
        )

    #find set of steps required for target
    if targets is None:
        steps = set(graph.steps.values())
    else:
        steps = set([])
        for target in targets:
            steps.add(target)
            steps.update(graph.all_ancestors(target))
        steps = set(graph.steps[s] for s in steps)

    time = 0
    possible = {}
    scheduled = {}
    start = {}
    waiting = {}
    ids = []

    while len(scheduled) < len(steps):
        #find possible next steps
        for step in steps:
            s_id = step.step_id
            if s_id in scheduled:
                continue
            for dep in graph.parents[s_id]:
                if not dep in scheduled:
                    break
            else:
                possible[s_id] = step

        #from these find the step with minimal end time
        best_cand = None
        for c_id,cand in possible.iteritems():
            cand_start = time
            #find earliest possible starting time
            for dep in graph.parents[c_id]:
                if dep in waiting and waiting[dep] > cand_start:
                    cand_start = waiting[dep]
            cand_stop = cand_start + cand.duration.total_seconds()
            if best_cand is None or cand_stop < best_cand[3]:
                best_cand = (c_id,cand,cand_start,cand_stop)

        #schedule it
        # pylint: disable=W0633
        c_id,cand,cand_start,cand_stop = best_cand

        start[c_id] = cand_start
        scheduled[c_id] = cand
        ids.append(c_id)

        possible.pop(c_id)
        time = cand_stop

    return [scheduled[i] for i in ids], [start[i] for i in ids]
