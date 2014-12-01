"""
This module defines the Graph class and related classes
"""

import jsonschema

from manuallabour.core.common import ReferenceBase, load_schema, SCHEMA_DIR,\
    ContentBase, add_ids

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
    def collect_ids(self,store):
        step = store.get_step(self.step_id)
        return step.collect_ids(store)

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

        self._calculated["steps"] = []
        for ref in kwargs["steps"]:
            self._calculated["steps"].append(GraphStep(**ref))

        #Dependency information
        self._calculated["children"] = {}
        self._calculated["parents"] = {}

        for ref in self.steps:
            self._calculated["parents"][ref.step_id] = ref.requires

            if not ref.step_id in self.children:
                self._calculated["children"][ref.step_id] = []

            for req in ref.requires:
                if not req in self.children:
                    self._calculated["children"][req] = [ref.step_id]
                else:
                    self._calculated["children"][req].append(ref.step_id)

    def dereference(self,store):
        res = ContentBase.dereference(self,store)
        for i, step in enumerate(res["steps"]):
            res[i] = step.dereference(store)
        return res

    def collect_ids(self,store):
        res = dict(graph_ids=set([self.graph_id]))
        for ref in self.steps:
            add_ids(res,ref.collect_ids(store))
        return res

    def all_ancestors(self,step_id):
        """ Return set of all ancestor steps

        Returns a set with aliases of all steps that are a direct or indirect
        prerequisite for the step with the alias alias.
        """
        res = set([])
        for parent in self.parents[step_id]:
            res.add(parent)
            res.update(self.all_ancestors(parent))
        return res
