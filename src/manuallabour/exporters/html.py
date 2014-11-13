"""
This module defines exporters for export of schedules to HTML and other
classes related to this task.
"""
from manuallabour.exporters.common import ExporterBase, MarkupBase
from jinja2 import Environment, PackageLoader
from os.path import join,  exists
from shutil import rmtree,copytree
from os import remove
# pylint: disable=W0622
from codecs import open
import pkg_resources

class HTMLMarkup(MarkupBase):
    """
    Markup for HTML export
    """
    def __init__(self,store):
        self.store = store
    def _handle_obj(self,obj,text):
        if obj["images"]:
            url = self.store.get_res_url(obj["images"][0]["res_id"])
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

class SinglePageHTMLExporter(ExporterBase):
    """
    Exporter to export schedules into a single HTML page.
    """
    def __init__(self,layout):
        ExporterBase.__init__(self)
        self.layout = layout
        self.env = Environment(
            loader=PackageLoader(
                'manuallabour.layouts.html_single.%s' % layout,
                package_path='template'
            )
        )

    def export(self,schedule,path,**kwargs):
        ExporterBase.export(self,schedule,path,**kwargs)
        #clean up output dir
        if exists(join(path)):
            rmtree(join(path))

        #copy over stuff
        layout_path = pkg_resources.resource_filename(
            'manuallabour.layouts.html_single.%s' % self.layout,
            'template')
        copytree(layout_path,path)
        remove(join(path,'template.html'))

        #prepare stuff for rendering
        store = schedule.store
        markup = HTMLMarkup(store)

        parts = [ref.dereference(store) for ref in schedule.parts.values()]
        tools = [ref.dereference(store) for ref in schedule.tools.values()]

        steps = []
        for step in schedule.steps:
            steps.append(step.markup(store,markup))

        template = self.env.get_template('template.html')

        with open(join(path,'out.html'),'w','utf8') as fid:
            fid.write(
                #pylint: disable=E1103
                template.render(
                    doc = kwargs,
                    schedule = schedule,
                    parts = parts,
                    tools = tools,
                    steps = steps
                )
            )

    def render(self,schedule,**kwargs):
        ExporterBase.render(self,schedule,**kwargs)

        #prepare stuff for rendering
        store = schedule.store
        markup = HTMLMarkup(store)

        parts = [ref.dereference(store) for ref in schedule.parts.values()]
        tools = [ref.dereference(store) for ref in schedule.tools.values()]

        steps = []
        for step in schedule.steps:
            steps.append(step.markup(store,markup))

        template = self.env.get_template('template.html')

        return template.render(
            doc = kwargs,
            schedule = schedule,
            parts = parts,
            tools = tools,
            steps = steps
            )
