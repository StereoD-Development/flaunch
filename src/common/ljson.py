"""
launch.json helper tools
"""

from __future__ import absolute_import

import os
import json
import logging

from . import log
from .platformdict import PlatformDict
from .abstract import _AbstractFLaunchData, FLaunchDataError

from .utils import merge_dicts

class LaunchJson(_AbstractFLaunchData):
    """
    Basic tool for handling launch.json files
    """
    def __init__(self, package, path, development=False):
        try:
            with open(path, 'r') as f:
                data = PlatformDict(json.load(f))
        except Exception as e:
            logging.error(path + ' - invalid json file')
            raise FLaunchDataError(str(e))

        _AbstractFLaunchData.__init__(self, package, path, data)

        self._development = development
        if self._development:
            # -- Attempt to locate the developement build.yaml for additional
            #    environment information
            try:
                from build.manage import BuildManager
                manager = BuildManager.get_manager(self.package, raise_=True)
            except:
                return # Cannot find the manager around here, ignore it for now

            if manager.build_file['dev']:
                dev_info = manager.build_file['dev']

                ig = dev_info['ignore'] or []
                ignore_packages = [manager.build_file.expand(i) for i in ig]

                for pkg in ignore_packages:
                    self['requires'].remove(pkg)

                for k,v in (dev_info['env'] or {}).items():
                    env_key = manager.build_file.expand(k)
                    env_value = manager.build_file.expand(v)
                    self['env'][env_key] = env_value


    def requires(self):
        """
        :return: list[str] of required packages
        """
        return self['requires'] or []


    def standalone_requires(self):
        """
        :return: ``list[str]`` - required pacakges when launching
        """
        return self['standalone_requires'] or self.requires()


    def prep_env(self):
        """
        :return: ``dict``
        """
        return self['prep_env'] or {}


    def extends(self):
        """
        :return: str of package this one extends
        """
        return self['extends'] or None


    def default_args(self):
        """
        :return: list of default arguments
        """
        return self['default_args'] or None


    def swap(self):
        """
        :return: ``list[tuple]``
        """
        return self['swap'] or []


    def set_base(self, base_ljson):
        """
        :param base_ljson: The LaunchJson that this instance overrides
        :return: None
        """
        self._path = base_ljson._path
        self._data = PlatformDict(
            dict(merge_dicts(base_ljson._data.to_dict(), self._data.to_dict()))
        )
