"""
Entry point for running applicaitons/prepping environments
"""
from __future__ import absolute_import, print_function

__version__ = "1.0.0"

import os
import sys
import platform
import logging
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common import log
from common import utils
from common import communicate
from common.constants import *

import pkgrep

PACKAGE_SPLIT = ':'

def _prep_env_for_launch(args, app, exec_, additional=None):
    """
    Before we start an applicaiton, be it through launch or run,
    we make sure to set the proper environment up
    :param args: Argument set
    :param app: The application we're 
    :return: dict (env)
    """
    env = getattr(args, "env", os.environ.copy())
    packages = getattr(args, "packages", [])

    if packages:
        env.update({
            FLAUNCH_PACKAGES : os.pathsep.join(packages)
        })

    env.update({
        FLAUNCH_APPLICATION : app,
        FLAUNCH_EXEC : exec_
    })

    add_arguments = additional
    if add_arguments is None and hasattr(args, 'arguments'): 
        add_arguments = args.arguments[1:]

    if add_arguments:
        env.update({
            FLAUNCH_ARGUMENTS : os.pathsep.join(add_arguments)
        })

    logging.debug('FLAUNCH Properties: ')
    with log.log_indent():
        logging.debug(
            'FLAUNCH_PACKAGES: ' + env.get(FLAUNCH_PACKAGES, '<none>')
        )
        logging.debug(
            'FLAUNCH_APPLICATION: ' + env.get(
                FLAUNCH_APPLICATION, '<none>'
            )
        )
        logging.debug(
            'FLAUNCH_EXEC: ' + env.get(FLAUNCH_EXEC, '<none>')
        )
        logging.debug(
            'FLAUNCH_ARGUMENTS: ' + env.get(FLAUNCH_ARGUMENTS, '<none>')
        )
    return env


def _prep_env(args, env=None):
    """
    A specialty command because this can take another command and process that too!
    :param args: Arguments that we're going to be working with.
    :param env: Pass a pre-existing environment
    :return: int
    """
    root_packages = []
    for pkglist in args.env:
        root_packages.extend(pkglist.split(PACKAGE_SPLIT))

    #
    # Possible locations that development builds might be located
    #
    build_locations = os.environ.get(FLAUNCH_BUILD_DIR, [])
    if build_locations:
        build_locations = build_locations.split(os.pathsep)
    build_locations += (args.dev_repo or [])

    #
    # Ask for all required packages via atom now so we can unpack everything at
    # once - sparing us recursive http requests
    #
    resolved_packages = pkgrep.resolve_packages(root_packages, set(), build_locations)

    env = env or os.environ.copy()
    for launch_json in resolved_packages:
        #
        # With each of the launch json files, we handle building the environment
        # and other settings in order
        #
        logging.debug('Prepping: {}'.format(launch_json.package))
        pkgrep.prep_env(launch_json, env)
        logging.debug('-- Done Prepping: {}'.format(launch_json.package))

    args.env = env
    args.packages = root_packages
    return args.env


def path_application(args):
    """
    Obtain the root location of a given package and print it to screen
    """
    for package in args.applications:
        pkgrep.print_path(package, args.all)
    return 0


def clear_applications(args):
    """
    Clear out the packages that have been listed
    :param args: Arguments that we're going to be working with.
    :return: int
    """
    for package in args.applications:
        pkgrep.clear_package(package)
    return 0


def run_command(args):
    """
    Run an application
    :param args: Arguments that we're going to be working with.
    :return: int
    """
    logging.debug('Run Command...')
    _prep_env(args)
    env = _prep_env_for_launch(args, args.arguments[0], 'run')
    utils.run_(args.arguments, env, args.verbose)
    return 0


