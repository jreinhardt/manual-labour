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
    lines = substitute_schema(app,source[0].splitlines(),'Members',add_title=True,add_description=True)
    source[0] = "\n".join(lines)

def preprocess_autodoc(app,what,name,obj,options,lines):
    lines[:] = substitute_schema(app,lines,'KW Arguments')

def translate_type(schema):
    if "$ref" in schema:
        parts = schema["$ref"].split("#/")
        target = 'jsonschema-' + '_'.join(parts).replace('.','-')
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
        return ":class:`list` of %s" % translate_type(schema["items"])


def substitute_schema(app,lines,designation,add_title=False,add_description=False):
    result = []
    for line in lines[:]:
        match = SCHEMA_RE.match(line.strip())
        if not match is None:
            parts = match.group(1).split("#/")

            schema = load_schema(app.config.json_schema_dir,parts[0])
            if len(parts) == 2:
                schema = schema[parts[1]]

            label = 'jsonschema-' + '_'.join(parts).replace('.','-')

            result.append(".. _%s:" % label)
            result.append("")

            if add_title:
                result.append(schema['title'])
                result.append("^"*len(schema['title']))

            if add_description:
                result.append("")
                result.append(schema['description'])
                result.append("")

            if schema["type"] == "object":
                result.append(":Type: :class:`dict`")
                result.append(":%s:" % designation)
                for name, sschema in schema.get('properties',{}).iteritems():
                    type = translate_type(sschema)
                    if name in schema.get('required',[]):
                        opt = 'mandatory'
                        result.append("  * %s (%s), %s (%s)" % (name,type,sschema.get('description'),opt))
                        result.append("")
                for name, sschema in schema.get('properties',{}).iteritems():
                    type = translate_type(sschema)
                    if not name in schema.get('required',[]):
                        opt = 'optional'
                        result.append("  * %s (%s), %s (%s)" % (name,type,sschema.get('description'),opt))
                        result.append("")
                for pattern, sschema in schema.get('patternProperties',{}).iteritems():
                    type = translate_type(sschema)
                    result.append("  * *%s* (%s)" % (pattern,type))
                    result.append("")
            elif schema["type"] == "string":
                result.append(":Type: %s" % schema["type"])
                result.append(":Pattern: `%s`" % schema["pattern"])

            result.append("")
        else:
            result.append(line)
    return result
