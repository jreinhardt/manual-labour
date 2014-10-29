"""
This module defines the Schedule class and related classes
"""
from datetime import timedelta

from manuallabour.core.graph import GraphStep
from manuallabour.core.common import BOMReference

class ScheduleStep(GraphStep):
    """
    Step used in a Schedule
    """
    def __init__(self,step_id,**kwargs):

        self.step_idx = kwargs.pop("step_idx")
        """ Index of this step, starting with 0"""
        self.step_nr = self.step_idx + 1
        """ Number of this step, starting with 1"""

        self.start = kwargs.pop("start",None)
        """ Time when the active part of the step starts"""
        self.stop = kwargs.pop("stop",None)
        """ Time when the active part of the step stops"""

        GraphStep.__init__(self,step_id,**kwargs)
    def as_dict(self):
        res = GraphStep.as_dict(self)
        res.pop("step_nr")
        if not self.start is None:
            res["start"] = self.start
        if not self.stop is None:
            res["stop"] = self.stop
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
                        step.step_id,
                        step_idx = i,
                        **step.as_dict()
                    )
                )
            else:
                step_id = step.step_id
                t_start = start[step_id]
                self.steps.append(
                    ScheduleStep(
                        step_id,
                        step_idx = i,
                        start = t_start,
                        stop = t_start + step.duration,
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
                obj_id = tool.obj_id
                if not obj_id in tools:
                    tools[obj_id] = {
                        "quantity" : 0,
                        "created" : 0
                    }
                if tool.created:
                    tools[obj_id]["quantity"] += tool.quantity
                else:
                    if not tool.optional:
                        tools[obj_id]["quantity"] = \
                            max(tool.quantity,tools[obj_id]["quantity"])
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

        for o_id,args in tools.iteritems():
            args["quantity"] = max(0,args["quantity"] - args.pop("created"))
            self.tools[o_id] = BOMReference(o_id,**args)

        for o_id,args in parts.iteritems():
            if args["quantity"] > 0 or args["optional"] > 0:
                self.parts[o_id] = BOMReference(o_id,**args)

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
