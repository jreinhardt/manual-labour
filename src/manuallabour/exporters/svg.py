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
This module defines exporters for export of schedules and Graphs to SVG.
"""

import manuallabour.exporters.common as common
import pygraphviz as pgv
import os
import tempfile

def graphviz_add_obj_edges(graph,s_id,objs,**kwargs):
    """
    add objects in the list objs to graph.

    kwargs:
    attr: dict of edge attributes
    opt: additional edge attributes for optional objects
    res: also add links to resources referenced by this object
    """
    for obj in objs.values():
        o_id = 'o_' + obj["obj_id"]
        attrs = {}
        attrs.update(kwargs["attr"])
        if obj["optional"] and "opt" in kwargs:
            attrs.update(kwargs["opt"])
        attrs["label"] = obj["quantity"]
        if obj["created"]:
            graph.add_edge(s_id,o_id,**attrs)
        else:
            graph.add_edge(o_id,s_id,**attrs)
        if kwargs["res"]:
            for img in obj["images"]:
                graph.add_edge('r_' + img["blob_id"],o_id)


class GraphSVGExporter(common.GraphExporterBase):
    """
    Exporter to export graphs to svg files.
    """
    def __init__(self,with_objects=False,with_resources=False):
        common.GraphExporterBase.__init__(self)
        self.with_objects = with_objects
        self.with_resources = with_resources

    def export(self,graph,store,path,**kwargs):
        common.GraphExporterBase.export(self,graph,store,path,**kwargs)

        result = pgv.AGraph(directed=True,strict=False)

        steps = {}
        for ref in graph.steps:
            steps[ref.step_id] = ref.dereference(store)

        #Nodes
        for alias,step_dict in steps.iteritems():
            s_id = "s_" + alias
            result.add_node(s_id,label=step_dict["title"])

        if self.with_objects:
            for o_id, obj in store.iter_obj():
                o_id = 'o_' + o_id
                result.add_node(o_id,label=obj.name,shape='rectangle')

        if self.with_resources:
            for blob_id in store.iter_blob():
                r_id = 'r_' + blob_id
                result.add_node(r_id,label=blob_id[:6],shape='diamond')

        #Edges
        for alias,children in graph.children.iteritems():
            for child in children:
                result.add_edge('s_' + alias,'s_' + child)

        if self.with_objects:
            for alias,step_dict in steps.iteritems():
                s_id = 's_' + alias

                args = dict(
                    attr={'color' : 'blue'},
                    opt={'style' : 'dashed'},
                    res=self.with_resources
                )
                graphviz_add_obj_edges(result,s_id,step_dict["parts"],**args)

                args["attr"] = {'color' : 'red'}
                graphviz_add_obj_edges(result,s_id,step_dict["tools"],**args)

                args["attr"] = {'color' : 'brown'}
                graphviz_add_obj_edges(result,s_id,step_dict["results"],**args)

        if self.with_resources:
            for alias,step_dict in steps.iteritems():
                s_id = 's_' + alias

                for res in step_dict["files"].values():
                    result.add_edge('r_' + res["blob_id"],s_id,color='orange')
                for res in step_dict["images"].values():
                    result.add_edge('r_' + res["blob_id"],s_id,color='green')

        result.draw(path,prog='dot')

    def render(self,graph,store,**kwargs):
        common.GraphExporterBase.render(self,graph,store,**kwargs)

        _filehandle,filename = tempfile.mkstemp(suffix=".svg")
        self.export(graph,store,filename,**kwargs)
        result = open(filename).read()
        os.remove(filename)
        return result


class ScheduleSVGExporter(common.ScheduleExporterBase):
    """
    Exporter to export schedules to svg files.
    """
    def __init__(self,with_objects=False,with_resources=False):
        common.ScheduleExporterBase.__init__(self)
        self.with_objects = with_objects
        self.with_resources = with_resources

    def export(self,schedule,store,path,**kwargs):
        common.ScheduleExporterBase.export(self,schedule,store,path,**kwargs)

        result = pgv.AGraph(directed=True,strict=False)

        #Nodes
        for ref in schedule.steps:
            s_id = 's_' + str(ref.step_nr)
            step_dict = ref.dereference(store)
            result.add_node(s_id,label=step_dict["title"])
            if ref.step_nr > 1:
                result.add_edge('s_' + str(ref.step_nr - 1),s_id)

        if self.with_objects:
            for o_id, obj in store.iter_obj():
                o_id = 'o_' + o_id
                result.add_node(o_id,label=obj.name,shape='rectangle')

        if self.with_resources:
            for blob_id in store.iter_blob():
                result.add_node(blob_id,label=blob_id[:6],shape='diamond')

        #edges
        for ref in schedule.steps:
            s_id = 's_' + str(ref.step_nr)
            if ref.step_nr > 1:
                result.add_edge('s_' + str(ref.step_nr - 1),s_id)

        if self.with_objects:
            for ref in schedule.steps:
                s_id = 's_' + str(ref.step_nr)
                step_dict = ref.dereference(store)

                args = dict(
                    attr={'color' : 'blue'},
                    opt={'style' : 'dashed'},
                    res=self.with_resources
                )
                graphviz_add_obj_edges(result,s_id,step_dict["parts"],**args)

                args["attr"] = {'color' : 'red'}
                graphviz_add_obj_edges(result,s_id,step_dict["tools"],**args)

                args["attr"] = {'color' : 'brown'}
                graphviz_add_obj_edges(result,s_id,step_dict["results"],**args)

        if self.with_resources:
            for ref in schedule.steps:
                s_id = 's_' + str(ref.step_nr)
                step = store.get_step(ref.step_id)

                for fil in step.files.values():
                    result.add_edge('r_' + fil.blob_id,s_id,color='orange')
                for img in step.images.values():
                    result.add_edge('r_' + img.blob_id,s_id,color='green')

        result.draw(path,prog='dot')


