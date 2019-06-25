"""
Raw command tools!
"""
from __future__ import absolute_import

import os
import sys
import logging

from common.utils import yaml
from common import utils
from .abstract_manager import _AbstractManager
from .parse import BuildCommandParser
from .buildfile import BuildFile

class RawCommandManager(_AbstractManager):
    """
    Utility class for executing arbitrary commands help within a build.yaml file
    """
    def __init__(self, app, arguments, build_file, source_dir=None):
        _AbstractManager.__init__(self, app, arguments, build_file, source_dir=source_dir)

        # Verify that we have a valid command in our build.yaml
        self._command = arguments.command_name or None
        if self._command:

            if self._command not in self.raw_commands():
                logging.critical('Command not found: "{}" in file: {}'.format(
                    self._command, self.build_file.flaunch_data_path
                ))
                sys.exit(1)

            if not self.raw_commands()[self._command]['commands']:
                logging.critical('Command: "{}" exists but has no "commands:" COMMAND_LIST')
                sys.exit(1)


    def raw_commands(self):
        return self.build_file['raw']


    def all_commmands(self):
        """
        :return: dict[str:(str,iterable)] of command name to any help docs
        """
        comms = {}
        rawcomm = self.raw_commands()
        for command in rawcomm:
            c = rawcomm[command]
            comms[command] = ((c['help'] or ''), c['arguments'] or ('None',))
        return comms


    @classmethod
    def get_manager(cls, package, arguments):
        """
        While not as intense as the BuildManager.get_manager function, this
        just does some of the initial validation and checkout for 
        """
        yaml_file = arguments.custom or cls._yaml_file_from_package(package)
        source_dir = None

        if isinstance(yaml_file, list):
            yaml_file, source_dir = yaml_file

        if not os.path.isfile(yaml_file):
            logging.critical('Invalid build yaml: {}'.format(yaml_file))
            sys.exit(1)

        build_data = BuildFile(package, yaml_file)
        return cls(package, arguments, build_data, source_dir=source_dir)


    def run_raw_commands(self):
        """
        Get the commands and fire away!
        """
        this_command = self.raw_commands()[self._command]
        required = this_command['arguments']
        if required:

            missing = []
            for r in required:
                if isinstance(r, (list, tuple)):
                    r = r[0]
                if utils.cli_name(r) not in self.additional:
                    missing.append(r)

            if missing:
                logging.critical("Missing required variable{}: {}".format(
                    's' if len(missing) > 1 else '',
                    ', '.join(missing)
                ))
                sys.exit(1) # ??

        entering_parameters = {}
        for req in required:
            req_name = req[0]
            idx = self.additional.index(utils.cli_name(req_name))

            if idx + 2 > len(self.additional):
                logging.critical('Missing value for {}!'.format(req_name))
                sys.exit(1)

            entering_parameters[req_name] = self.additional[idx + 1]

        with self.build_file.overload(entering_parameters):
            self.build_commands(
                condition=None, build_data=this_command['commands'], type_='Raw'
            )
