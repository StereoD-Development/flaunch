"""
Management tools for building/deploying things
"""
import os
import sys
import platform
import logging

import yaml

from common.platformdict import PlatformDict
from common.abstract import _AbstractFLaunchData, FLaunchDataError
from common import utils
from common import constants

class BuildFile(_AbstractFLaunchData):
    """
    A build file describes the processes required for constructing and
    deploying packages with flaunchdev
    """
    def __init__(self, package, path):
        try:
            with open(path) as f:
                d = yaml.safe_load(f)
                data = PlatformDict(d)
        except Exception as e:
            logging.error(path + ' - invalid yaml file')
            raise FLaunchDataError(str(e))

        _AbstractFLaunchData.__init__(self, package, path, data)


    def attributes(self):
        """
        For variable expansion, we handle it at the build file level
        """
        return self['props'] or {}


class BuildCommandParser(object):
    """
    Utility for parsing and understanding a command. This will handle
    the various types of commands as well as the 
    """
    pass


class BuildManager(object):
    """
    Base calss for build management. This handles a lot of the cruft for us when
    building with different toolkits (cmake, qmake, basic python, etc.)

    Managers for different build types can be added to to help speed up a particular
    workflow if need be.

    What's more is that the whole app meshes with the flaunch tools for some very
    powerful tools.
    """
    registry = []

    def __init__(self, app, arguments, build_file, source_dir=None):
        self._app         = app
        self._is_local    = arguments.local
        self._no_clean    = arguments.no_clean
        self._additional  = arguments.additional_arguments
        self._build_file  = build_file
        self._source_dir  = source_dir or build_file.path

    # -- Registration

    @staticmethod
    def register(builder_class):
        """
        Register a build manager
        """
        BuildManager.registry.append(builder_class)

    # -- Public Interface

    def run_build(self):
        """
        Run the full extent of the build. This includes any pre and post
        commands.
        """
        self._pre_build_commands()
        self.build()
        self._post_build_commands()

    @property
    def source_dir(self):
        return self._source_dir


    @property
    def development_path(self):
        return utils.local_path(self.package, version='dev')


    @property
    def package(self):
        return self._app


    @property
    def build_file(self):
        return self._build_file


    @classmethod
    def get_manager(cls, package, arguments):
        """
        Grab the manager based on the build.yaml file
        """
        from build import managers

        yaml_file = arguments.custom or cls._yaml_file_from_package(package)
        source_dir = None

        if isinstance(yaml_file, list):
            yaml_file, source_dir = yaml_file

        if not os.path.isfile(yaml_file):
            logging.critical('Invalid build yaml: {}'.format(yaml_file))
            sys.exit(1)

        build_data = BuildFile(package, yaml_file)
        build_type = build_data['build']['type']

        for _cls in BuildManager.registry:
            if hasattr(_cls, 'alias') and _cls.alias == build_type:
                return _cls(package, arguments, build_data, source_dir)

        logging.critical('Cannot find build a build manager')


    @classmethod
    def _yaml_file_from_package(cls, package):
        """
        Based on the environment, grab the package that is most likely
        to be used for the 
        :param package: The name of the package were going to use
        :return: str
        """
        return os.path.join(
            os.environ.get(constants.FLAUNCH_DEV_DIR, os.getcwd()),
            package,
            'build.yaml'
        )

    # -- Virtual Interface

    def build(self):
        """
        Execute the build.
        """
        pass # Overload per manager

    # -- Private Methods

    def _pre_build_commands(self):
        """
        Using the build file, identify if we have any commands to process
        with our environment and then do it!
        :return: None
        """
        build_descrpitor = self.build_file['build']

        # if build_descrpitor['pre_build_conditions']:


    def _post_build_commands(self):
        """
        Using the build file, identify if we have any commands to process
        with our environment and then do it!
        :return: None
        """
        build_descrpitor = self.build_file['build']

        # if build_descrpitor['post_build_conditions']:
            
