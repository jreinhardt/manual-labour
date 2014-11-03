"""
Common Interfaces for exporters and related classes
"""
import re
from manuallabour.core.common import load_schema
from pkg_resources import resource_filename

import jsonschema

SCHEMA_DIR =  resource_filename('manuallabour.exporters','schema')

ML_FUNC = re.compile(r'{{\s*([a-z]*)\(([^,]*?)(,[^\)]*)?\)\s*}}')

# pylint: disable=R0921
class MarkupBase(object):
    """
    Interface for Markup objects
    """
    def markup(self,step,store,string):
        """
        Markup string with informations from the Step step and the Store
        store by expanding the {{func(...)}} constructs into something that
        is appropriate for the output format.
        """
        return ML_FUNC.sub(lambda m: self._output_ml_func(m,step,store),string)

    def _output_ml_func(self,match,step,store):
        #determine callback
        func = match.group(1)
        callback = getattr(self,func)

        #collect additional arguments
        kwargs = {}
        if not match.group(3) is None:
            #first comma is contained in group, skip empty arg
            for arg in match.group(3).split(',')[1:]:
                key,val = arg.split('=')
                kwargs[key] = val

        #get the resource or object
        if func in ["part","tool","result"]:
            if func == "part":
                obj = step.parts[match.group(2)].dereference(store)
            elif func == "tool":
                obj = step.tools[match.group(2)].dereference(store)
            elif func == "result":
                obj = step.results[match.group(2)].dereference(store)
            return callback(obj,kwargs.get("text",""))
        elif func in ["image","file"]:
            if func == "image":
                res = step.images[match.group(2)].dereference(store)
            elif func == "file":
                res = step.files[match.group(2)].dereference(store)
            return callback(res,kwargs.get("text",""))
        else:
            raise ValueError("Unknown callback %s" % func)

    def part(self,obj,text):
        """
        Callback for expanding a {{part(...)}} construct
        """
        raise NotImplementedError
    def tool(self,obj,text):
        """
        Callback for expanding a {{tool(...)}} construct
        """
        raise NotImplementedError
    def result(self,obj,text):
        """
        Callback for expanding a {{result(...)}} construct
        """
        raise NotImplementedError
    def image(self,res,text):
        """
        Callback for expanding a {{image(...)}} construct
        """
        raise NotImplementedError
    def file(self,res,text):
        """
        Callback for expanding a {{file(...)}} construct
        """
        raise NotImplementedError

# pylint: disable=R0921
class ExporterBase(object):
    """
    Interface for Exporter classes.
    """
    _schema = load_schema(SCHEMA_DIR,"export_data.json")
    _validator = jsonschema.Draft4Validator(_schema)
    def export(self,_1,_2,**kwargs):
        """
        Export the schedule into the format provided by the exporter and
        store the result in path. Additional data for the export is given in
        kwargs
        """
        self._validator.validate(kwargs)
