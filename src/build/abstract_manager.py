"""
Abstract manager class that contains some useful utilities for dealing with build.yaml
files.
"""
from __future__ import absolute_import

import os
import sys
import logging
import traceback
import subprocess

from common.platformdict import PlatformDict
from common.abstract import _AbstractFLaunchData, FLaunchDataError
from .parse import BuildCommandParser
from .buildfile import BuildFile

from common import log
from common import utils
from common import constants


class _AbstractManager(object):

    type_ = ''

    def __init__(self, app, arguments, build_file, source_dir=None):
        self._app         = app
        self._arguments   = arguments
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
    def package(self):
        return self._build_file.package


    @property
    def build_file(self):
        return self._build_file


    @property
    def additional(self):
        return self._additional


    @property
    def arguments(self):
        return self._arguments
    

    @classmethod
    def get_manager(cls, package, arguments=None, raise_=False):
        """
        Grab the manager based on the build.yaml file
        """
        if not arguments:
            import argparse
            arguments = argparse.Namespace()
            arguments.custom = None
            arguments.additional_arguments = []

        yaml_file = arguments.custom or cls.yaml_file_from_package(package)
        source_dir = None

        if isinstance(yaml_file, list):
            yaml_file, source_dir = yaml_file

        if not os.path.isfile(yaml_file):
            logging.critical('Invalid build yaml: {}'.format(yaml_file))
            if not raise_:
                sys.exit(1)
            else:
                raise IOError('Cannot find build yaml: {}'.format(yaml_file))

        build_data = BuildFile(package, yaml_file)
        return cls(package, arguments, build_data, source_dir=source_dir)


    @classmethod
    def yaml_file_from_package(cls, package):
        """
        Based on the environment, grab the package that is most likely
        to be used for the 
        :param package: The name of the package were going to use
        :return: str
        """
        return os.path.join(
            os.environ.get(constants.FLAUNCH_DEV_DIR, os.path.dirname(os.getcwd())),
            package,
            'build.yaml'
        )


    def prerequisite_check(self):
        """
        In the event our action requires select software to be available
        from it's root environment, we call that here.

        Perhaps in the future we could also include "modules" for finding
        basic tools and items.
        """
        prereq = self.build_file[self.type_]['local_required']
        if not prereq:
            prereq = ['git']
        else:
            logging.debug('Searching for prerequisites...')

        if not isinstance(prereq, (list, tuple)):
            logging.warning('build.yaml {} -> local_required must be a list'.format(self.type_))
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

                if requirement.startswith('py::'):
                    # Required python module
                    module = requirement.replace('py::', '', 1)
                    try:
                        __import__(module)
                    except ImportError as err:
                        logging.critical('The python module: "{}" is required!'.format(module))
                        sys.exit(1)

                    logging.debug('Module "{}" found'.format(
                        module,
                    ))
                    continue


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
                        continue # quiet, this is always needed

                    logging.debug('{} found at: "{}"'.format(
                        requirement,
                        _clean_path(information)
                    ))


    def setup_environment(self):
        """
        Update our locale environment with whatever values have been supplied
        with our build section
        """
        env = self.build_file[self.type_]['env'] or {}

        for key, value in utils._iter(env):
            os.environ.update({key: self.build_file.expand(value)})


    def build_commands(self, condition, build_data, type_ = None):
        """
        General method for getting commands together from our build data and
        executing them via the BuildCommandParser
        :param condition: conditional parameter (if any) - str | None
        :param build_data: The COMMAND_LIST we're potentially executing
        :param type_: Pretty name of the condition (if any)
        :return None:
        """

        if type_:
            type_ = type_ + ' '
        else:
            type_ = ''

        if build_data:

            ok = condition is None  # False if conditions required
            if condition:
                logging.debug('Checking {}{} Conditions...'.format(
                    type_, self.type_.capitalize()
                ))

                if not isinstance(condition, (list, tuple)):
                    condition = (condition,)

                # http://book.pythontips.com/en/latest/for_-_else.html
                for c in condition:
                    if c not in self._additional:
                        break
                else:
                    # We're good to run!
                    ok = True

            if ok:
                logging.debug('Start {}Execution...'.format(type_))
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
        else:
            logging.debug('No {}Commands'.format(type_))
