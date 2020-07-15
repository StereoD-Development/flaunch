"""
Build management utilities
"""
from __future__ import absolute_import

import re
import os
import sys
import json
import shlex
import shutil
import logging
import tempfile
import platform
import subprocess

from contextlib import contextmanager

from . import log

PY3 = sys.version_info[0] == 3
SYSTEM = platform.system()

if PY3:
    def _iter(it):
        return it.items()
    string_types = str
else:
    def _iter(it):
        return it.iteritems()
    string_types = (str, basestring)


def path_ancestor(path, count):
    if count <= 0:
        return path
    return path_ancestor(os.path.dirname(path), count - 1)


def run_(command_and_args, custom_env = {}, verbose = False, build_file = None):
    """
    Execute the command provided
    :param command_and_args: list|str of the command and arguments we want to run
    :param custom_env: Environment values we want to utilize over our current environ
    :param verbose: Not used currently
    :param build_file: For building, this is a BuildFile instance that has additional
                       environment augmentation
    :return: int exit code
    """
    env = dict(os.environ, **custom_env)
    if build_file is not None:
        build_file.command_environment(env)
    os.environ.update(env)

    if not isinstance(command_and_args, (list, tuple)):
        full_command = shlex.split(command_and_args)
    else:
        full_command = list(command_and_args)

    for i, c in enumerate(full_command):
        if re.match("^\"[^\"]\"^", c):
            # Strip away surrounding the quotes
            full_command[i] = c[1:-1]

    # Last second evaluation
    full_command = [os.path.expandvars(f) for f in full_command]
    logging.info("Running command: " + " ".join(full_command))

    if PY3:
        return subprocess.run(full_command).returncode
    else:
        return subprocess.check_call(" ".join(full_command), shell=True)


def local_path(package, version=None, base_only=False):
    """
    Based on the package and the local version, build a
    path that we know will hold onto this version of the
    software suite
    :param pacakge: The package that we're localizing (str)
    :param version: The version of the pacakge (str)
    :param base_only: Should we only return the root of all apps
    :return: str
    """
    if platform.system() == 'Windows':
        base = os.path.join(os.environ['APPDATA'], 'flux_launch', 'apps')
    elif platform.system() == 'Linux':
        base = os.path.join(
            os.path.expanduser('~'),
            '.local',
            'share',
            'flux_launch',
            'apps'
        )

    if not os.path.isdir(base):
        os.makedirs(base)

    if base_only:
        return base

    if version is None:
        return os.path.join(base, package).replace('\\', '/')

    return os.path.join(base, package, version).replace('\\', '/')


def add_metaclass(metaclass):
    """
    Taken from the six module. Python 2 and 3 compatible.
    """
    def wrapper(cls):
        """
        The actual wrapper. take the given class and return one that contains the proper metaclass.
        """
        orig_vars = cls.__dict__.copy()
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper


def merge_dicts(dict1, dict2, combine_keys=None, ignore=None):
    '''
    Merge dictionaries recursively and pass back the result.
    If a conflict of types arrive, just get out with what
    we can.
    '''
    if combine_keys is None:
        combine_keys = {}
    if ignore is None:
        ignore = []
    def _merge_list_of_dicts(list1, list2, key):

        list1_values = [l[key] for l in list1]
        list2_values = [l[key] for l in list2]

        for v in set(list1_values).union(list2_values):
            if v in list2_values:
                # If the value is in the second list, we use that instead
                yield list2[list2_values.index(v)]
            else:
                yield list1[list1_values.index(v)]


    for k in set(dict1.keys()).union(dict2.keys()):
        if k in dict1 and k in dict2:
            if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                if k in ignore:
                    yield (k, dict2[k])
                else:
                    yield (k, dict(merge_dicts(dict1[k], dict2[k], combine_keys, ignore)))
            else:
                # If one of the values is not a dict, you can't continue merging it.
                # Value from second dict overrides one in first and we move on.

                # That is, unless, we've supplied combine keys. This is for list
                # concatinaion based on a given key.
                if k in combine_keys:
                    if isinstance(dict1[k], list) and isinstance(dict2[k], list):
                        yield (k, list(_merge_list_of_dicts(dict1[k], dict2[k], combine_keys[k])))
                    else:
                        yield (k, dict2[k])
                else:
                    yield (k, dict2[k])
        elif k in dict1:
            yield (k, dict1[k])
        else:
            yield (k, dict2[k])


def levenshtein(s1, s2):
    """
    Pythonic levenshtein math to quickly determine how many "edits" two strings are
    differently than one another.

    Code snippet by Halfdan Ingvarsson

    :param s1: String to compare
    :param s2: String to compare
    :return: int - number of edits required (higher number means more different)
    """

    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer
            # than s2
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def cli_name(arg, ignore_prefix = False):
    """
    Convert an argument name into the cli equivalent
    
    Basically this just adds '--' to the front and converts '_' to '-'

    :param arg: str to convert
    :return: str
    """
    prefix = '--' if (not arg.startswith('--') and not ignore_prefix) else ''
    return prefix + arg.replace('_', '-')


@contextmanager
def cd(new_directory, cleanup=lambda: True):
    """
    Quick context for working in our temp directory
    """
    previous = os.getcwd()
    os.chdir(os.path.expanduser(new_directory))
    try:
        yield
    finally:
        os.chdir(previous)
        cleanup()


@contextmanager
def temp_dir(change_dir=True):
    """
    Quick temp directory that we move into to do our work
    :return: The new temp directory (we've also cd'd into it) 
    """
    dirpath = tempfile.mkdtemp()
    def _clean():
        shutil.rmtree(dirpath)
    if change_dir:
        with cd(dirpath, _clean):
            yield dirpath
    else:
        yield dirpath


def load_from_source(filepath, name=None):
    """
    Obligatory Python 2/3 source file loading mechanism
    :param filepath: path to a loadable source file
    :param name: name to give this module (will pick one if None)
    :return: Python Module
    """
    if name is None:
        name = os.path.basename(filepath).replace('.py', '')

        # In the event we have a repeat module name
        count = 0
        while name in sys.modules:
            name += str(count)
            count += 1

    if PY3:
        if sys.version_info[2] >= 5:
            import importlib.util
            spec = importlib.util.spec_from_file_location(name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        else:
            from importlib.machinery import SourceFileLoader
            return SourceFileLoader(name, filepath).load_module()
    else:
        import imp
        return imp.load_source(name, filepath)


default_build_yaml = """\
#
# The {package} build.yaml
#

# The name of the package
name: {package}

# The build procedure
build:

  type: basic
"""

def initialize_pacakge(args):
    """
    Initialize the current directory with a build.yaml
    """
    if os.path.exists('build.yaml'):
        logging.error('build.yaml already exists! Cannot initialize.')
        sys.exit(1)

    package_name = os.path.basename(os.getcwd())

    with open('build.yaml', 'w') as f:
        f.write(default_build_yaml.format(
            package = package_name
        ))

    logging.info('Initialized - created build.yaml! Welcome to fbuild.')


class SimpleRegistry(type):
    """
    A metaclass that builds a registry automatically
    """
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, '_registry'):
            cls._registry = {} # Base Class
        else:
            cls._registry[cls.alias] = cls
