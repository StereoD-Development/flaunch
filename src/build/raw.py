"""
Raw command tools!
"""
from __future__ import absolute_import

import re
import os
import sys
import logging
import argparse
from functools import wraps

from common.utils import yaml
from common import utils
from .abstract_manager import _AbstractManager
from .parse import BuildCommandParser
from .buildfile import BuildFile

class RawCommandManager(_AbstractManager):
    """
    Utility class for executing arbitrary commands help within a build.yaml file
    """
    type_ = 'raw'

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


    def all_commmand_parsers(self):
        """
        :return: dict[str:(str,iterable)] of command name to any help docs
        """
        return (self.parser_from_command(c) for c in self.raw_commands())


    def parser_from_command(self, name):
        """
        Using the descriptor of our command, build an argparse.ArgumentParser that
        can handle it, making it easy for the tools to wrap around the commands.
        :param name: The name of the command we want the parser of
        :return: argparse.ArgumentParser instance
        """
        command = self.raw_commands()[name]

        def _to_args(arg_data):
            r = []
            o = []
            for d in (arg_data or []):
                n = d
                if isinstance(d, (list, tuple)):
                    n = d[0]
                if n.startswith('--'):
                    o.append(d)
                else:
                    r.append(d)
            return r, o

        required, optional = _to_args(command['arguments'])
        flags = command['flags'] or []

        # Let python argparsing do the work
        parser = argparse.ArgumentParser(
            prog=name,
            description=command['help'] or '',
            epilog=command['epilog'],
            add_help=False
        )

        class _doc(argparse._StoreTrueAction):
            def __call__(self, parser, namespace, values, option_string=None):
                parser.print_help()
                sys.exit(1)

        parser.add_argument('--docs', action=_doc, help="Print this help information and exit")

        def _info(d):
            """
            Get the name of the action, help docs, and any regex patterns
            to match to.
            :return: tuple(name, help|'', regex|None)
            """
            if not isinstance(d, (list, tuple)):
                return (d, '', None)
            output = [None, '', None]
            for i, v in enumerate(d):
                output[i] = v
            return tuple(output)

        def _regex_wrapper(regex):
            """
            :return: A wrapped function that will give us a regex matcher based
            on the pattern passsed to the type matcher
            """
            pattern = re.compile(regex)

            @wraps(_regex_wrapper)
            def _type_match(argument_value):
                if not pattern.match(argument_value):
                    raise argparse.ArgumentTypeError("Doesn't match pattern \"{}\""\
                        .format(regex))
                return argument_value

            return _type_match

        for req in required:
            req_name, help_, regex = _info(req)
            kwargs = { "help" : help_ }
            if regex:
                kwargs['type'] = _regex_wrapper(regex)
            parser.add_argument(req_name, **kwargs)

        for opt in optional:
            opt_name, help_, regex = _info(opt)
            kwargs = { "help" : help_ }
            if regex:
                kwargs['type'] = _regex_wrapper(regex)
            parser.add_argument(utils.cli_name(opt_name), **kwargs)

        for flag in flags:
            flag_name, help_, _ = _info(flag)
            parser.add_argument(utils.cli_name(flag_name), help=help_)

        return parser


    def run_raw_commands(self):
        """
        Get the commands and fire away!
        """
        this_command = self.raw_commands()[self._command]
        parser = self.parser_from_command(name=self._command)

        # if '--docs' in self.additional:
        #     parser.print_help()
        #     sys.exit(1)

        parsed_args = parser.parse_args(self.additional)

        with self.build_file.overload(vars(parsed_args)):
            self.build_commands(
                condition=None, build_data=this_command['commands'], type_='Raw'
            )
