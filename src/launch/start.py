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
import shlex

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


def _prep_launch_jsons(args, env=None):
    """
    A specialty command because this can take another command and process that too!
    :param args: Arguments that we're going to be working with.
    :param env: Pass a pre-existing environment
    :return: int
    """
    root_packages = []
    if args.package:
        for pkglist in args.package:
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

    args.env = env or os.environ.copy()
    args.packages = root_packages
    return resolved_packages


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
    launch_jsons = _prep_launch_jsons(args)
    exec_name = 'launch' if not args.run else 'run'
    env = _prep_env_for_launch(args, args.application, exec_name, args.app_args)
    packages = set(getattr(args, 'packages', []))

    build_locations = os.environ.get(FLAUNCH_BUILD_DIR, [])
    if build_locations:
        build_locations = build_locations.split(os.pathsep)
    build_locations += (args.dev_repo or [])

    #
    # Because this is a proper package, we also prep our launchable package!
    #
    resolved_launch = []
    if not args.run:
        resolved_launch = pkgrep.resolve_packages(
            [args.application], packages,
            builds=build_locations,
            all_ljsons=launch_jsons,
            launching=True
        )

        # -- Swappable dependency management
        this_app = resolved_launch[-1]
        for swap_from, swap_to in this_app.swap():
            all_packages = [lj.package for lj in resolved_launch]

            index = -1
            if swap_from in all_packages:
                index = all_packages.index(swap_from)
                resolved_launch.pop(index)

            if swap_to in all_packages:
                continue
            else:
                packages = pkgrep.resolve_packages(
                    [swap_to], packages,
                    builds=build_locations,
                    all_ljsons=launch_jsons
                )
                for lj in packages:
                    if lj.package not in all_packages:
                        resolved_launch.insert(index, lj)
                        index += 1

    prepped = set()
    for launch_json in resolved_launch + list(launch_jsons):
        if launch_json.package in prepped:
            continue # We've already collected this
        prepped.add(launch_json.package)

        logging.debug('Prepping: {}'.format(launch_json.package))
        pkgrep.prep_env(launch_json, env)
        logging.debug('-- Done Prepping: {}'.format(launch_json.package))

    arguments = args.app_args
    args_consumed = False

    if args.run:
        #
        # Just fire the command passed in using our environment
        #
        executable = args.application
    else:
        #
        # Fire the application up! Get the exectuable within our launch.json. When
        # resolving a package, the last one should _always_ be the launchable
        # application.
        #
        this_app = resolved_launch[-1]
        if not arguments and this_app.default_args():
            arguments = this_app.default_args()

        resolve_env = {}
        resolve_env.update(env)
        checked = set()
        for ljson in launch_jsons:
            if ljson.package in checked:
                continue

            checked.add(ljson.package)
            prep = ljson.prep_env()
            for key in prep:
                key = ljson.expand(key, env)
                resolve_env[key] = ljson.expand(prep[key], resolve_env)

        executable, args_consumed = pkgrep.resolve_exec(
            this_app, resolve_env, arguments
        )

        # Fire any bootstrapping this application requires
        bootstrap_commands = pkgrep.resolve_bootstrap(this_app, env, arguments)
        if bootstrap_commands:
            for command in bootstrap_commands:
                bs_split = shlex.split(command.replace('\\', '/'))
                code = utils.run_(bs_split, env, args.verbose)
                if code != 0:
                    sys.exit(code) # ??

    full_command = shlex.split(executable.replace('\\', '/'))
    if not args_consumed:
        full_command = full_command + arguments

    utils.run_(full_command, env, args.verbose)
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
        parser.add_argument('-i', '--index', help="Use this package index URL to locate packages")

        # -- Environment tools
        parser.add_argument('-p', '--package', action='append', help='The package(s) to use with this command')
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

    return parser


def main():
    """
    Main function for handling our cli
    """
    parser = build_parser()

    original_error = parser.error
    def _e(m): pass # -- We handle the errors ourselves
    parser.error = _e

    if len(sys.argv) < 2:
        parser.print_help()
        return 1

    try:
        args = parser.parse_args()
    except:
        if '-h' in sys.argv or '--help' in sys.argv:
            # Ignore help requests
            if len(sys.argv) <= 2:
                return 0

        if sys.argv[1] in ('launch', 'path', 'clear', 'update'):
            return 1

        parser.error = original_error
        args = parser.parse_args(['launch'] + sys.argv[1:])

    if not vars(args):
        print ("Invalid command! (-h for help)")
        return 1

    log.start(args.verbose, args.log)
    logging.debug("Starting Command...")

    if args.index:
        os.environ["FLAUNCH_CUSTOM_INDEX"] = args.index

    if not hasattr(args, 'func'):
        logging.critical('Unknown command!')
        parser.print_help()
        return 1

    logging.debug("Command: " + args.func.__name__)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
