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

from unittest import TestCase
from os import walk
from os.path import join

class PylintTest(TestCase):
    def test_package(self):
        from pylint import epylint as lint
        errors = []
        for dirpath,_,filenames in walk('src/manuallabour'):
            for filename in filenames:
                if filename.endswith(".py"):
                    args = []
                    args.append(join(dirpath,filename))
                    args.append('--rcfile ../pylint.rc')
                    (stdout,stderr) = lint.py_run(" ".join(args),True)
                    errors.append(stderr.read())
                    errors.append(stdout.read())
        errors = "\n".join(errors).strip()
        if len(errors) > 0:
            print errors
            raise SyntaxError("PyLint has detected problems")
