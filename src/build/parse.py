"""
Custom commands that can be run cross-platform by dealing with
the crosplatformness for us
"""
from __future__ import absolute_import

import re
import shlex
import logging

from common import utils
from common import log
from common.platformdict import PlatformDict

from .command import _BuildCommand

# -- Boot all known commands into the registry
# (TODO: Eventual plugin system for commands)
from .commands import *

# -------------------------------------------------------------------
# FIXME: Need to lift these somewhere they can be auto documented and
# expanded upon

def env_check(env, value, build_file):
    return (os.environ.get(env.upper(), None) is value)

def env_set(env, build_file):
    return (os.environ.get(env.upper(), None) is not None)

def prop_set(prop, build_file):
    return (build_file['props'][prop] is not None)

def file_exists(file, build_file):
    return os.path.exists(file)

local_commands = {
    'env_check' : env_check,
    'env_set' : env_set,
    'prop_set' : prop_set,
    'file_exists' : file_exists
}

# -------------------------------------------------------------------

class BuildCommandParser(object):
    """
    Utility for parsing and understanding a command. This will handle
    the various types of commands as well as basic variable expansion
    and the like.
    """
    LOCAL_COMMAND = re.compile(r'^:(?P<alias>[^\s]+)(\s)?(?P<args>(.*))$')

    def __init__(self, commands=[], build_file=None, additional=None, supplied=None, arguments=None):
        if not isinstance(commands, (list, tuple)):
            logging.critical(
                'Commands must be in an array!, Got {}' .format(type(commands))
            )
            with log.log_indent():
                logging.critical('Build File: {}'.format(build_file.path))
            sys.exit(1)

        self._commands = commands
        self._build_file = build_file
        self._additional = additional
        self._supplied = supplied

        self._temp_properties = {}
        if arguments is not None:
            for argument in arguments:
                cli_name = '--' + argument.replace('_', '-')
                if cli_name in self._additional:
                    idx = self._additional.index(cli_name)
                    if idx + 2 <= len(self._additional):
                        self._temp_properties[argument] = self._additional[idx + 1]


    def exec_(self):
        """
        Run through our commands and run them!
        """
        with self._build_file.overload(self._temp_properties):

            if self._supplied:
                for arg, val in utils._iter(self._supplied):
                    # Will revert once overload is over
                    self._build_file.add_attribute(arg, self._build_file.expand(val))

            self._exec_internal(self._commands)


    def _exec_internal(self, commands):
        """
        Iterate through commands and do our bidding with them
        :param commands: list[varaint] of commands that we're processing
        """
        for command_info in commands:
            if isinstance(command_info, list):
                #
                # In the event we have a list, this means we
                # have conditional execution
                #
                negative = []
                if len(command_info) > 2:
                    condition, commands, negative = command_info
                else:
                    condition, commands = command_info
                if not isinstance(condition, (list, tuple)):
                    condition = (condition,)

                # http://book.pythontips.com/en/latest/for_-_else.html
                for c in condition:

                    # NOT gate
                    not_logic = False
                    if c.startswith('!'):
                        not_logic = True
                        c = c[1:]

                    if not c.startswith('--'):
                        if c in self._build_file['props']:
                            if not_logic:
                                break # We have it but don't want it
                        elif not not_logic:
                            break # We don't have it and want it

                    elif c in self._additional:
                        if not_logic:
                            break # We have it but don't want it

                    elif not not_logic:
                        break # We don't have it and want it

                else:
                    # Ready to run!
                    if not isinstance(commands, (list, tuple)):
                        commands = [commands]
                    if self._exec_internal(commands) == _BuildCommand.RETURN_COMMAND:
                        return _BuildCommand.RETURN_COMMAND
                    continue

                # If we've made it here, it means we broke out, therefore we
                # should check if we have a negative command set
                if negative:
                    if isinstance(negative, (list, tuple)):
                        if self._exec_internal(negative) == _BuildCommand.RETURN_COMMAND:
                            return _BuildCommand.RETURN_COMMAND
                    else:
                        if self._exec_internal([negative]) == _BuildCommand.RETURN_COMMAND:
                            return _BuildCommand.RETURN_COMMAND

            elif isinstance(command_info, dict):
                #
                # The dictionary is used for more complex actionable
                # events.
                #

                # For the sake of conformity, we push the additional checking to a
                # playform dictionary to ease routing and let users have
                # different command paths per system
                command_info = PlatformDict.simple(command_info)

                if isinstance(command_info, (dict, PlatformDict)):
                    command_info_raw = command_info.to_dict()
                    commands_from_dict = command_info_raw.get('commands')
                    else_commands_from_dict = command_info_raw.get('else_commands')

                    #
                    # If we're still a dictionary, then we'll
                    # want to look for a clause
                    #
                    if command_info_raw.get('clause'):
                        python_to_eval = self._build_file.expand(command_info_raw['clause'])
                        logging.debug('Evaluating: {}'.format(python_to_eval))

                        is_command = False
                        if '(' in python_to_eval:
                            is_command = python_to_eval[:python_to_eval.index('(')].split(" ")[-1] in local_commands
                        if is_command and python_to_eval.endswith(')'):
                            # All of the quick commands take the build file as the last arg
                            python_to_eval = python_to_eval[:-1] + ', build_file)'

                        local_commands['build_file'] = self._build_file
                        if not (eval(python_to_eval, local_commands)):
                            if else_commands_from_dict:
                                # We didn't suceed but we have false conditions
                                commands_from_dict = else_commands_from_dict
                            else:
                                continue # - Nothing to do

                    if isinstance(commands_from_dict, (list, tuple)):
                        if self._exec_internal(commands_from_dict) == _BuildCommand.RETURN_COMMAND:
                            return _BuildCommand.RETURN_COMMAND
                    else:
                        if self._exec_internal([commands_from_dict]) == _BuildCommand.RETURN_COMMAND:
                            return _BuildCommand.RETURN_COMMAND

                elif isinstance(command_info, (list, tuple)):
                    # Just a platform reroute
                    if self._exec_internal(command_info) == _BuildCommand.RETURN_COMMAND:
                        return _BuildCommand.RETURN_COMMAND

                elif isinstance(command_info, utils.string_types):
                    # Single command platform reroute
                    if self._exec_internal([command_info]) == _BuildCommand.RETURN_COMMAND:
                        return _BuildCommand.RETURN_COMMAND


            elif isinstance(command_info, utils.string_types):
                #
                # A string is a direct command
                #
                this_command = self.parse(command_info)
                this_command._setup() # Vital, see the docstring for more
                logging.debug(str(this_command))
                with log.log_indent():
                    result = this_command.run(self._build_file)
                    if result == _BuildCommand.RETURN_COMMAND:
                        return _BuildCommand.RETURN_COMMAND # We want to brak out of this loop!

            else:
                logging.critical(
                    'Command, unknown type: {}'.format(type(command_info))
                )
                sys.exit(1) # Should we just move to a raise?


    def parse(self, command_string):
        """
        Based on the command string provided, parse and build the path we're
        going to need.
        :param command_string: The command comming from our build.yaml
        """
        match = BuildCommandParser.LOCAL_COMMAND.match(command_string)
        if match:
            d = match.groupdict()

            arguments = shlex.split(d['args'])
            cmd = _BuildCommand.get_command(d['alias'].upper())
        else:
            arguments = shlex.split(command_string)
            cmd = _BuildCommand

        expanded = []
        for arg in arguments:
            expanded.extend(self._build_file.expand(arg, rtype=list))

        return cmd(*expanded)
