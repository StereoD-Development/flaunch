"""
Entry point fot the build/deployment tools
"""
from __future__ import absolute_import

import os
import sys
import argparse
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build import manage
from build import command
from build import compose
from common import utils
from common import log

full_description = """Building and deployment toolkit for the Flux ecosystem.
The flaunchdev suite of commands is build to help serve as a boundary between developer,
their development environments, and production stable code. This is not to be confused
with a build management software a-la buildbot, 
"""

def _build(args):
    """
    The entry point for the build toolkit
    :param args: The args namespace object our parser returns
    :return: None
    """
    manager = manage.BuildManager.get_manager(args.package, args)
    manager.run_build()
    logging.info('Build Complete')


def _deploy(args):
    """
    The entry point for the deploy toolkit
    :param args: The args namespace object our parser returns
    :return: None
    """
    pass


def _commands(args):
    """
    Internal commands utility
    :param args: The args namespace object our parser returns
    :return: None
    """
    if args.docs:
        #
        # Print the documentation omn each of the commands we know about
        #
        print ("Available Commands:")
        for _, command_class in utils._iter(command._BuildCommand._registry):
            inst = command_class([])
            print ("")
            print ("{0}\n{1}\n{2}".format("--"*25, inst.alias, '-'*len(inst.alias)))
            inst._parser.print_help()


def _compose(args):
    """
    Composing a launcher
    """
    composer = compose.Composer(args)
    composer.exec_()


def build_parser():
    """
    Construct the parser that handles all things related to building/deploying things
    """
    def _fill_parser_with_defaults(parser):
        parser.add_argument('-v', '--verbose', action='store_true', help='Chatty feedback when running')

    parser = argparse.ArgumentParser(prog='fbuild', description=full_description)
    subparsers = parser.add_subparsers(help='Commands that can be run')

    # -- Build Management
    builder = subparsers.add_parser('build', help='Build toolkit')
    _fill_parser_with_defaults(builder)
    builder.add_argument('package', help='The package we\re building')
    builder.add_argument('-c', '--custom', nargs=2, metavar=('YAML', 'SOURCE'), help='Custom yaml file and source directory location')
    builder.add_argument('-o', '--output-directory', metavar='DIR', help='Custom build location to place these files into')
    builder.add_argument('-l', '--local', action='store_true', help='Build based on local files (for development)')
    builder.add_argument('-n', '--no-clean', action='store_true', help='For complex builds, do not destroy the build '
                                                                       'directory. Also known as a delta build')
    builder.add_argument('-t', '--tag', help='Tag to checkout')
    builder.add_argument('-b', '--branch', help='Branch to checkout')
    builder.add_argument('-g', '--git', help='Custom git link to pull from')
    builder.set_defaults(func=_build)

    # -- Deploy Management
    deployer = subparsers.add_parser('deploy', help='Deployment toolkit')
    _fill_parser_with_defaults(deployer)
    deployer.add_argument('package', help='The package we\'re deploying')
    deployer.set_defaults(func=_deploy)

    helper = subparsers.add_parser('commands', help='Internal fbuild command utils')
    _fill_parser_with_defaults(helper)
    helper.add_argument('-d', '--docs', action='store_true', help='Print all known commands and their arguments')
    helper.set_defaults(func=_commands)

    # -- Launcher composer
    composer = subparsers.add_parser('compose', help='Create a custom flaunch command')
    _fill_parser_with_defaults(composer)
    composer.add_argument('name', help='The "launcher" name')
    composer.add_argument('version', help='The version that is assigned to this "launcher"')
    composer.add_argument('-p', '--package', action='append', help='Package this launcher requires')
    composer.add_argument('-l', '--launch', help='The package that this launcher executes')
    composer.add_argument('-u', '--pre-release', action='store_true', help='When registering, don\'t make this the active version')
    composer.add_argument('-r', '--run', action='store_true', help='This is a direct execution (within our environment)')
    composer.add_argument('-a', '--arg', action='append', help='The default arguments to pass to the launched process')
    composer.add_argument('-e', '--env', action='append', help='The environment variables to set whehn running this launcher (VAR_NAME=value)')
    composer.add_argument('-f', '--force-update', action='store_true', help='Force update if the version exists')
    composer.set_defaults(func=_compose)

    return parser


def main():
    #
    # Parse and run our cammand
    #

    parser = build_parser()

    original_error = parser.error
    def _e(m): pass # -- We handle the errors ourselves
    parser.error = _e

    try:
        args, addon = parser.parse_known_args()
    except:
        # Ignore help requests
        if '-h' in sys.argv or '--help' in sys.argv:
            return 0

        parser.error = original_error

        if sys.argv[1] in ('build', 'deploy', 'compose', 'commands'):
            return 1

        args, addon = parser.parse_known_args(['build'] + sys.argv[1:])

    args.additional_arguments = addon

    log.start(args.verbose)
    logging.debug("Starting Command...")

    if not hasattr(args, 'func'):
        logging.critical('Unknown command!')
        parser.print_help()
        return 1

    logging.debug("Command: " + args.func.__name__[1:])
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())