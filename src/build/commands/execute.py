"""
Custom python scripts that are processed via command!

NOTE: DON'T sys.exit(1) out of here. We're trying to catch these
errors for better reporting.
"""
from __future__ import print_function, absolute_import

import os
import sys
import shutil
import logging
import argparse

# import imp

from types import ModuleType
from build.command import _BuildCommand

def _execute_into_module(command, name, locals):
    compiled = compile(command, '', 'exec')
    module = ModuleType(name)
    exec(compiled, module.__dict__)


class PythonCommand(_BuildCommand):
    alias = 'PYTHON'

    def description(self):
        return 'Run Python code within a limited context'


    def populate_parser(self, parser):
        """
        A few arguments to augment how the interpreter will work
        """
        parser.add_argument(
            '-f', '--file',
            action='store_true',
            help='The script provided is from a file'
        )
        parser.add_argument(
            'code',
            help='The script to execute. This can be a file (-f arg) or a property'
        )

    def run(self, build_file):
        """
        Time to run!
        """
        code = ''
        attrs = build_file.attributes()

        if self.data.file:
            if not os.path.isfile(self.data.code):
                raise RuntimeError('The Python file: {} - cannot be found!' \
                                    .format(self.data.code))

            with open(self.data.code, 'r') as f:
                for l in f:
                    code += l

        elif not attrs[self.data.code]:
            raise RuntimeError('The script "{}" cannot be found in the build.yaml' \
                                .format(self.data.code))

        else:
            # The code is within the build file
            code = build_file.expand(attrs[self.data.code])

        _execute_into_module(
            code,
            self.data.code,
            {
                'build_file': build_file
            }
        )


class FuncCommand(_BuildCommand):
    """
    Function command utility
    """
    alias = 'FUNC'

    def description(self):
        return 'Execute a COMMAND_LIST that we\'ve defined elsewhere.'


    def populate_parser(self, parser):
        """
        Not many options for this
        """
        parser.add_argument(
            'func',
            help='The function to execute',
            nargs=argparse.REMAINDER
        )


    def run(self, build_file):
        """
        Execute the commands with a parser
        """
        from build.parse import BuildCommandParser

        commands, supplied_arguments, global_arguments = build_file.get_function_commands(
            ''.join(self.data.func)
        )

        parser = BuildCommandParser(
            commands,
            build_file,
            build_file.additional,
            supplied=supplied_arguments,
            arguments=global_arguments
        )
        parser.exec_()


class SuperCommand(_BuildCommand):
    """
    Commands for calling template functionality
    """
    alias = 'SUPER'

    def description(self):
        return 'Call commands from an inherited template'


    def populate_parser(self, parser):
        parser.add_argument(
            'command',
            help='"." delimited sequence of keys to grab from our '
                 ' template to search for commands'
        )


    def run(self, build_file):
        """
        Based on the command, search our builf_file templates for a
        viable COMMAND_LIST based on the instruction set
        """
        from build.parse import BuildCommandParser

        template_data = self.data.command.split('.')
        if template_data == ['']:
            raise RuntimeError('Missing template name!')

        template_name = template_data.pop(0)
        template = build_file.included_templates.get(template_name)
        if template is None:
            raise RuntimeError('Template: {} not inherited!'.format(template_name))

        current_location = None
        for section in template_data:
            if current_location is None:
                current_location = template[section]
            else:
                current_location = current_location[section]

        if current_location is None:
            raise RuntimeError('Super commands not found for: {}'.format(self.data.command))

        parser = BuildCommandParser(
            current_location,
            build_file,
            build_file.additional
        )
        parser.exec_()