def launch_application(args):
    """
    Launch an application that contains a launch.json

    This differs from the run command in that the launch.json tells flaunch what to actually
    call and, because it's a package, the app can contain all the same abilities that our
    environment building tools do. In essence, it's a env package that can also be called.
    :param args: Arguments that we're going to be working with.
    :return: int
    """
    logging.debug('Launch Command...')
    _prep_env(args)
    exec_name = 'launch' if not args.run else 'run'
    env = _prep_env_for_launch(args, args.application, exec_name, args.app_args)
    packages = set(getattr(args, 'packages', []))

    #
    # Because this is a proper package, we also prep our launchable package!
    #
    if not args.run:
        resolved_launch = pkgrep.resolve_packages([args.application], packages)

        for launch_json in resolved_launch:
            logging.debug('Prepping: {}'.format(launch_json.package))
            pkgrep.prep_env(launch_json, env)
            logging.debug('-- Dont Prepping: {}'.format(launch_json.package))

    if args.run:
        #
        # Just fire the command passed in using our environment
        #
        executable = args.application
    else:
        #
        # Fire the applicaiton up! Get the exectuable within our launch.json. When
        # resolving a package, the last one should _always_ be the launchable
        # application.
        #
        executable = pkgrep.resolve_exec(resolved_launch[-1], env)
    utils.run_([executable] + args.app_args, env, args.verbose)
    return 0


def update_flaunch(args):
    """
    Update the flaunch toolkit locally based on the current version available within
    our package repo
    """
    logging.debug('Checking for FLaunch updates...')
    results = communicate.get_flaunch_info()
    if not results:
        return 1
    pkgrep.update_flaunch(results)
    return 0


def build_parser():
    """
    Build the application parser. Based on all of this, we'll decide on what the user
    wants to do.
    """
    def _fill_parser_with_defaults(parser):
        """
        Fill all parsers with the same defaults
        """
        parser.add_argument('-v', '--verbose', action='store_true', help="Give feedback while working")
        parser.add_argument('-l', '--log', help="Push logging information to a file")
        parser.add_argument('-f', '--force', help="Force redownload any packages that this command uses")

        # -- Environment tools
        parser.add_argument('-e', '--env', action='append', help='The environment to use on this launch')
        parser.add_argument('-d', '--dev-repo', action='append',
                            help="Provide additional directories to scan for development builds")
    
    parser = argparse.ArgumentParser(prog='flaunch', description="Launch an application with possible flux packages")
    subparsers = parser.add_subparsers(help="Commands for flaunch")

    # -- launch
    launch_parser = subparsers.add_parser('launch', help="Launch an applicaiton")
    _fill_parser_with_defaults(launch_parser)
    launch_parser.add_argument('-t', '--detach', action='store_true', help="When launching, detach from this process")
    launch_parser.add_argument('-r', '--run', action='store_true',
                               help="Marks the command as a direct executable rather than a package")
    launch_parser.add_argument('application', help="Application name to launch")
    launch_parser.add_argument('app_args', nargs=argparse.REMAINDER, help="Arguments that we pass to our application")
    launch_parser.set_defaults(func=launch_application)

    # -- path
    path_parser = subparsers.add_parser('path', help="Get the install locations of downloaded applications")
    _fill_parser_with_defaults(path_parser)
    path_parser.add_argument('applications', nargs=argparse.REMAINDER, help="Application name to find")
    path_parser.add_argument('-a', '--all', action='store_true', help='Show all versions currently downloaded')
    path_parser.set_defaults(func=path_application)

    # -- clear
    clear_parser = subparsers.add_parser('clear', help="Clear packages that we may have downloaded")
    _fill_parser_with_defaults(clear_parser)
    clear_parser.add_argument('applications', nargs=argparse.REMAINDER, help="Applications that we're clearing out")
    clear_parser.set_defaults(func=clear_applications)

    # -- update
    update_parser = subparsers.add_parser('update', help="Update the flaunch tool")
    _fill_parser_with_defaults(update_parser)
    update_parser.set_defaults(func=update_flaunch)

    return parser


def main():
    """
    Main function for handling our cli
    """
    parser = build_parser()

    original_error = parser.error
    def _e(m): pass # -- We handle the errors ourselves
    parser.error = _e

    try:
        args = parser.parse_args()
    except:

        # Ignore help requests
        if '-h' in sys.argv or '--help' in sys.argv:
            return 0

        parser.error = original_error
        new_args = []
        for arg in sys.argv[1:]:
            if arg.startswith('-'):
                new_args.append(arg)
            else:
                break
        args = parser.parse_args(['launch'] + sys.argv[1:])

    log.start(args.verbose, args.log)
    logging.debug("Starting Command...")

    if not hasattr(args, 'func'):
        logging.critical('Unknown command!')
        parser.print_help()
        return 1

    logging.debug("Command: " + args.func.__name__)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
