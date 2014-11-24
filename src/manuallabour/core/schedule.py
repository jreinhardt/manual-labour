"""
This module defines the Schedule class and related classes
"""
import jsonschema
from datetime import timedelta

from manuallabour.core.common import ReferenceBase, load_schema, SCHEMA_DIR,\
    ContentBase

class BOMReference(ReferenceBase):
    """
    An object with counters.
    """
    _schema = load_schema(SCHEMA_DIR,'references.json')["bom_ref"]
    _validator = jsonschema.Draft4Validator(_schema)

    def __init__(self,**kwargs):
        ReferenceBase.__init__(self,**kwargs)
    def dereference(self,store):
        res = ReferenceBase.dereference(self,store)
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
            if time in kwargs and kwargs[time]:
                self._calculated[time] = timedelta(**kwargs[time])
            else:
                self._calculated[time] = None
        if ("start" in kwargs) != ("stop" in kwargs):
            raise ValueError("Both or none of start and stop must be given")

    def dereference(self,store):
        res = ReferenceBase.dereference(self,store)
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

class Schedule(ContentBase):
    """
    Container to hold a sequence of steps
    """
    _schema = load_schema(SCHEMA_DIR,'schedule.json')
    _validator = jsonschema.Draft4Validator(_schema)
    _id = "sched_id"

    def __init__(self,**kwargs):
        ContentBase.__init__(self,**kwargs)

        self._calculated["steps"] = []
        for step in kwargs["steps"]:
            self._calculated["steps"].append(ScheduleStep(**step))

    def collect_bom(self,store):
        """
        Collect the list of required materials and tools for this schedule.
        The resulting dicts are suitable to create BOMReferences.
        """
        tools = {}
        parts = {}
        for ref in self.steps:
            step = store.get_step(ref.step_id)
            for tool in step.tools.values():
                count = tools.setdefault(tool.obj_id,{
                    "obj_id" : tool.obj_id,
                    "quantity" : 0,
                    "optional" : 0,
                    "current" : 0,
                    "current_opt" : 0,
                })

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

            for obj in step.parts.values() + step.results.values():
                count = parts.setdefault(obj.obj_id,{
                    "obj_id" : obj.obj_id,
                    "optional" : 0,
                    "quantity" : 0
                })

                if obj.created:
                    count["quantity"] -= obj.quantity
                else:
                    if obj.optional:
                        count["optional"] += obj.quantity
                    else:
                        count["quantity"] += obj.quantity

        result = {"parts" : {}, "tools" : {}}

        for obj_id,count in tools.iteritems():
            count.pop("current")
            count.pop("current_opt")
            count["optional"] -= count["quantity"]
            if count["quantity"] > 0 or count["optional"] > 0:
                result["tools"][obj_id] = BOMReference(**count)

        for obj_id,count in parts.items():
            if count["quantity"] > 0 or count["optional"] > 0:
                result["parts"][obj_id] = BOMReference(**count)

        return result


def schedule_greedy(graph, store, targets = None):
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

    for step in steps:
        step_dict = step.dereference(store)
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
        for step in steps:
            if step.step_id in scheduled:
                continue
            for dep in graph.parents[step.step_id]:
                if not dep in scheduled:
                    break
            else:
                possible[step.step_id] = step

        #from these find the step with minimal end time
        best_cand = None
        for step_id,cand in possible.iteritems():
            cand_start = time
            #find earliest possible starting time
            for dep in graph.parents[step_id]:
                if dep in waiting and waiting[dep] > cand_start:
                    cand_start = waiting[dep]
            cand_dict = cand.dereference(store)
            cand_stop = cand_start + cand_dict["duration"].total_seconds()
            if best_cand is None or cand_stop < best_cand[2]:
                best_cand = (cand,cand_start,cand_stop)

        #schedule it
        # pylint: disable=W0633
        cand,cand_start,cand_stop = best_cand
        scheduled[cand.step_id] = dict(
            step_id=cand.step_id,
            start = dict(seconds=int(cand_start)),
            stop = dict(seconds=int(cand_stop)),
            step_idx = len(scheduled)
        )
        possible.pop(cand.step_id)

    return sorted(scheduled.values(),key=lambda x: x["step_idx"])
