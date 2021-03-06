# Manual labour - a library for step-by-step instructions
# Copyright (C) 2014 Johannes Reinhardt <jreinhardt@ist-dein-freund.de>
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#  USA

"""
This module defines the Graph class and related classes
"""

import jsonschema

from manuallabour.core.common import ReferenceBase, load_schema, SCHEMA_DIR,\
    ComponentBase, add_ids

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

class Graph(ComponentBase):
    """
    Container to hold a set of dependent steps

    {{graph.json}}

    :Calculated:
        * steps (:class:`dict` of :class:`~manuallabour.core.graph.GraphStep`)
          Dict mapping step_ids to GraphSteps
        * children (:class:`dict` of :class:`str`)
          Dict mapping the id of a step to the id of its children
        * parents (:class:`dict` of :class:`str`)
          Dict mapping the id of a step to id of its parents


    """
    _schema = load_schema(SCHEMA_DIR,'graph.json')
    _validator = jsonschema.Draft4Validator(_schema)
    _id = "graph_id"

    def __init__(self,**kwargs):
        ComponentBase.__init__(self,**kwargs)

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
        res = ComponentBase.dereference(self,store)
        for i, step in enumerate(res["steps"]):
            res[i] = step.dereference(store)
        return res

    def collect_ids(self,store):
        res = dict(graph_ids=set([self.graph_id]))
        for ref in self.steps:
            add_ids(res,ref.collect_ids(store))
        return res

    def all_ancestors(self,step_id):
        """ Return set with ids of all ancestor steps of step_id, i.e. all
        steps that are a direct or indirect prerequisite.

        :rtype: :class:`set` of :ref:`jsonschema-members-common-json-step_id`
        """
        res = set([])
        for parent in self.parents[step_id]:
            res.add(parent)
            res.update(self.all_ancestors(parent))
        return res
