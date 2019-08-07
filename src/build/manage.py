"""
Management tools for building software with fbuild
"""
from __future__ import absolute_import

import os
import sys
import shlex
import platform
import subprocess
import logging
import traceback
import json
from copy import deepcopy

from common.platformdict import PlatformDict
from common.abstract import _AbstractFLaunchData, FLaunchDataError
from common import log
from common import utils
from common.utils import yaml
from common import constants

from .parse import BuildCommandParser
from .buildfile import BuildFile
from .abstract_manager import _AbstractManager


class BuildManager(_AbstractManager):
    """
    Base calss for build management. This handles a lot of the cruft for us when
    building with different toolkits (cmake, qmake, basic python, etc.)

    Managers for different build types can be added to to help speed up a particular
    workflow if need be.

    What's more is that the whole app meshes with the flaunch tools for some very
    powerful tools.
    """
    registry = []
    type_ = 'build'

    def __init__(self, app, arguments, build_file, source_dir=None):
        _AbstractManager.__init__(self, app, arguments, build_file, source_dir=source_dir)

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
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir)

        os.chdir(self.build_dir)

        self.setup_environment()

        self.prerequisite_check()

        # -- Check for dependent build
        if self.arguments.build_required:
            self._build_required()

        self._pre_build_commands()

        self.build()

        self._post_build_commands()


    @classmethod
    def get_manager(cls, package, arguments):
        """
        Grab the manager based on the build.yaml file
        """
        from build import managers

        yaml_file = arguments.custom or cls.yaml_file_from_package(package)
        source_dir = None

        if isinstance(yaml_file, list):
            yaml_file, source_dir = yaml_file

        if not os.path.isfile(yaml_file):
            logging.critical('Invalid build yaml: {}'.format(yaml_file))
            sys.exit(1)

        build_data = BuildFile(package, yaml_file)
        build_type = build_data['build']['type'] or 'basic'

        for _cls in BuildManager.registry:
            if hasattr(_cls, 'alias') and _cls.alias == build_type:
                return _cls(package,
                            arguments,
                            build_data,
                            source_dir=source_dir)

        logging.critical('Cannot find build a build manager')

    # -- "Protected" methodM

    def create_launch_json(self, build_path):
        """
        Create a launch.json file within our build directory.
        Uses the 'launch_json' key if available 
        """
        bf_build = self.build_file['build']

        ljson_path = os.path.join(build_path, 'launch.json')
        if bf_build['launch_json']:
            if not isinstance(bf_build['launch_json'], PlatformDict):
                logging.critical('launch_json must be a JSON compliant dictionary!')
                with log.log_indent():
                    s = traceback.format_stack()
                    map(logging.critical, s)
                sys.exit(1)

            with open(ljson_path, 'w') as f:
                json.dump(bf_build['launch_json'].to_dict(), f, sort_keys=True, indent=4)

        else:
            real_path = os.path.join(self.build_file.path, 'launch.json')
            if os.path.isfile(real_path):
                import shutil
                shutil.copy2(real_path, ljson_path)

        if not os.path.exists(ljson_path):
            # Not hyper critical
            logging.warning('launch.json file not found! Expect issues when launching!')


    # -- Virtual Interface

    def build(self):
        """
        Execute the build.
        """
        pass # Overload per build manager

    # -- Private Methods

    def _build_required(self):
        """
        Given the build file, check if we have any packages that we require
        and, if so, build them with any arguments placed in the build.yaml
        :return: None
        """
        #
        # Might as well treat it like a native command and avoid any kind
        # of subprocess junk.
        #
        from build.start import build_parser

        logging.debug(':Requirements Build:')
        with log.log_indent():
            requirements = self.build_file['requires']
            if not requirements:
                logging.info(self.package + ' has no known requirements')

            if not isinstance(requirements, (list, tuple)):
                requirements = [requirements]

            parser = build_parser()
            for requirement in requirements:

                req_expanded = self.build_file.expand(requirement)

                logging.info('Required: {}'.format(req_expanded))
                arg_string = 'build {}{}'.format(
                    '-v ' if log.is_verbose() else '',
                    req_expanded
                )
                args, addon = parser.parse_known_args(shlex.split(arg_string))
                args.additional_arguments = addon
                args.func(args)
                os.chdir(self.build_dir) # Reset the current dir every time


    def _pre_build_commands(self):
        """
        Using the build file, identify if we have any commands to process
        with our environment and then do it!
        :return: None
        """

        logging.debug(':Pre Build:')
        with log.log_indent():

            build_descrpitor = self.build_file['build']

            condition = build_descrpitor['pre_build_conditions']
            pre_build = build_descrpitor['pre_build']
            self.build_commands(condition, pre_build, 'Pre')


    def _post_build_commands(self):
        """
        Using the build file, identify if we have any commands to process
        with our environment and then do it!
        :return: None
        """
        build_descrpitor = self.build_file['build']

        logging.debug(':Post Build:')
        with log.log_indent():

            build_descrpitor = self.build_file['build']

            condition = build_descrpitor['post_build_conditions']
            post_build = build_descrpitor['post_build']
            self.build_commands(condition, post_build, 'Post')