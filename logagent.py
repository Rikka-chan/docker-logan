#!/usr/bin/env python

import sys
import os.path
import yaml
import glob
import tailer
import grin
import re
import uuid
from flask import Flask, render_template
from flask import request, session
from flask import make_response

from docker import Client

# -*- coding: utf-8 -*-
"""
    Logan log file viewer

    Simple log service agent to provide tailing (tailer) and 
    grep (grin) services over REST

    FIXME: No results found for expression 

    :copyright: (c) 2012 by Jonathan Holloway.
    :license: BSD-2, see LICENSE_FILE for more details.
"""
app = Flask(__name__)

configurationfile = 'logagentconfig.yaml'
config = {}
cli = Client(base_url='unix://var/run/docker.sock')
validfiles = {}


def get_container_name(container_id):
    if not container_id:
        return

    inspect = cli.inspect_container(container_id)
    return inspect.get('Name')


def get_container_id(path):
    container_id = re.search(r'(((\w)+?)(?=-json\.log))', path)
    return container_id.group(0)


def init():
    """Init configuration"""
    configfile = open(configurationfile, 'r')
    global config
    try:
        config = yaml.load(configfile)
        for item in config:
            print(item + ": " + str(config[item]))
    finally:
        configfile.close()


def link(href, text):
    """Generate a link"""
    return '<a href="' + href + '">' + text + '</a>'


def process_path(validfiles, path):
    """Process a given filesystem path and add the valid files to list"""
    # Generate URLs
    container_id = get_container_id(path)
    name = get_container_name(container_id)
    if not name or not container_id:
        return

    if os.path.getsize(path) > 0:
        size = str(os.path.getsize(path))
        name = name.replace('/', '_')
        uniquefilename = name.replace('/', '_') + "_" + str(uuid.uuid1())
        validfiles[container_id] = [path, size, name]
        return validfiles


def process_file(fn, filename, numlines):
    """Process a file using a given function and a set of arguments"""
    if filename in validfiles:
        logpath = validfiles[filename][0]

        try:
            logfile = open(logpath, 'r')
            # pass generic function name
            lines = fn(logfile, numlines)
            content = '<br>'.join(lines)
            return render_template('content.html', content=content)
        finally:
            logfile.close()
    else:
        resp = make_response(render_template('content.html'), 200)
        session['content'] = 'Refusing to process file'
        return resp


def search_for_expression(output, filepaths, validfiles, expression, grepbefore, grepafter):
    """Carry out search for expression (using grep context) on validfiles returning matching files as output"""
    options = grin.Options()
    options['before_context'] = int(grepbefore)
    options['after_context'] = int(grepafter)
    options['use_color'] = False
    options['show_filename'] = False
    options['show_match'] = True
    options['show_emacs'] = False
    options['show_line_numbers'] = True

    anchorcount = 1

    searchregexp = re.compile(expression)
    grindef = grin.GrepText(searchregexp, options)

    for file in validfiles:
        filepath = validfiles.get(file)[0]
        report = grindef.grep_a_file(filepath)
        if report:

            output += '<a name="filename' + str(anchorcount) + '"></a><h2>' + filepath + '</h2>'

            filepaths.append(filepath)
            reporttext = report.split("\n")
            for text in reporttext:
                if text:
                    output += "line " + text + "<br>"
            anchorcount += 1

    return output


@app.route("/")
def index():
    """Route: index page"""
    return list(validfiles=validfiles)


@app.route("/list/")
def list(validfiles=None):
    """Route: List all files based on directory and extension"""
    for dir in config['docker']:
        for ext in config['extensions']:
            for path in glob.iglob(dir + '/**/*.' + ext, recursive=True):
                tmpfiles = process_path(validfiles, path)
                if tmpfiles:
                    validfiles = tmpfiles

    session['grepnumlines'] = str(config['grepnumlines'])
    session['searchbeforecontext'] = str(config['searchbeforecontext'])
    session['searchaftercontext'] = str(config['searchaftercontext'])

    return render_template('list.html', validfiles=validfiles)


@app.route("/tail/<filename>/<numlines>/")
def tail(filename, numlines=200):
    """Route: tail the contents of a file given the numlines"""
    return process_file(tailer.tail, filename, int(numlines))


@app.route("/head/<filename>/<numlines>/")
def head(filename, numlines=200):
    """Route: head the contents of a file given the numlines"""
    return process_file(tailer.head, filename, int(numlines))


# TODO: Fix bad GET request
@app.route("/grep/", methods=['GET', 'POST'])
def grep():
    """Search through a file looking for a matching phrase"""

    # Validate the form inputs
    if request is None or request.form is None:
        return render_template('list.html', error='no search expression specified')

    if request.form['expression'] is None or len(request.form['expression']) == 0:
        return render_template('list.html', error='no search expression specified')

    expression = request.form['expression'].strip()
    output = ""
    filepaths = []

    output += search_for_expression(output,
                                    filepaths,
                                    validfiles,
                                    expression,
                                    request.form['grepbefore'],
                                    request.form['grepafter'])

    if not output:
        return render_template('list.html', error='No results found for search expression')

    expression = expression.decode('utf-8')
    highlight = '<span class="highlightmatch">' + expression + '</span>'
    highlightedoutput = output.decode('utf-8').replace(expression, highlight)

    return render_template('results.html', output=highlightedoutput, filepaths=filepaths, expression=expression)


if __name__ == "__main__":
    init()
    app.debug = True
    app.secret_key = 'A0Zr97sfas8j/asdkj R~XHH!jkjaLWX/,?RT'
    app.run(host='0.0.0.0')
