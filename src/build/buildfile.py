"""
build.yaml file toolkit
"""
from __future__ import absolute_import

import os
import sys
import logging
from copy import deepcopy

from common.utils import yaml
from common.platformdict import PlatformDict
from common.abstract import _AbstractFLaunchData, FLaunchDataError
from common import utils

class BuildFile(_AbstractFLaunchData):
    """
    A build file describes the processes required for constructing and
    deploying packages with flaunchdev
    """
    def __init__(self, package, path, manager=None, name=None):
        try:
            with open(path) as f:
                d = yaml.safe_load(f.read())

                if not d.get('props'):
                    d['props'] = {} # Make sure for plugin setup

                data = PlatformDict(d)
        except Exception as e:
            logging.error(path + ' - invalid yaml file')
            raise FLaunchDataError(str(e))

        _AbstractFLaunchData.__init__(self, package, path, data)

        self._name = name
        self._templates = {}
        self._manager = manager
        self._load()

    def get_manager(self):
        """
        Get the manager (if any)
        :return: _AbstractManager subclass
        """
        return self._manager

    def set_manager(self, manager):
        """
        Link ourselves back to a build manager
        :param manager: The BuildManager that owns this item
        """
        self._manager = manager


    @property
    def additional(self):
        if self._manager:
            return self._manager.additional
        return []


    @property
    def build_dir(self):
        if self._manager:
            return self._manager.build_dir
        return ''


    @property
    def source_dir(self):
        if self._manager:
            return self._manager.source_dir
        return ''


    @property
    def included_templates(self):
        return self._templates


    def add_attribute(self, key, value, global_=False):
        """
        Add an attribute to our properties
        """
        if self['props'] is None:
            self._data.update({'props' : {}})
        self._data['props'].update({key : value})
        if global_:
            self.add_global_attr(key, value)


    def attributes(self):
        """
        For variable expansion, we handle it at the build file level
        """
        return deepcopy(self['props']) or PlatformDict()


    def expand_prop(self, prop):
        """
        Expand a property value (if it exists)
        :param prop: str property value
        :return: str|None
        """
        v = (self['props'] or PlatformDict())[prop]
        if v:
            return self.expand(v)
        return None


    def command_environment(self, env):
        """
        The environment that we run when working with a command
        based tool
        :return: dict{str:str}
        """
        if self['env']:
            for k,v in utils._iter(self['env']):
                # Passing key will update the environment
                self.expand(v, env, key=k)


    def get_function_commands(self, name):
        """
        Get a function based on it's name as well as any arguments it
        requires
        :param namne: The name of the function to look up (this should
        exclude the func__)
        :return: tuple(list[<COMMAND>,], dict[str:str], list[str])
        """
        commands = []  # The COMMAND_LIST we're about to run
        supplied = {}  # Arguments that we've supplied with the function
        arguments = [] # Global variables to look for

        supplied_args = []
        if '(' in name:
            found_supplied = name[name.index('(')+1:name.index(')')]
            if found_supplied:
                found_supplied = found_supplied.split(',')
                supplied_args = list(map(lambda x: x.strip(), found_supplied))

            name = name[:name.index('(')]

        for key, value in utils._iter(self._data):
            if key.startswith('func__'):
                func_name = key[:key.index('(')].replace('func__', '')
                if func_name == name:
                    commands = self[key]

                    # We've found the function, now check for arguments
                    # we need to supply
                    func_args_string = key[key.index('(')+1:key.index(')')]
                    if func_args_string:
                        func_args = func_args_string.split(',')
                        arguments = [a.strip() for a in func_args]

                    if len(supplied_args) > len(arguments):
                        raise RuntimeError('Invalid number of arguments for {}.'
                                           ' Expected <= {}, got {}'.format(
                            name, len(arguments), len(supplied_args)
                        ))

                    for supplied_arg in supplied_args:
                        supplied[arguments.pop(0)] = self.expand(supplied_arg)

        return commands, supplied, arguments


    def get_function_names(self):
        """
        :return: list[str] of all known functions for this BuildFile
        """
        functions = []
        for key, value in utils._iter(self._data):
            if key.startswith('func__'):
                functions.append(key[:key.index('(')].replace('func__', ''))
        return functions


    def _load(self):
        """
        The BuildFile manages some additional features. See docs/plugins.md for
        for information
        """

        #
        # Start with any plugins. Our local build file will overload anything in
        # said plugin but at least we don't have to duplicate functions
        #
        include = self['include']
        if not include:
            include = []

        if not isinstance(include, (list, tuple)):
            raise TypeError('build.yaml -> include: must be a list of plugins')

        if self._name != 'global':
            include.insert(0, 'global')

        for plugin in include:
            plugin_filepath = utils.path_ancestor(os.path.abspath(__file__), 3)
            plugin_filepath = os.path.join(plugin_filepath, 'templates', plugin + '.yaml')

            if not os.path.isfile(plugin_filepath):
                logging.error("Invalid plugin: {}".format(plugin_filepath))
                return

            # FIXME: Need to check for cyclic dependencies
            plugin_bf = BuildFile(self.package, plugin_filepath, manager=self._manager, name=plugin)
            self._templates[plugin] = plugin_bf

            self._data = PlatformDict(
                dict(utils.merge_dicts(plugin_bf._data.to_dict(), self._data.to_dict()))
            )
