"""
This module defines the Graph class and related classes
"""

import jsonschema

from manuallabour.core.common import ReferenceBase, load_schema, SCHEMA_DIR,\
    graphviz_add_obj_edges

class GraphStep(ReferenceBase):
    """
    Reference to a Step for use in a Graph.
    """
    _schema = load_schema(SCHEMA_DIR,'graph_step_reference.json')
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        ReferenceBase.__init__(self,**kwargs)
    def dereference(self,store):
        res = self.as_dict(full=True)
        step = store.get_step(self.step_id)
        res.update(step.dereference(store))
        return res

class Graph(object):
    """
    Container to hold a set of dependent steps

    steps is a dictionary of alias,GraphStep tuples
    """
    def __init__(self,steps,store):
        self.steps = steps

        self.children = {}
        """Dict mapping the alias of a step to aliases of all its children"""
        self.parents = {}
        """Dict mapping the alias of a step to aliases of its parent"""

        self.store = store
        """A datastructure to store object and resource data"""

        for alias,ref in steps.iteritems():
            self.parents[alias] = ref.requires

            if not alias in self.children:
                self.children[alias] = []

            for req in ref.requires:
                if not req in self.children:
                    self.children[req] = [alias]
                else:
                    self.children[req].append(alias)

    def all_ancestors(self,alias):
        """ Return set of all ancestor steps

        Returns a set with aliases of all steps that are a direct or indirect
        prerequisite for the step with the alias alias.
        """
        res = set([])
        for parent in self.parents[alias]:
            res.add(parent)
            res.update(self.all_ancestors(parent))
        return res


    def to_svg(self,path,with_objects=False,with_resources=False):
        """
        Render graph structure to svg file
        """
        import pygraphviz as pgv

        graph = pgv.AGraph(directed=True,strict=False)

        #Nodes
        for alias,ref in self.steps.iteritems():
            s_id = 's_' + alias
            step_dict = ref.dereference(self.store)
            graph.add_node(s_id,label=step_dict["title"])

        if with_objects:
            for o_id, obj in self.store.iter_obj():
                o_id = 'o_' + o_id
                graph.add_node(o_id,label=obj.name,shape='rectangle')

        if with_resources:
            for r_id, res, _ in self.store.iter_res():
                r_id = 'r_' + r_id
                graph.add_node(r_id,label=res.res_id[:6],shape='diamond')

        #Edges
        for alias,children in self.children.iteritems():
            for child in children:
                graph.add_edge('s_' + alias,'s_' + child)

        if with_objects:
            for alias,ref in self.steps.iteritems():
                s_id = 's_' + alias
                step_dict = ref.dereference(self.store)

                args = dict(
                    attr={'color' : 'blue'},
                    opt={'style' : 'dashed'},
                    res=with_resources
                )
                graphviz_add_obj_edges(graph,s_id,step_dict["parts"],**args)

                args["attr"] = {'color' : 'red'}
                graphviz_add_obj_edges(graph,s_id,step_dict["tools"],**args)

                args["attr"] = {'color' : 'brown'}
                graphviz_add_obj_edges(graph,s_id,step_dict["results"],**args)

        if with_resources:
            for alias,ref in self.steps.iteritems():
                s_id = 's_' + alias
                step = self.store.get_step(ref.step_id)

                for res in step.files.values():
                    graph.add_edge('r_' + res.res_id,s_id,color='orange')
                for res in step.images.values():
                    graph.add_edge('r_' + res.res_id,s_id,color='green')

        graph.draw(path,prog='dot')
