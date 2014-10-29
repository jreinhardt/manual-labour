from manuallabour.exporters.common import ExporterBase, MarkupBase
from jinja2 import Environment, PackageLoader
from os.path import join, basename, splitext, exists, dirname, relpath
from shutil import rmtree,copytree
from os import makedirs, remove
from codecs import open
import pkg_resources

class HTMLMarkup(MarkupBase):
    """
    Markup for HTML export
    """
    def part(self,obj,text):
        return text or obj.name
    def tool(self,obj,text):
        return text or obj.name
    def result(self,obj,text):
        return text or obj.name
    def image(self,res,url,text):
        return "<img src='%s' alt='%s'>" % (url,res.alt)
    def file(self,res,url,text):
        return "<a href='%s'>%s</a>" % (url,text or res.filename)

class SinglePageHTMLExporter(ExporterBase):
    def __init__(self,layout):
        ExporterBase.__init__(self,HTMLMarkup())
        self.layout = layout
        self.env = Environment(
            loader=PackageLoader(
                'manuallabour.layouts.html_single.%s' % layout,
                package_path='template'
            )
        )

    def export(self,schedule,path):
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

        parts = []
        for ref in schedule.parts.values():
            part = store.get_obj(ref.obj_id)
            part_dict = part.as_dict()
            part_dict["images"] = list(
                (ref,store.get_res(ref.res_id),store.get_res_url(ref.res_id))
                    for ref in part.images
            )
            part_dict["quantity"] = ref.quantity
            part_dict["optional"] = ref.optional
            parts.append(part_dict)

        tools = []
        for ref in schedule.tools.values():
            tool = store.get_obj(ref.obj_id)
            tool_dict = tool.as_dict()
            tool_dict["images"] = list(
                (ref,store.get_res(ref.res_id),store.get_res_url(ref.res_id))
                    for ref in tool.images
            )
            tool_dict["quantity"] = ref.quantity
            tool_dict["optional"] = ref.optional
            tools.append(tool_dict)

        steps = []
        for step in schedule.steps:
            step_dict = step.as_dict()
            step_dict["step_nr"] = step.step_idx + 1
            step_dict["description"] = self.markup.markup(
                step,
                store,
                step_dict["description"]
            )
            step_dict["attention"] = self.markup.markup(
                step,
                store,
                step_dict.get("attention","")
            )
            step_dict["parts"] = dict(
                (ref,store.get_obj(ref.obj_id)) for ref in step.parts.values()
            )
            step_dict["tools"] = dict(
                (ref,store.get_obj(ref.obj_id)) for ref in step.tools.values()
            )
            step_dict["results"] = dict(
                (ref,store.get_obj(ref.obj_id))
                    for ref in step.results.values()
            )
            step_dict["files"] = list(
                (ref,store.get_res(ref.res_id),store.get_res_url(ref.res_id))
                    for ref in step.files.values()
            )
            step_dict["images"] = list(
                (ref,store.get_res(ref.res_id),store.get_res_url(ref.res_id))
                    for ref in step.images.values()
            )
            steps.append(step_dict)

        template = self.env.get_template('template.html')

        with open(join(path,'out.html'),'w','utf8') as fid:
            fid.write(
                template.render(
                    title = "Title",
                    schedule = schedule,
                    parts = parts,
                    tools = tools,
                    steps = steps
                )
            )
