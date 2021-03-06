# Manual labour - a library for step-by-step instructions
# Copyright (C) 2014 Johannes Reinhardt <jreinhardt@ist-dein-freund.de
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
This module defines the Sphinx autodoc jsonschema extension, which allows to insert automatically generated documentation about parameters from a jsonschema file
"""

import re
import json
from os.path import join
from docutils.parsers.rst.directives.tables import ListTable
from docutils import nodes, statemachine

def setup(app):
    app.add_config_value('json_schema_dir','.',True)
    app.connect('autodoc-process-docstring',preprocess_autodoc)
    app.connect('source-read',preprocess_source)

def load_schema(schema_dir,schema_name):
    """
    Load a jsonschema and dereferences JSON references by substitution.

    This allows to utilize references for mantainability and get a complete
    schema that can be used for e.g. default handling.
    """
    with open(join(schema_dir,schema_name)) as fid:
        schema = json.loads(fid.read())
    return schema

SCHEMA_RE = re.compile(r"{{([^}]*)}}")

def preprocess_source(app,docname, source):
    lines = substitute_schema(
        app,
        source[0].splitlines(),
        'Members',
        add_title=True,
        add_description=True,
        add_type=True,
        label_prefix="jsonschema-members"
    )
    source[0] = "\n".join(lines)

def preprocess_autodoc(app,what,name,obj,options,lines):
    lines[:] = substitute_schema(
        app,
        lines,
        'KW Arguments',
        label_prefix="jsonschema-args"
    )

def translate_type(schema,prefix):
    if "$ref" in schema:
        parts = schema["$ref"].split("#/")
        target = prefix + '-' + '-'.join(parts).replace('.','-')
        if len(parts) == 2:
            label = parts[1]
        else:
            label = parts[0].splitext()[0]
        return ":ref:`%s <%s>`" % (label,target)
    elif not "type" in schema:
        return None
    elif schema["type"] == "integer":
        return ":class:`int`"
    elif schema["type"] == "string":
        return ":class:`str`"
    elif schema["type"] == "array":
        return ":class:`list` of %s" % translate_type(
            schema["items"],'jsonschema-members')
    elif schema["type"] == "boolean":
        return ":class:`bool`"



def substitute_schema(app,lines,designation,add_title=False,add_description=False,add_type=False,label_prefix=""):
    result = []
    for line in lines[:]:
        match = SCHEMA_RE.match(line.strip())
        if not match is None:
            parts = match.group(1).split("#/")

            schema = load_schema(app.config.json_schema_dir,parts[0])
            if len(parts) == 2:
                schema = schema[parts[1]]

            label = label_prefix + '-' + '-'.join(parts).replace('.','-')

            result.append(".. _%s:" % label)
            result.append("")

            if add_title:
                result.append(schema['title'])
                result.append('"'*len(schema['title']))

            if add_description:
                result.append("")
                result.append(schema['description'])
                result.append("")

            if schema["type"] == "object":
                if add_type:
                    result.append(":Type: :class:`dict`")
                result.append(":%s:" % designation)
                for name, sschema in schema.get('properties',{}).iteritems():
                    type = translate_type(sschema,'jsonschema-members')
                    if name in schema.get('required',[]):
                        opt = 'mandatory'
                        result.append("  * %s (%s), %s (%s)" % (name,type,sschema.get('description'),opt))
                        result.append("")
                for name, sschema in schema.get('properties',{}).iteritems():
                    type = translate_type(sschema,'jsonschema-members')
                    if not name in schema.get('required',[]):
                        opt = 'optional'
                        result.append("  * %s (%s), %s (%s)" % (name,type,sschema.get('description'),opt))
                        result.append("")
                for pattern, sschema in schema.get('patternProperties',{}).iteritems():
                    type = translate_type(sschema,'jsonschema-members')
                    result.append("  * *%s* (%s)" % (pattern,type))
                    result.append("")
            elif schema["type"] == "string":
                if add_type:
                    result.append(":Type: %s" % schema["type"])
                result.append(":Pattern: `%s`" % schema["pattern"])

            result.append("")
        else:
            result.append(line)
    return result
