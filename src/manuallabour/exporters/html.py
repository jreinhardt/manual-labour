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
This module defines exporters for export of schedules to HTML and other
classes related to this task.
"""
from manuallabour.exporters.common import ScheduleExporterBase, MarkupBase
from jinja2 import Environment, FileSystemLoader
from os.path import join,  exists
from shutil import rmtree,copytree
from os import remove
# pylint: disable=W0622
from codecs import open

class HTMLMarkup(MarkupBase):
    """
    Markup for HTML export
    """
    def __init__(self,store):
        MarkupBase.__init__(self)
        self.store = store
    def _handle_obj(self,obj,text):
        if obj["images"]:
            url = self.store.get_blob_url(obj["images"][0]["blob_id"])
            return "<a href='%s'>%s</a>" % (url,text or obj["name"])
        else:
            return text or obj["name"]
    def part(self,obj,text):
        return self._handle_obj(obj,text)
    def tool(self,obj,text):
        return self._handle_obj(obj,text)
    def result(self,obj,text):
        return self._handle_obj(obj,text)
    def image(self,res,text):
        return "<img src='%s' alt='%s'>" % (res["url"],res["alt"])
    def file(self,res,text):
        return "<a href='%s'>%s</a>" % (res["url"],text or res["filename"])

class SinglePageHTMLExporter(ScheduleExporterBase):
    """
    Exporter to export schedules into a single HTML page.
    """
    def __init__(self,layout_path):
        ScheduleExporterBase.__init__(self)
        self.layout_path = layout_path
        self.env = Environment(loader=FileSystemLoader(layout_path))

    def export(self,schedule,store,path,**kwargs):
        ScheduleExporterBase.export(self,schedule,store,path,**kwargs)
        #clean up output dir
        if exists(join(path)):
            rmtree(join(path))

        #copy over stuff
        copytree(self.layout_path,path)
        remove(join(path,'template.html'))

        with open(join(path,'out.html'),'w','utf8') as fid:
            fid.write(self.render(schedule,store,**kwargs))

    def render(self,schedule,store,**kwargs):
        ScheduleExporterBase.render(self,schedule,store,**kwargs)

        #prepare stuff for rendering
        markup = HTMLMarkup(store)

        bom = schedule.collect_bom(store)
        sourcefiles = schedule.collect_sourcefiles(store)
        parts = [ref.dereference(store) for ref in bom["parts"].values()]
        tools = [ref.dereference(store) for ref in bom["tools"].values()]

        steps = []
        for step in schedule.steps:
            steps.append(step.markup(store,markup))

        template = self.env.get_template('template.html')

        #pylint: disable=E1103
        return template.render(
            doc = kwargs,
            schedule = schedule,
            sourcefiles = sourcefiles,
            parts = parts,
            tools = tools,
            steps = steps
            )
