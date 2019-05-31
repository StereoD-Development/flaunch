
import os
import sys
import logging
import argparse

from common import utils

# -- Command Control

class CommandRegistry(type):
    """
    A metaclass that builds a registry automatically
    """
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, '_registry'):
            cls._registry = {} # Base Class
        else:
            cls._registry[cls.alias] = cls


@utils.add_metaclass(CommandRegistry)
class _BuildCommand(object):
    """
    Abstract build command. Overload per-command
    """
    alias = None

    def __init__(self, *arguments):
        self._arguments = arguments
        self._parser = argparse.ArgumentParser(
            prog=":" + (self.alias or 'COMMAND'),
            description=self.description()
        )
        self.populate_parser(self._parser)


    def __repr__(self):
        detail = self.alias if hasattr(self, 'alias') else 'Generic'
        return "<(BuildCommand, {})".format(detail)


    def __str__(self):
        def _truncate(arg):
            if len(arg) > 50:
                arg = arg[:47].strip() + '...'
            return arg.replace('\r\n', '\n').replace('\n', '|')

        detail = self.alias if self.alias else 'COMMAND'
        return "{}({})".format(detail, ' '.join(map(_truncate, self._arguments)))


    def _setup(self):
        """
        Called elsewhere so we can introspect the help documentation of
        a command without having to run through any building
        """
        self._data = self._parser.parse_args(self._arguments)

    # -- Virtual Interface

    def description(self):
        return 'Generic command processor'

    def populate_parser(self, parser):
        """
        !Override me!
        Get the argument parser this command supports. This way, we can have both
        options as well as other features for each command type.
        """
        parser.add_argument(
            'args',
            nargs=argparse.REMAINDER,
            help='arguments to pass to our subprocess'
        )


    def run(self, build_file):
        """
        !Override me!
        Execute the comand. By default this just runs the arguments together.

        Overloaded commands (e.g. MOVE, PRINT, etc.) are useful for cutting
        down on the number of platform specific calls that need to be made

        :param build_file: BuildFile object that controls this whole process
        """
        result = utils.run_(self._arguments)

    # -- Public Methods

    @property
    def data(self):
        return self._data


    @classmethod
    def get_command(cls, alias):
        """
        Based on the alias, validate and return and instance of
        the _BuildCommand that can process our data.
        :param alias: The alias that our command is known by
        :return: subclass of _BuildCommand
        """
        if not alias in cls._registry:
            logging.critical('Unknown Command Alias: "{}"'.format(alias))
            sys.exit(1)

        return cls._registry[alias]
