"""
This module defines the Graph class and related classes
"""

import jsonschema

from manuallabour.core.common import ReferenceBase, load_schema, SCHEMA_DIR,\
    graphviz_add_obj_edges, ContentBase

class GraphStep(ReferenceBase):
    """
    Reference to a Step for use in a Graph.
    """
    _schema = load_schema(SCHEMA_DIR,'references.json')["graph_step"]
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        ReferenceBase.__init__(self,**kwargs)
    def dereference(self,store):
        res = {}
        res.update(self._kwargs)
        res.update(self._calculated)
        step = store.get_step(self.step_id)
        res.update(step.dereference(store))
        return res

class Graph(ContentBase):
    """
    Container to hold a set of dependent steps

    steps:
        Dict with aliases and GraphSteps
    children:
        Dict mapping the alias of a step to aliases of all its children
    parents:
        Dict mapping the alias of a step to aliases of its parent
    """
    _schema = load_schema(SCHEMA_DIR,'graph.json')
    _validator = jsonschema.Draft4Validator(_schema)
    _id = "graph_id"

    def __init__(self,**kwargs):
        ContentBase.__init__(self,**kwargs)

        self._calculated["steps"] = {}
        for alias,ref in kwargs["steps"].iteritems():
            self._calculated["steps"][alias] = GraphStep(**ref)

        #Dependency information
        self._calculated["children"] = {}
        self._calculated["parents"] = {}

        for alias,ref in self.steps.iteritems():
            self._calculated["parents"][alias] = ref.requires

            if not alias in self.children:
                self._calculated["children"][alias] = []

            for req in ref.requires:
                if not req in self.children:
                    self._calculated["children"][req] = [alias]
                else:
                    self._calculated["children"][req].append(alias)

    def collect_ids(self,store):
        #Sets of steps, objects, and blobs used in this graph
        res = {}
        res["step_ids"] = set([])
        res["obj_ids"] = set([])
        res["blob_ids"] = set([])

        for ref in self.steps.values():
            res["step_ids"].add(ref.step_id)

        for step_id in list(res["step_ids"]):
            step = store.get_step(step_id)

            for img in step.images.values():
                res["blob_ids"].add(img.blob_id)
            for fil in step.files.values():
                res["blob_ids"].add(fil.blob_id)

            for tool in step.tools.values():
                res["obj_ids"].add(tool.obj_id)
            for part in step.parts.values():
                res["obj_ids"].add(part.obj_id)
            for result in step.results.values():
                res["obj_ids"].add(result.obj_id)

        for obj_id in list(res["obj_ids"]):
            obj = store.get_obj(obj_id)
            for img in obj.images:
                res["blob_ids"].add(img.blob_id)

        return res

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

        steps = {}
        for alias,ref in self.steps.iteritems():
            steps[alias] = ref.dereference(self.store)

        #Nodes
        for alias,step_dict in steps.iteritems():
            s_id = 's_' + alias
            graph.add_node(s_id,label=step_dict["title"])

        if with_objects:
            for o_id, obj in self.store.iter_obj():
                o_id = 'o_' + o_id
                graph.add_node(o_id,label=obj.name,shape='rectangle')

        if with_resources:
            for blob_id in self.store.iter_blob():
                r_id = 'r_' + blob_id
                graph.add_node(r_id,label=blob_id[:6],shape='diamond')

        #Edges
        for alias,children in self.children.iteritems():
            for child in children:
                graph.add_edge('s_' + alias,'s_' + child)

        if with_objects:
            for alias,step_dict in steps.iteritems():
                s_id = 's_' + alias

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
            for alias,step_dict in steps.iteritems():
                s_id = 's_' + alias

                for res in step_dict["files"].values():
                    graph.add_edge('r_' + res["blob_id"],s_id,color='orange')
                for res in step_dict["images"].values():
                    graph.add_edge('r_' + res["blob_id"],s_id,color='green')

        graph.draw(path,prog='dot')
