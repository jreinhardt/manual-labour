"""
This module defines the Graph class and related classes
"""
import re
from copy import copy
from datetime import timedelta

from manuallabour.core.common import validate

STEP_ID = '^[a-z-A-Z][a-zA-Z0-9]*$'

class GraphStep(object):
    """
    Step used in a Graph.
    """
    def __init__(self,step_id,**kwargs):
        """parameters: see schema +
        parts: list of ObjectReferences
        tools: list of ObjectReferences
        """
        if re.match(STEP_ID,step_id) is None:
            raise ValueError('Invalid step_id: %s' % step_id)
        self.step_id = step_id

        validate(kwargs,'step.json')

        #local namespaces
        self.images = kwargs.get("images",{})
        self.files = kwargs.get("files",{})

        self.tools = kwargs.get("tools",{})
        self.parts = kwargs.get("parts",{})
        self.results = kwargs.get("results",{})
        for res in self.results.values():
            assert res.created

        self.waiting = kwargs.get("waiting",timedelta())
        self.duration = kwargs.get("duration",None)

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

        graph = pgv.AGraph(directed=True,strict=False)

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

            for obj in step.results.values():
                o_id = 'o_' + obj.obj_id
                attr = {'color' : 'brown','label' : obj.quantity}
                if obj.optional:
                    attr['style'] = 'dashed'
                #results are always created
                graph.add_edge(s_id,o_id,**attr)

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

