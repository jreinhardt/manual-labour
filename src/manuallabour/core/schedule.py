"""
This module defines the Schedule class and related classes
"""
import jsonschema
from datetime import timedelta

from manuallabour.core.common import ReferenceBase, load_schema, SCHEMA_DIR,\
    graphviz_add_obj_edges

class BOMReference(ReferenceBase):
    """
    An object with counters.
    """
    _schema = load_schema(SCHEMA_DIR,'references.json')["bom_ref"]
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        ReferenceBase.__init__(self,**kwargs)
    def dereference(self,store):
        res = {}
        res.update(self._kwargs)
        res.update(self._calculated)
        obj = store.get_obj(self.obj_id)
        res.update(obj._kwargs)
        res.update(obj._calculated)
        res["images"] = [ref.dereference(store) for ref in res["images"]]
        return res

class ScheduleStep(ReferenceBase):
    """
    Step used in a Schedule
    """

    _schema = load_schema(SCHEMA_DIR,'references.json')["schedule_step"]
    _validator = jsonschema.Draft4Validator(_schema)
    def __init__(self,**kwargs):
        ReferenceBase.__init__(self,**kwargs)

        self._calculated["step_nr"] = self.step_idx + 1
        for time in ["start","stop"]:
            if time in kwargs:
                self._calculated[time] = timedelta(**kwargs[time])
        if ("start" in kwargs) != ("stop" in kwargs):
            raise ValueError("Both or none of start and stop must be given")

    def dereference(self,store):
        res = {}
        res.update(self._kwargs)
        res.update(self._calculated)
        step = store.get_step(self.step_id)
        res.update(step.dereference(store))
        return res

    def markup(self,store,markup):
        """
        Dereference the reference and markup all strings with the Markup
        Object markup.
        """

        res = self.dereference(store)
        step = store.get_step(self.step_id)
        res["description"] = markup.markup(step,store,res["description"])
        res["attention"] = markup.markup(step,store,res["attention"])
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

        self.steps = []
        for step in steps:
            self.steps.append(ScheduleStep(**step))

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
            count["optional"] -= count["quantity"]
            self.tools[obj_id] = BOMReference(obj_id=obj_id,**count)

        for obj_id,count in parts.iteritems():
            if count["quantity"] > 0 or count["optional"] > 0:
                self.parts[obj_id] = BOMReference(obj_id=obj_id,**count)

    def to_svg(self,path,with_objects=False,with_resources=False):
        """
        Render schedule structure to svg file
        """
        import pygraphviz as pgv

        graph = pgv.AGraph(directed=True)

        #Nodes
        for ref in self.steps:
            s_id = 's_' + str(ref.step_nr)
            step_dict = ref.dereference(self.store)
            graph.add_node(s_id,label=step_dict["title"])
            if ref.step_nr > 1:
                graph.add_edge('s_' + str(ref.step_nr - 1),s_id)

        if with_objects:
            for o_id, obj in self.store.iter_obj():
                o_id = 'o_' + o_id
                graph.add_node(o_id,label=obj.name,shape='rectangle')

        if with_resources:
            for r_id, res, _ in self.store.iter_res():
                r_id = 'r_' + r_id
                graph.add_node(r_id,label=res.res_id[:6],shape='diamond')

        #edges
        for ref in self.steps:
            s_id = 's_' + str(ref.step_nr)
            if ref.step_nr > 1:
                graph.add_edge('s_' + str(ref.step_nr - 1),s_id)

        if with_objects:
            for ref in self.steps:
                s_id = 's_' + str(ref.step_nr)
                step_dict = ref.dereference(self.store)

                args = dict(
                    attr={'color' : 'blue'},
                    opt={'style' : 'dashed'},
                    res=with_resources
                )
                graphviz_add_obj_edges(graph,s_id,step_dict["parts"],**args)

                args["attr"] = {'color' : 'red'}
                graphviz_add_obj_edges(graph,s_id,step_dict["tools"],**args)

                args["attr"] = {'color' : 'brown'}
                graphviz_add_obj_edges(graph,s_id,step_dict["results"],**args)

        if with_resources:
            for ref in self.steps:
                s_id = 's_' + str(ref.step_nr)
                step = self.store.get_step(ref.step_id)

                for res in step.files.values():
                    graph.add_edge('r_' + res.res_id,s_id,color='orange')
                for res in step.images.values():
                    graph.add_edge('r_' + res.res_id,s_id,color='green')

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
    waiting = {}

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
            print cand_dict
            cand_stop = cand_start + cand_dict["duration"].total_seconds()
            if best_cand is None or cand_stop < best_cand[3]:
                best_cand = (alias,cand,cand_start,cand_stop)

        #schedule it
        # pylint: disable=W0633
        alias,cand,cand_start,cand_stop = best_cand
        scheduled[alias] = dict(
            step_id=cand.step_id,
            start = dict(seconds=int(cand_start)),
            stop = dict(seconds=int(cand_stop)),
            step_idx = len(scheduled)
        )
        possible.pop(alias)

    return sorted(scheduled.values(),key=lambda x: x["step_idx"])
