"""
This module defines the Schedule class and related classes
"""
from datetime import timedelta

import jsonschema

import manuallabour.core.common as common
from manuallabour.core.common import ReferenceBase, DataStruct, load_schema,\
    SCHEMA_DIR

TYPES = {
    "timedelta" : (timedelta,),
    "objref" : (common.ObjectReference,),
    "resref" : (common.ResourceReference,)
}

class BOMReference(ReferenceBase):
    """
    An object with counters.
    """
    _schema = load_schema(SCHEMA_DIR,'bom_ref.json')
    _validator = jsonschema.Draft4Validator(_schema,types=TYPES)

    def __init__(self,**kwargs):
        ReferenceBase.__init__(self,**kwargs)
    def dereference(self,store):
        res = self.as_dict(full=True)
        res.update(store.get_obj(self.obj_id).as_dict())
        res["images"] = [ref.dereference(store) for ref in res["images"]]
        return res

class ScheduleStep(ReferenceBase):
    """
    Step used in a Schedule
    """

    _schema = load_schema(SCHEMA_DIR,'schedule_step_reference.json')
    _validator = jsonschema.Draft4Validator(_schema, types=TYPES)
    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)

        self._calculated["step_nr"] = self.step_idx + 1

    def dereference(self,store):
        res = self.as_dict(full=True)
        step = store.get_step(self.step_id)
        res.update(step.dereference(store))
        if res["start"] is None or res["duration"] is None:
            res["stop"] = None
        else:
            res["stop"] = res["start"] + res["duration"]
        return res

    def markup(self,store,markup):
        res = self.dereference(store)
        res["description"] = markup.markup(self,store,res["description"])
        res["attention"] = markup.markup(self,store,res["attention"])
        return res

class Schedule(object):
    """
    Container to hold a sequence of steps
    """
    def __init__(self,steps,store):
        """
        Initialize the Schedule with a sequence of ScheduleSteps and a store
        for all steps, objects and resources.
        """
        self.store = store

        self.steps = steps

        self.tools = {}
        self.parts = {}
        self._create_bom()

    def _create_bom(self):
        """
        Assemble the list of required parts and tools
        """
        tools = {}
        parts = {}
        for step in self.steps:
            step_dict = step.dereference(self.store)
            for tool in step_dict["tools"]:
                if not tool["obj_id"] in tools:
                    tools[tool["obj_id"]] = {
                        "quantity" : 0,
                        "optional" : 0,
                        "current" : 0,
                        "current_opt" : 0,
                    }
                count = tools[tool["obj_id"]]
                if tool["created"]:
                    count["current"] -= tool["quantity"]
                    count["current_opt"] -= tool["quantity"]
                else:
                    if tool["optional"]:
                        count["current_opt"] = + tool["quantity"]
                    else:
                        count["current"] = + tool["quantity"]
                        count["current_opt"] = + tool["quantity"]
                count["quantity"] = max(count["quantity"],count["current"])
                count["optional"] = max(count["optional"],count["current_opt"])

            for obj in step_dict["parts"] + step_dict["results"]:
                obj_id = obj["obj_id"]
                if not obj_id in parts:
                    parts[obj_id] = {
                        "optional" : 0,
                        "quantity" : 0
                    }

                if obj["created"]:
                    parts[obj_id]["quantity"] -= obj["quantity"]
                else:
                    if obj["optional"]:
                        parts[obj_id]["optional"] += obj["quantity"]
                    else:
                        parts[obj_id]["quantity"] += obj["quantity"]

        for obj_id,count in tools.iteritems():
            count.pop("current")
            count.pop("current_opt")
            self.tools[obj_id] = BOMReference(obj_id=obj_id,**count)

        for obj_id,count in parts.iteritems():
            if count["quantity"] > 0 or count["optional"] > 0:
                self.parts[obj_id] = BOMReference(obj_id=obj_id,**count)

    def to_svg(self,path):
        """
        Render schedule structure to svg file
        """
        import pygraphviz as pgv

        graph = pgv.AGraph(directed=True)

        #Add objects
        for o_id, obj in self.store.iter_obj():
            o_id = 'o_' + o_id
            graph.add_node(o_id,label=obj.name,shape='rectangle')

        for r_id, res, _ in self.store.iter_res():
            r_id = 'r_' + r_id
            graph.add_node(r_id,label=res.res_id[:6],shape='diamond')

        #Add nodes
        for step in self.steps:
            nr = step.step_nr
            s_id = 's_%d' % nr
            graph.add_node(s_id,label=step.title)

            #add object dependencies
            for obj in step.parts.values():
                o_id = 'o_' + obj.obj_id
                attr = {'color' : 'blue','label' : obj.quantity}
                if obj.optional:
                    attr['style'] = 'dashed'
                graph.add_edge(o_id,s_id,**attr)

                for img in self.store.get_obj(obj.obj_id).images:
                    graph.add_edge('r_' + img.res_id,o_id)

            for obj in step.tools.values():
                o_id = 'o_' + obj.obj_id
                attr = {'color' : 'red','label' : obj.quantity}
                if obj.optional:
                    attr['style'] = 'dashed'
                graph.add_edge(o_id,s_id,**attr)

                for img in self.store.get_obj(obj.obj_id).images:
                    graph.add_edge('r_' + img.res_id,o_id)

            for obj in step.results.values():
                o_id = 'o_' + obj.obj_id
                attr = {'color' : 'brown','label' : obj.quantity}
                if obj.optional:
                    attr['style'] = 'dashed'
                #results are always created
                graph.add_edge(s_id,o_id,**attr)

                for img in self.store.get_obj(obj.obj_id).images:
                    graph.add_edge('r_' + img.res_id,o_id)

            #add resource dependencies
            for res in step.files.values():
                graph.add_edge('r_' + res.res_id,s_id,color='orange')
            for res in step.images.values():
                graph.add_edge('r_' + res.res_id,s_id,color='green')

        for step in self.steps:
            #Add step dependencies
            nr = step.step_nr
            if nr > 1:
                graph.add_edge('s_%d' % (nr-1),'s_%d' % nr)

        graph.draw(path,prog='dot')

