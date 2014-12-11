"""
This module defines exporters for export of schedules to gantt charts
"""

import matplotlib.pyplot as pl
from StringIO import StringIO

from manuallabour.exporters.common import ScheduleExporterBase

class GanttExporter(ScheduleExporterBase):
    """
    Exporter to export schedules to gantt charts in svg format.
    """
    def export(self,schedule,store,path,**kwargs):
        ScheduleExporterBase.export(self,schedule,store,path,**kwargs)

        for i,step in enumerate(schedule.steps):
            pl.plot([
                step.start.total_seconds(),
                step.stop.total_seconds(),
            ],[i,i],"b-")
            pl.plot([
                step.stop.total_seconds(),
                step.waiting.total_seconds(),
            ],[i,i],"r:")
        pl.yticks(
            [i for i,_ in enumerate(schedule.steps)],
            [step.dereference(store)["title"] for step in schedule.steps]
        )
        pl.ylim((-1,len(schedule.steps)))

        pl.xlabel('t [s]')

        pl.savefig(path,format='svg',bbox_inches='tight',pad_inches=0.5)

    def render(self,schedule,store,**kwargs):
        ScheduleExporterBase.render(self,schedule,store,**kwargs)

        for i,step in enumerate(schedule.steps):
            pl.plot([
                step.start.total_seconds(),
                step.stop.total_seconds(),
            ],[i,i],"b-")
            pl.plot([
                step.stop.total_seconds(),
                step.waiting.total_seconds(),
            ],[i,i],"r:")
        pl.yticks(
            [i for i,_ in enumerate(schedule.steps)],
            [step.dereference(store)["title"] for step in schedule.steps]
        )
        pl.ylim((-1,len(schedule.steps)+1))

        pl.xlabel('t [s]')

        out = StringIO()

        pl.savefig(out,format='svg',bbox_inches='tight',pad_inches=0.5)

        res =  out.getvalue()
        out.close()

        return res
