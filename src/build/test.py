"""
Test execution manager for flaunch packages
"""
from __future__ import absolute_import

import os
import sys
import logging

from common import log

from .abstract_manager import _AbstractManager

class TestManager(_AbstractManager):
    """
    Manager for controlling test running for a particular application
    """
    type_ = 'test'

    def __init__(self, app, arguments, build_file, source_dir=None):
        _AbstractManager.__init__(self, app, arguments, build_file, source_dir=source_dir)

        build_file.add_attribute('_in_test', True)
        self._stage = 'none'


    def run_tests(self):
        """
        Execute the test suite
        """
        os.chdir(self.source_dir)

        self.setup_environment()

        self.prerequisite_check()

        self._pre_test_commands()

        self.exec_()

        self._post_test_commands()


    @property
    def stage(self):
        return self._stage


    def exec_(self):
        """
        Execute the test commands

        :return: bool
        """
        self._state = 'test'

        logging.debug(':Test:')
        with log.log_indent():

            test_descriptor = self.build_file[self.type_]
            test_commands = test_descriptor['commands']
            self.build_commands(None, test_commands)

        return True


    def _pre_test_commands(self):
        """
        Check if we want to run any commands before we start our testing
        """
        self._stage = 'pre_test'

        logging.debug(':Pre Test:')
        with log.log_indent():

            test_descriptor = self.build_file[self.type_]
            condition = test_descriptor['pre_test_condition']
            pre_test = test_descriptor['pre_test']
            self.build_commands(condition, pre_test)


    def _post_test_commands(self):
        """
        Check if we want to run any commands after we've done our testing
        """
        self._stage = 'post_test'

        logging.debug(':Post Test:')
        with log.log_indent():

            test_descriptor = self.build_file[self.type_]
            condition = test_descriptor['post_test_condition']
            post_test = test_descriptor['post_test']
            self.build_commands(condition, post_test)
