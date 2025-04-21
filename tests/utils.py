import os
import re
import json
import base64
import shutil
import hashlib
import zipfile
import tempfile
import pycparser
from os import environ
from glob import glob
from subprocess import run
from subprocess import PIPE
from tabulate import tabulate
from distutils.dir_util import copy_tree


# builds program file string
def get_ex(ch, ex):
    return f"./ch{ch}/ex-{ch}.{ex}.c"


# builds program test file string
def get_in(ch, ex):
    if (ch == 1):
        if (ex == 9):
            return "./ch1/spaces.test"
        elif (ex == 13 or ex == 14):
            return "./ch1/words.test"
        elif (ex == 17):
            return "./ch1/long.test"
        elif (ex == 20):
            return "./ch1/tabs.test"
        else:
            return "./ch1/input.test"
    else:
        return "placeholder.test"

# builds expected output file string
def get_out(ch, ex):
    return f"./ch{ch}/expected-{ch}.{ex}"

# reads a file
def read(filename):
    f = open(filename, 'r')
    text = f.read()
    f.close()
    return text.strip()


# writes json
def write_json(data, filename):
    f = open(filename, 'w')
    f.write(json.dumps(data))
    f.close()


# reads a json
def read_json(filename):
    f = open(filename, 'r')
    text = f.read()
    f.close()
    return json.loads(text)


# parse a json string
def parse_json(text):
    return json.loads(text)


# extracts a zip file to a directory:
def extract_to(file, to, delete=False):
    zip_ref = zipfile.ZipFile(file, 'r')
    zip_ref.extractall(to)
    zip_ref.close()
    if delete:
        os.remove(file)


# join paths
def join(*args):
    return os.path.join(*args)


# creates a temp directory
def tempdir(prefix='cc-3-temp', suffix=''):
    return tempfile.mkdtemp(prefix=prefix, suffix=suffix)


# copy files from one dir to another
def copy_files(dirfrom, dirto):
    if os.path.exists(dirfrom):
        for f in glob(os.path.join(dirfrom, '*')):
            if os.path.isdir(f):
                copy_tree(f, os.path.join(dirto, os.path.basename(f)))
            else:
                shutil.copy2(f, dirto)


# copy file to a dir
def copy_file(filename, dirto):
    if os.path.exists(filename):
        shutil.copy2(filename, dirto)


# lists all files in dir
def ls(dir='.', files=[]):
    for e in glob(os.path.join(dir, '*')):
        if os.path.isdir(e):
            ls(dir=e, files=files)
        else:
            files.append(e)
    return files


# fix ownership
def fix_ownership():
    # fix ownership
    statinfo = os.stat(os.getcwd())
    for f in ls():
        if (os.geteuid() == 0):
            os.chown(f, statinfo.st_uid, statinfo.st_gid)
    for f in os.listdir(os.getcwd()):
        if os.path.isdir(f):
            os.chown(f, statinfo.st_uid, statinfo.st_gid)


# removes a directory
def delete_dir(dir):
    shutil.rmtree(dir)


# removes a file
def delete_file(f):
    os.remove(f)


# expected files
def expected_files(files, dir='.'):
    dirfiles = ls(dir=dir)
    not_found = []
    for f in files:
        if f not in dirfiles:
            not_found.append(f)
    return not_found


# executes a shell command
def execute(cmd=[], shell=False, dir='.', input=None, encoding='ascii', timeout=5):
    return run(cmd, shell=shell, stdout=PIPE, stderr=PIPE, input=input, cwd=dir, timeout=timeout)

# makes a target
def make(target=''):
    return execute(cmd=['make', target])


# compile a target
def compile(target=''):
    return execute(cmd=['gcc', '-std=c99', target])

# run a file
def run_program(command):
    return run(command, shell=True, stdout=PIPE, stderr=PIPE, cwd='.', timeout=10)


# passed message
def passed(*args):
    if len(args) > 0:
        return 'passed: ' + args[0]
    return 'passed'


# failed message
def failed(*args):
    if len(args) > 0:
        return 'failed: ' + args[0]
    return 'failed'


# incomplete message
def incomplete(*args):
    if len(args) > 0:
        return 'incomplete: ' + args[0]
    return 'incomplete'


# creates a compilation error msg
def create_error(filename, msg):
    if msg != '':
        return '[%s]\n\n%s\n' % (filename, msg)
    return ''


# creates a pretty result report
def report(table):
    return tabulate(table, headers=['Exercise', 'Grade', 'Message'])


# writes autograder result (lab)
def write_result(grade, msg):
    write_json({'grade': grade, 'output': msg}, 'output.json')


# finds a specific function in the ast
def find_func(ast, name):
    for f in ast.ext:
        if type(f) == pycparser.c_ast.FuncDef and f.decl.name == name:
            return f
    return None


# parses a form
def parse_form(f):
    f = open(f, 'r', encoding='latin1')
    p = re.compile(r'^[0-9]+( )*:[a-zA-Z0-9, ]+$')
    lookup = {}
    for line in f:
        line = line.strip()
        if p.search(line) is not None:
            vals = line.split(':')
            lookup[vals[0].strip()] = vals[1].strip()
    return lookup


# parses a c c99 file
def parse_c(filename):
    make(target=filename + '_conv.c')
    f = open(filename + '_conv.c', 'r')
    text = ''
    p = re.compile(r'(\w)*#.*')
    for line in f:
        line = line.strip('\n')
        if line == '':
            continue
        if p.search(line):
            continue
        text += line + '\n'
    f.close()
    parser = pycparser.c_parser.CParser()
    return parser.parse(text)


# parses a c c99 file
def parse_c_raw(filename):
    f = open(filename + '.c', 'r')
    text = ''
    p = re.compile(r'(\w)*#.*')
    for line in f:
        line = line.strip()
        if line == '':
            continue
        if p.search(line) and 'pragma' not in line.lower():
            continue
        text += line + '\n'
    f.close()
    f = open('temp.c', 'w')
    f.write(text)
    f.close()
    task = execute(cmd=['gcc', '-E', 'temp.c'], timeout=30)
    execute(cmd=['rm', 'temp.c'])
    text = task.stdout.decode().strip()
    parser = pycparser.c_parser.CParser()
    return parser.parse(text)
