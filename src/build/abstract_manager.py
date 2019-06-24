"""
Abstract manager class that contains some useful utilities for dealing with build.yaml
files.
"""
from __future__ import absolute_import

import os
import sys
import logging
import traceback

from common.platformdict import PlatformDict
from common.abstract import _AbstractFLaunchData, FLaunchDataError
from .parse import BuildCommandParser
from .buildfile import BuildFile

from common import log
from common import utils
from common import constants


class _AbstractManager(object):

    def __init__(self, app, arguments, build_file, source_dir=None):
        self._app         = app
        # self._is_local    = arguments.local
        self._no_clean    = arguments.no_clean if hasattr(arguments, 'no_clean') else False
        self._additional  = arguments.additional_arguments
        self._build_file  = build_file
        self._source_dir  = source_dir or build_file.path
        self._build_file.set_manager(self)


    @property
    def source_dir(self):
        return self._source_dir.replace('\\', '/')


    @property
    def development_path(self):
        return utils.local_path(self.package, version='dev')


    @property
    def build_dir(self):
        bf_build = self.build_file['build'] # type: PlatformDict
        if bf_build['build_path']:
            build_path = self.build_file.expand(bf_build['build_path'])
        elif os.environ.get(constants.FLAUNCH_BUILD_DIR, None):
            build_path = os.path.join(os.environ[constants.FLAUNCH_BUILD_DIR], self.package)
        else:
            build_path = self.development_path
        return build_path.replace('\\', '/')


    @property
    def install_path(self):
        raise NotImplementedError('FUTURE')


    @property
    def package(self):
        return self._app


    @property
    def build_file(self):
        return self._build_file


    @property
    def additional(self):
        return self._additional


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


    def build_commands(self, condition, build_data, type_):
        """
        General method for getting commands together from our build data and
        executing them via the BuildCommandParser
        :param condition: conditional parameter (if any) - str | None
        :param build_data: The COMMAND_LIST we're potentially executing
        :param type_: Pretty name of th condition
        :return None:
        """
        if build_data:

            ok = condition is None  # False if conditions required
            if condition:
                logging.debug('Checking {} Build Conditions...'.format(type_))

                if not isinstance(condition, (list, tuple)):
                    condition = (condition,)

                # http://book.pythontips.com/en/latest/for_-_else.html
                for c in condition:
                    if c not in self._additional:
                        break;
                else:
                    # We're good to run!
                    ok = True

            if ok:
                logging.debug('Start {} Execution...'.format(type_))
                parser = BuildCommandParser(
                    build_data, self.build_file, self._additional
                )

                try:
                    parser.exec_()
                except Exception as e:
                    logging.critical('Encountered a critical failure!')
                    with log.log_indent():
                        list(map(logging.critical, traceback.format_exc().split('\n')))
                    sys.exit(1)