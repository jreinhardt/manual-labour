import re

ML_FUNC = re.compile(r'{{\s*([a-z]*)\(([^,]*?)(,[^\)]*)?\)\s*}}')

class MarkupBase(object):
    """
    Interface for Markup objects
    """
    def markup(self,step,store,string):
        return ML_FUNC.sub(lambda m: self.output_ml_func(m,step,store),string)

    def output_ml_func(self,m,step,store):
        #determine callback
        func = m.group(1)
        callback = getattr(self,func)

        #collect additional arguments
        kwargs = {}
        if not m.group(3) is None:
            #first comma is contained in group, skip empty arg
            for arg in m.group(3).split(',')[1:]:
                k,v = arg.split('=')
                kwargs[k] = v

        #get the resource or object
        if func in ["part","tool","result"]:
            if func == "part":
                obj = store.get_obj(step.parts[m.group(2)].obj_id)
            elif func == "tool":
                obj = store.get_obj(step.tools[m.group(2)].obj_id)
            elif func == "result":
                obj = store.get_obj(step.results[m.group(2)].obj_id)
            return callback(obj,kwargs.get("text",""))
        elif func in ["image","file"]:
            if func == "image":
                res_id = step.images[m.group(2)].res_id
            elif func == "file":
                res_id = step.files[m.group(2)].res_id
            res = store.get_res(res_id)
            url = store.get_res_url(res_id)
            return callback(res,url,kwargs.get("text",""))
        else:
            raise ValueError("Unknown callback %s" % func)

    def part(self,obj,text):
        raise NotImplementedError
    def tool(self,obj,text):
        raise NotImplementedError
    def result(self,obj,text):
        raise NotImplementedError
    def image(self,res,url,text):
        raise NotImplementedError
    def file(self,res,url,text):
        raise NotImplementedError

class ExporterBase(object):
    def export(self,schedule,path):
        raise NotImplementedError