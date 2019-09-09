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
from common import constants
from common import communicate

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
        self._stage = 'none'


    def run_deploy(self):
        """
        Execute the deployment.
        """
        self.setup_environment()
        self.prerequisite_check()
        self._pre_deploy_commands()
        if self.deploy():
            self._post_deploy_commands()


    def run_registration(self):
        """
        Execute a registratino process
        """
        self.setup_environment()
        if not self.arguments.skip_validation:
            self._verify_existence()
        else:
            logging.warning('Releasing package without file validation')

        result = communicate.register_package(
            self.package,
            self.version,
            method='post',
            launch_data=None,
            force=self.arguments.force,
            pre_release=self.arguments.beta
        )
        return result


    @property
    def stage(self):
        return self._stage


    @property
    def version(self):
        return self.arguments.version


    def deploy(self):
        """
        The deployment process starts here!
        :return: bool
        """
        if not (self.arguments.transfer):
            # This was only a predeploy, nothing to do
            logging.info("Predeploy Only")
            return False

        self._stage = 'deploy'
        logging.debug(':Deploy:')
        with log.log_indent():

            deploy_descrpitor = self.build_file[self.type_]
            deploy_commands = deploy_descrpitor['commands']
            self.build_commands(None, deploy_commands)

        return True


    # -- Private Methods

    def _verify_existence(self):
        """
        Verify that the version we're looking for exists globally. This
        requires a machine that can reach all points - which is a bit of
        a tough ask when considering the nature of the active disk
        architecture...
        :return: None
        """
        # TODO!
        return


    def _pre_deploy_commands(self):
        """
        Using the build file, identify if we have any commands to process
        with our environment and then do it!
        :return: None
        """
        self._stage = 'pre_deploy'

        logging.debug(':Pre Deploy:')
        with log.log_indent():

            deploy_descrpitor = self.build_file[self.type_]

            condition = deploy_descrpitor['pre_deploy_conditions']
            pre_deploy = deploy_descrpitor['pre_deploy']
            self.build_commands(condition, pre_deploy, 'Pre')


    def _post_deploy_commands(self):
        """
        Using the build file, identify if we have any commands to process
        with our environment and then do it!
        :return: None
        """
        self._stage = 'post_deploy'
        deploy_descrpitor = self.build_file[self.type_]

        logging.debug(':Post Deploy:')
        with log.log_indent():

            deploy_descrpitor = self.build_file[self.type_]

            condition = deploy_descrpitor['post_deploy_conditions']
            post_deploy = deploy_descrpitor['post_deploy']
            self.build_commands(condition, post_deploy, 'Post')