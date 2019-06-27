"""
DeployMangaer for deploying software with fbuild
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


class DeployManager(_AbstractManager):
    """
    Deployment!
    """
    type_ = 'deploy'


    def __init__(self, app, arguments, build_file, source_dir=None):
        _AbstractManager.__init__(self, app, arguments, build_file, source_dir=source_dir)
        build_file.add_attribute('version', self.version)


    def run_deploy(self):
        """
        Execute the deployment.
        """
        self.setup_environment()
        self.prerequisite_check()
        self._pre_deploy_commands()
        self.deploy()
        self._post_deploy_commands()


    @property
    def version(self):
        if self.arguments.beta:
            return 'b' + self.arguments.version
        return self.arguments.version


    def deploy(self):
        """
        The actually deployment starts here!
        
        1. Identify what type of deployment we're working with
        """
        # if self.arguments.release:

        pass


    # -- Private Methods

    def _pre_deploy_commands(self):
        """
        Using the build file, identify if we have any commands to process
        with our environment and then do it!
        :return: None
        """

        logging.debug(':Pre Deploy:')
        with log.log_indent():

            build_descrpitor = self.build_file[self.type_]

            condition = build_descrpitor['pre_deploy_conditions']
            pre_build = build_descrpitor['pre_deploy']
            self.build_commands(condition, pre_build, 'Pre')


    def _post_deploy_commands(self):
        """
        Using the build file, identify if we have any commands to process
        with our environment and then do it!
        :return: None
        """
        build_descrpitor = self.build_file[self.type_]

        logging.debug(':Post Deploy:')
        with log.log_indent():

            build_descrpitor = self.build_file[self.type_]

            condition = build_descrpitor['post_deploy_conditions']
            post_build = build_descrpitor['post_deploy']
            self.build_commands(condition, post_build, 'Post')