def schedule_greedy(graph, targets = None):
    """
    Scheduler that always chooses the next step such that its finish time
    is minimized. Does not take into account limited availability of tools.

    if targets is not given, schedules full graph
    """

    #find set of steps required for target
    if targets is None:
        steps = graph.steps
    else:
        steps = set([])
        for target in targets:
            steps.add(target)
            steps.update(graph.all_ancestors(target))
        steps = dict((key,graph.steps[key]) for key in steps)

    timing = True
    for step in steps.values():
        step_dict = step.dereference(graph.store)
        if step_dict["duration"] is None:
            raise ValueError(
                "This graph can not be scheduled greedily due to "
                "missing timing information"
            )

    time = 0
    possible = {}
    scheduled = {}
    start = {}
    waiting = {}
    ids = []

    while len(scheduled) < len(steps):
        #find possible next steps
        for alias,step in steps.iteritems():
            if alias in scheduled:
                continue
            for dep in graph.parents[alias]:
                if not dep in scheduled:
                    break
            else:
                possible[alias] = step

        #from these find the step with minimal end time
        best_cand = None
        for alias,cand in possible.iteritems():
            cand_start = time
            #find earliest possible starting time
            for dep in graph.parents[alias]:
                if dep in waiting and waiting[dep] > cand_start:
                    cand_start = waiting[dep]
            cand_dict = cand.dereference(graph.store)
            cand_stop = cand_start + cand_dict["duration"].total_seconds()
            if best_cand is None or cand_stop < best_cand[3]:
                best_cand = (alias,cand,cand_start,cand_stop)

        #schedule it
        # pylint: disable=W0633
        alias,cand,cand_start,cand_stop = best_cand
        scheduled[alias] = ScheduleStep(
            step_id=cand.step_id,
            start = timedelta(seconds=cand_start),
            step_idx = len(scheduled)
        )
        possible.pop(alias)

    return sorted(scheduled.values(),key=lambda x: x.step_idx)
