#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2010 José de Paula Eufrásio Júnior <jose.junior@gmail.com>
#
# This file is part of cgrouptools.
#
# cgrouptools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cgrouptools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with cgrouptools.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
from debathena.metrics import connector
from libcgrouptool.skel import Cgroup, CgroupError
from cgrouptoold.utils import CgroupToolDaemonError

class Engine(object):
    """docstring for Engine"""
    def __init__(self, log):
        self.enabled = False
        self.name = None
        self.log = log
        self.debug, self.info, self.crit = log.debug, log.info, log.critical

    def resolve_name(self, pid):
        exelink = os.path.join('/proc/', str(pid), 'exe')
        if os.path.exists(exelink):
            name = os.readlink(exelink)
        else:
            # name vanished too fast
            name = None
        return name

class TTY(Engine):
    """Simple engine that will create a separate cgroup for each process
    that owns a TTY/PTY
    """

    def __init__(self, log):
        Engine.__init__(self, log)

    def check_stdin(self, pid):
        """Checks if the stdin of a process is connected to a terminal file
        descriptor
        """

        fdpath = os.path.join('/proc', str(pid), 'fd/1')
        if os.path.exists(fdpath):
            stdin = os.readlink(fdpath)
            if (stdin.find('pts') >= 0  or
                stdin.find('tty') >= 0):
                return True
            else:
                return False
        else:
                self.debug("Process %s vanished too fast" % pid)
                raise CgroupToolDaemonError("Process vanished too fast")

    def new_exec(self, pid):
        """Receives the pid from a new exec() and decides if it should be put
        on a new cgroup. In case it does, starts the process to create the
        cgroup and organize the processes there.
        """

        name = self.resolve_name(pid)
        try:
            if self.check_stdin(pid):
                self.debug("PID %s/%s connected to terminal" % (pid, name))
            else:
                self.debug("PID %s/%s NOT connected to a terminal" % (pid, name))
        except CgroupToolDaemonError:
            # Expected in case process vanish too far, just ignore they
            pass

    def new_exit(self, pid):
        """docstring for exit"""

        self.debug("PID %s exited" % pid)