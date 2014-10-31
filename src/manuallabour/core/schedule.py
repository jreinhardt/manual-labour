"""
This module defines the Schedule class and related classes
"""
from datetime import timedelta

import jsonschema

import manuallabour.core.common as common
from manuallabour.core.common import DataStruct, load_schema, SCHEMA_DIR

TYPES = {
    "timedelta" : (timedelta,),
    "objref" : (common.ObjectReference,),
    "resref" : (common.ResourceReference,)
}

class BOMReference(DataStruct):
    """
    An object with counters.
    """
    _schema = load_schema(SCHEMA_DIR,'bom_ref.json')
    _validator = jsonschema.Draft4Validator(_schema,types=TYPES)

    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)
    def dereference(self,store):
        res = self.as_dict(full=True)
        res.update(store.get_obj(self.obj_id).as_dict())
        res["images"] = [ref.dereference(store) for ref in res["images"]]
        return res

class ScheduleStep(DataStruct):
    """
    Step used in a Schedule
    """

    _schema = load_schema(SCHEMA_DIR,'schedule_step.json')
    _validator = jsonschema.Draft4Validator(_schema, types=TYPES)
    def __init__(self,**kwargs):
        DataStruct.__init__(self,**kwargs)

        self._calculated["step_nr"] = self.step_idx + 1

        for res in self.results.values():
            assert res.created

        if not (self.start is None or self.duration is None):
            self._calculated["stop"] = self.start + self.duration
    def markup(self,store,markup):
        res = self.as_dict(full=True)
        res["description"] = markup.markup(self,store,res["description"])
        res["attention"] = markup.markup(self,store,res["attention"])
        for nsp in ["parts","tools","results","images","files"]:
            res[nsp] = [ref.dereference(store) for ref in res[nsp].values()]
        return res

class Schedule(object):
    """
    Container to hold a sequence of steps
    """
    def __init__(self,steps,store,start=None):
        """
        Initialize the Schedule with a sequence of Graph Steps and a store
        for all needed objects and resources.  If it is a timed schedule, a
        dict mapping ids to start timedeltas must be given
        """
        self.store = store

        self.steps = []
        i = 0
        for step in steps:
            if start is None:
                self.steps.append(
                    ScheduleStep(
                        step_idx = i,
                        **step.as_dict()
                    )
                )
            else:
                step_id = step.step_id
                t_start = start[step_id]
                self.steps.append(
                    ScheduleStep(
                        step_idx = i,
                        start = t_start,
                        **step.as_dict()
                    )
                )
            i += 1

        #reverse lookup
        self.id_to_nr = {}
        for step in self.steps:
            self.id_to_nr[step.step_id] = step.step_nr

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
            for tool in step.tools.values():
                if not tool.obj_id in tools:
                    tools[tool.obj_id] = {
                        "quantity" : 0,
                        "optional" : 0,
                        "current" : 0,
                        "current_opt" : 0,
                    }
                count = tools[tool.obj_id]
                if tool.created:
                    count["current"] -= tool.quantity
                    count["current_opt"] -= tool.quantity
                else:
                    if tool.optional:
                        count["current_opt"] = + tool.quantity
                    else:
                        count["current"] = + tool.quantity
                        count["current_opt"] = + tool.quantity
                count["quantity"] = max(count["quantity"],count["current"])
                count["optional"] = max(count["optional"],count["current_opt"])

            for part in step.parts.values() + step.results.values():
                obj_id = part.obj_id
                if not obj_id in parts:
                    parts[obj_id] = {
                        "optional" : 0,
                        "quantity" : 0
                    }

                if part.created:
                    parts[obj_id]["quantity"] -= part.quantity
                else:
                    if part.optional:
                        parts[obj_id]["optional"] += part.quantity
                    else:
                        parts[obj_id]["quantity"] += part.quantity

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

    if not graph.timing:
        raise ValueError(
            "This graph can not be scheduled greedily due to "
            "missing timing information"
        )

    #find set of steps required for target
    if targets is None:
        steps = set(graph.steps.values())
    else:
        steps = set([])
        for target in targets:
            steps.add(target)
            steps.update(graph.all_ancestors(target))
        steps = set(graph.steps[s] for s in steps)

    time = 0
    possible = {}
    scheduled = {}
    start = {}
    waiting = {}
    ids = []

    while len(scheduled) < len(steps):
        #find possible next steps
        for step in steps:
            s_id = step.step_id
            if s_id in scheduled:
                continue
            for dep in graph.parents[s_id]:
                if not dep in scheduled:
                    break
            else:
                possible[s_id] = step

        #from these find the step with minimal end time
        best_cand = None
        for c_id,cand in possible.iteritems():
            cand_start = time
            #find earliest possible starting time
            for dep in graph.parents[c_id]:
                if dep in waiting and waiting[dep] > cand_start:
                    cand_start = waiting[dep]
            cand_stop = cand_start + cand.duration.total_seconds()
            if best_cand is None or cand_stop < best_cand[3]:
                best_cand = (c_id,cand,cand_start,cand_stop)

        #schedule it
        # pylint: disable=W0633
        c_id,cand,cand_start,cand_stop = best_cand

        start[c_id] = timedelta(seconds=cand_start)
        scheduled[c_id] = cand
        ids.append(c_id)

        possible.pop(c_id)
        time = cand_stop

    return [scheduled[i] for i in ids], start
