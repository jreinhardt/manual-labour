"""
This module defines the Graph class and related classes
"""

import jsonschema

from manuallabour.core.common import ReferenceBase, load_schema, SCHEMA_DIR,\
    ContentBase

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
        """
        Collect the step_ids, obj_ids  and blob_ids that are directly or
        indirectly referenced by this graph

        returns a dict of lists
        """
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

        for ids in res:
            res[ids] = list(res[ids])

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
