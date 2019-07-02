"""
Entry point fot the build/deployment tools
"""
from __future__ import absolute_import, print_function

import os
import sys
import argparse
import logging
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build import manage
from build import command
from build import compose
from build import deploy
from build import raw
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
    #
    # Before we build - we have to check if the user is asking for a particular
    # branch or tag. If they are, we need to make sure we're on that before
    # peering into the build.yaml in the event it's different than the current
    # branch
    #
    # TODO

    manager = manage.BuildManager.get_manager(args.package, args)
    manager.run_build()
    logging.info('Build Complete')


def _deploy(args):
    """
    The entry point for the deploy toolkit
    :param args: The args namespace object our parser returns
    :return: None
    """
    manager = deploy.DeployManager.get_manager(args.package, args)
    manager.run_deploy()
    logging.info('Deployment Complete')


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


def _register(args):
    """
    Registration utility for Flux
    :param args: The args namespace object our parser returns
    :return: None
    """
    manager = deploy.DeployManager.get_manager(args.package, args)
    if manager.run_registration():
        logging.info('Registration Complete')


def _raw(args):
    """
    Exection of arbtrary COMMAND_LISTS fed through our build.yaml file
    :return: None
    """
    manager = raw.RawCommandManager.get_manager(args.package, args)
    if args.list_commands:
        print ("Raw commands for: {}".format(args.package))
        data = manager.all_commmands()
        for comm, info in sorted(data.items()):

            help_, args = info

            print ("-----------------------------------------------")
            print ('-', comm + ':')
            for l in help_.strip().split('\n'):
                print ("    ", l)

            print ("     - Arguments:")
            for arg in args:
                printme = arg
                if isinstance(arg, list):
                    if len(arg) > 1:
                        printme = arg[0] + ': ' + arg[1]
                    else:
                        printme = arg[0]
                print ("        ", printme)

            print ("")
    else:
        if args.command_name is None:
            print ("Please provide a command to run! (use \"fbuild {}\" for available commands)".format(
                ' '.join(sys.argv[1:] + ['--list-commands'])
            ))
            sys.exit(1)
        manager.run_raw_commands()


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
        parser.add_argument('-i', '--index', help="Use this package index URL to locate packages")

    parser = argparse.ArgumentParser(prog='fbuild', description=full_description)
    subparsers = parser.add_subparsers(help='Commands that can be run')

    # -- Build Management
    builder = subparsers.add_parser('build', description='Build toolkit')
    _fill_parser_with_defaults(builder)
    builder.add_argument('package', help='The package we\re building')
    builder.add_argument('-c', '--custom', nargs=2, metavar=('YAML', 'SOURCE'), help='Custom yaml file and source directory location')
    builder.add_argument('-o', '--output-directory', metavar='DIR', help='Custom build location to place these files into')
    builder.add_argument('-n', '--no-clean', action='store_true', help='For complex builds, do not destroy the build '
                                                                       'directory. Also known as a delta build')
    builder.add_argument('-t', '--tag', help='Tag to checkout')
    builder.add_argument('-b', '--branch', help='Branch to checkout')
    builder.add_argument('-g', '--git', help='Custom git link to pull from')
    builder.set_defaults(func=_build)

    # -- Deploy Management
    deployer = subparsers.add_parser('deploy', description='Deployment toolkit')
    _fill_parser_with_defaults(deployer)
    deployer.add_argument('package', help='The package we\'re deploying')
    deployer.add_argument('version', help='The version that we\'re deploying')
    deployer.add_argument('-t', '--transfer', action='store_true', help='Transfer material around the globe')
    deployer.add_argument(
        '-s', '--skip-wait',
        action='store_true',
        help='Don\'t wait for transfers to complete before returning',
    )
    deployer.add_argument('-d', '--destination', action='append', help='Facility codes to transfer to (e.g. tor, mad, etc.)')
    deployer.add_argument('-e', '--exclude', action='append', help='Facility codes to not transfer to')
    deployer.add_argument('-p', '--platform', action='append', help='Supply specific platforms to trasnfer for')
    deployer.add_argument('-c', '--custom', nargs=2, metavar=('YAML', 'SOURCE'), help='Custom yaml file and source directory location')
    deployer.set_defaults(func=_deploy)

    # -- Basic utility toolchain (TODO)
    helper = subparsers.add_parser('commands', description='Internal fbuild command utils')
    _fill_parser_with_defaults(helper)
    helper.add_argument('-d', '--docs', action='store_true', help='Print all known commands and their arguments')
    helper.set_defaults(func=_commands)

    # -- Registration
    register = subparsers.add_parser('release', description='Register a version with Flux. Do this last')
    _fill_parser_with_defaults(register)
    register.add_argument('package', help='The package that we want to register with Flux')
    register.add_argument('version', help='The version of the package that we\'re sending to Flux')
    register.add_argument('-b', '--beta', action='store_true', help='This is a pre-release, not production current')
    register.add_argument('-f', '--force', action='store_true', help='Force the version even if it already exists on Atom')
    register.add_argument('-s', '--skip-validation', action='store_true', help='Skip global file validation (careful)')
    register.add_argument('-c', '--custom', nargs=2, metavar=('YAML', 'SOURCE'), help='Custom yaml file and source directory location')
    register.set_defaults(func=_register)

    # -- Raw Command Toolkit
    raw_commands = subparsers.add_parser('raw', description='Run loose structured commands from our build.yaml files')
    _fill_parser_with_defaults(raw_commands)
    raw_commands.add_argument('package', help='The package that we\'re running commands through')
    raw_commands.add_argument('command_name', nargs='?', help='The command list to execute (key underneath the "raw" section of the build.yaml)')
    raw_commands.add_argument('-l', '--list-commands', action='store_true', help='Provide a listing of possible commands')
    raw_commands.add_argument('-c', '--custom', nargs=2, metavar=('YAML', 'SOURCE'), help='Custom yaml file and source directory location')
    raw_commands.set_defaults(func=_raw)

    # -- Launcher composer
    composer = subparsers.add_parser('compose', description='Create a custom flaunch command')
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

    if len(sys.argv) < 2:
        parser.print_help()
        return 1

    try:
        args, addon = parser.parse_known_args()
    except Exception as e:
        # print (traceback.format_exc())
        # Ignore help requests
        if '-h' in sys.argv or '--help' in sys.argv:
            return 0

        parser.error = original_error

        if sys.argv[1] in ('build', 'raw', 'deploy', 'compose', 'commands'):
            return 1

        args, addon = parser.parse_known_args(['build'] + sys.argv[1:])

    if not vars(args):
        print ("Invalid command! (-h for help)")
        return 1

    if args.index:
        os.environ["FLAUNCH_CUSTOM_INDEX"] = args.index

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