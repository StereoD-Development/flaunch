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
    def __init__(self, package, path, manager=None):
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
        self._load()

        self._build_manager = manager

    def set_manager(self, manager):
        """
        Link ourselves back to a build manager
        :param manager: The BuildManager that owns this item
        """
        self._build_manager = manager

    @property
    def additional(self):
        if self._build_manager:
            return self._build_manager.additional
        return []


    @property
    def build_dir(self):
        if self._build_manager:
            return self._build_manager.build_dir
        return ''


    @property
    def install_path(self):
        if self._build_manager:
            return self._build_manager.install_path
        return ''


    @property
    def source_dir(self):
        if self._build_manager:
            return self._build_manager.source_dir
        return ''


    def add_attribute(self, key, value):
        """
        Add an attribute to our properties
        """
        if self['props'] is None:
            self._data.update({'props' : {}})
        self._data['props'].update({key : value})


    def attributes(self):
        """
        For variable expansion, we handle it at the build file level
        """
        return deepcopy(self['props']) or PlatformDict()


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
        :return: tuple(list[<COMMAND>,], list[str])
        """
        commands = []
        arguments = []

        if '(' in name:
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

        return commands, arguments


    def _load(self):
        """
        The BuildFile manages some additional features. See docs/plugins.md for
        for information
        """

        #
        # Start with any plugins. Our local build file will overload anything in
        # said plugin but it's good to have
        #
        if self['include']:
            if not isinstance(self['include'], (list, tuple)):
                raise TypeError('build.yaml -> include: must be a list of plugins')

            for plugin in self['include']:
                plugin_filepath = utils.path_ancestor(os.path.abspath(__file__), 3)
                plugin_filepath = os.path.join(plugin_filepath, 'plugins', plugin + '.yaml')

                if not os.path.isfile(plugin_filepath):
                    logging.error("Invalid plugin: {}".format(plugin_filepath))
                    return

                with open(plugin_filepath) as f:
                    plugin_data = yaml.safe_load(f)
                    self._data = PlatformDict(
                        dict(utils.merge_dicts(plugin_data, self._data.to_dict()))
                    )
