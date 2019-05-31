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
from common import utils
from common import log

full_description = """Building and deployment toolkit for the Flux ecosystem

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


def build_parser():
    """
    Construct the parser that handles all things related to building/deploying things
    """
    parser = argparse.ArgumentParser(prog='fbuild', description=full_description)
    parser.add_argument('-v', '--verbose', action='store_true', help='Chatty feedback when running')
    subparsers = parser.add_subparsers(help='Commands that can be run')

    # -- Build Management
    builder = subparsers.add_parser('build', help='Build toolkit')
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
    deployer.add_argument('package', help='The package we\'re deploying')
    deployer.set_defaults(func=_deploy)

    helper = subparsers.add_parser('commands', help='Internal fbuild command utils')
    helper.add_argument('-d', '--docs', action='store_true', help='Print all known commands and their arguments')
    helper.set_defaults(func=_commands)

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
        parser.error = original_error
        new_args = []
        for arg in sys.argv[1:]:
            if arg.startswith('-'):
                new_args.append(arg)
            else:
                break
        args, addon = parser.parse_known_args(new_args + ['build'] + sys.argv[len(new_args) + 1:])

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