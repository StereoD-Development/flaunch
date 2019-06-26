"""
Management tools for building/deploying things
"""
from __future__ import absolute_import

import os
import sys
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

        self._setup_environment()

        self._prerequisite_check()

        self._pre_build_commands()

        self.build()

        self._post_build_commands()


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

    def _setup_environment(self):
        """
        Update our locale environment with whatever values have been supplied
        with our build section
        """
        env = self.build_file['build']['env'] or {}

        for key, value in utils._iter(env):
            os.environ.update({key: self.build_file.expand(value)})


    def _prerequisite_check(self):
        """
        In the event our action requires select software to be available
        from it's root environment, we call that here.

        Perhaps in the future we could also include "modules" for finding
        basic tools and items.
        """
        prereq = self.build_file['build']['local_required']
        if not prereq:
            prereq = ['git']
        else:
            logging.debug('Searching for prerequisites...')

        if not isinstance(prereq, (list, tuple)):
            logging.warning('build.yaml build -> local_required must be a list')
            return


        command = PlatformDict.simple({
            'windows' : 'where',
            'unix' : 'which'
        })

        def _clean_path(p):
            d = p.decode('utf-8').replace("\r\n", "\n")
            d = d.split("\n")[0].replace("\\", "/")
            return d

        with log.log_indent():
            for requirement in prereq:
                proc = subprocess.Popen(
                    [command, requirement],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                information = proc.communicate()[0]
                if proc.returncode != 0:
                    logging.critical(
                        'Could not find prerequisite: {}'.format(requirement)
                    )
                    sys.exit(1)
                else:
                    if requirement == 'git':
                        continue # quite, this is always needed

                    logging.debug('{} found at: "{}"'.format(
                        requirement,
                        _clean_path(information)
                    ))


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