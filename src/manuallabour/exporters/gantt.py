# Manual labour - a library for step-by-step instructions
# Copyright (C) 2014 Johannes Reinhardt <jreinhardt@ist-dein-freund.de>
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#  USA

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
