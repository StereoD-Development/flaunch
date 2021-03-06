"""
Entry point fot the build/deployment tools
"""
from __future__ import absolute_import, print_function

import os
import sys
import argparse
import platform
import logging
import traceback

_root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ['_FLAUNCH_ROOT_DIR'] = os.path.dirname(_root_path).replace('\\', '/')

sys.path.append(_root_path)

from build import manage
from build import command
from build import compose
from build import deploy
from build import test
from build import prep
from build import raw

from common import constants
from common import transfer
from common import gitutil
from common import utils
from common import log

full_description = """Building and deployment toolkit for the Flux ecosystem.
The fbuild suite of commands is built to help serve as a boundary between developer,
their development environments, and production stable code. This is not to be confused
with a build management software a-la buildbot - at least not yet.

The other major key is unity via simplicity. Creating environments where the same
commands works on multiple machines and platforms handling the differences in a
seamless way.
"""

def _fail_or_pass(result):
    """
    Minor util to exit if we hit a failure on the gitutil functions.
    :param result: boolean
    :return: None
    """
    if not result:
        sys.exit(1)


def _go_to_repo(args):
    """
    Quick way to move into a repository
    :param args: arguments that were supplied via argparse
    :return: None
    """
    repo_path = os.path.join(
        os.environ.get(constants.FLAUNCH_DEV_DIR, os.path.dirname(os.getcwd())),
        args.package
    )

    if not os.path.exists(repo_path):
        if args.git:
            _fail_or_pass(gitutil.clone_repo(args.git))
        else:
            logging.error('Cannot find repository! (include --git with link if needed)')
            sys.exit(1)
        os.chdir(args.package) # Not foolproof
    else:
        os.chdir(repo_path)


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
    if args.package == '.':
        args.package = os.path.basename(os.getcwd())

    if args.branch or args.tag:
        _go_to_repo(args)
        _fail_or_pass(gitutil.fetch())
        _fail_or_pass(gitutil.stash())
        _fail_or_pass(gitutil.checkout(branch=args.branch, tag=args.tag))

    manager = manage.BuildManager.get_manager(args.package, args)
    manager.run_build()
    logging.info('Build Complete')


def _prep(args):
    """
    The first process in a full-scale deployment. This is used to tag our content for
    a specific point across platforms which can then be used to trigger a full build
    and deploy procedure across the gamut.

    examples:

        fbuild prep Helios 1.2.0
        fbuild prep Helios 1.2.0 --jenkins
        fbuild prep Helios 1.2.0 --jenkins-deploy

    :param args: The args namespace object our parser returns
    :return: None    
    """
    _go_to_repo(args)
    _fail_or_pass(gitutil.fetch())

    code_hash = None
    if args.hash:
        code_hash = args.hash
    elif args.branch:
        code_hash = gitutil.git_hash(args.branch)

    logging.info('Tagging: {}'.format(args.version))
    _fail_or_pass(gitutil.tag(args.version, code_hash))
    _fail_or_pass(gitutil.push_tag(args.version, args.remote))

    # If we've made it here, we can assume we've taged the 
    manager = prep.PrepManager.get_manager(args.package, args)
    manager.run_prep()
    logging.info('Prep Complete')


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

        parsers = manager.all_commmand_parsers()
        for parser in sorted(parsers, key=lambda x: x.prog):

            print ("")
            print ("-----------------------------------------------")
            print ("")
            print (">>> COMMAND: {}".format(parser.prog))
            parser.print_help()

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


def _transfer(args):
    """
    Transfer packages based on the arguments
    """
    logging.info('Initialize transfer interface...')

    destinations = args.destination
    if not destinations:
        logging.info('No destinations supplied, ignoring')
        sys.exit(0)

    package_to_version = {}
    for package in args.package:

        if '/' in package:
            package, version = package.split('/', 1)
            package_to_version[package] = version
            continue

        if not args.version:
            logging.error('Version not provided for {}. Please provide'
                          .format(package))
            sys.exit(1)
        package_to_version[package] = args.version

    platforms = set([platform.system()])
    if args.all_platforms:
        platforms |= set(['Windows', 'Linux', 'Darwin'])

    build_file = utils.flaunch_build_file()

    for package, version in package_to_version.items():
        logging.info('Transfer: {}/{}'.format(package, version))
        package_file = '{}.{}.zip'.format(package, version)
        transfer.transfer_package(
            build_file,
            package_name=package,
            package_file=package_file,
            destinations=args.destination,
            platforms=list(platforms),
            wait=False # Option?
        )


def _test(args):
    """
    Execute a test
    """
    testing_manager = test.TestManager.get_manager(args.package, args)
    testing_manager.run_tests()
    logging.info('Testing Complete')


def _initialize(args):
    """
    Initalize a package
    """
    utils.initialize_pacakge(args)


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
    builder.add_argument('-r', '--build-required', action='store_true', help='Build any dependent packages (must have a build.yaml available)')
    builder.set_defaults(func=_build, _flaunch_parser=builder)

    # -- Deploy Prep Management
    prepper = subparsers.add_parser('prep', description='Utility kit for prepparing a package for deployment and release')
    _fill_parser_with_defaults(prepper)
    prepper.add_argument('package', help='The package that we\'re deploying')
    prepper.add_argument('version', help='The version that we\'re deploying (hint: This is the git tag that\'s created)')
    prepper.add_argument('-c', '--custom', nargs=2, metavar=('YAML', 'SOURCE'), help='Custom yaml file and source directory location')
    prepper.add_argument('-b', '--branch', help='The branch to create our tag from')
    prepper.add_argument('-s', '--hash', help='A specific commit hash to use for our tag')
    prepper.add_argument('-g', '--git', help='Custom git link to pull from')
    prepper.add_argument('-r', '--remote', help='Remote to use (default is origin)', default='origin')
    prepper.set_defaults(func=_prep, _flaunch_parser=prepper)


    # -- Deploy Management
    deployer = subparsers.add_parser('deploy', description='Deployment toolkit')
    _fill_parser_with_defaults(deployer)
    deployer.add_argument('package', help='The package we\'re deploying')
    deployer.add_argument('version', help='The version that we\'re deploying')
    deployer.add_argument('-t', '--transfer', action='store_true', help='Copy material to repository and transfer around the globe')
    deployer.add_argument(
        '-s', '--skip-wait',
        action='store_true',
        help='Don\'t wait for transfers to complete before returning',
    )
    deployer.add_argument('-d', '--destination', action='append', help='Facility codes to transfer to (e.g. tor, mad, etc.)')
    deployer.add_argument('-e', '--exclude', action='append', help='Facility codes to not transfer to')
    deployer.add_argument('-p', '--platform', action='append', help='Supply specific platforms to transfer for')
    deployer.add_argument('-c', '--custom', nargs=2, metavar=('YAML', 'SOURCE'), help='Custom yaml file and source directory location')
    deployer.set_defaults(func=_deploy, _flaunch_parser=deployer)

    # -- Basic utility toolchain (TODO)
    helper = subparsers.add_parser('command', description='Internal fbuild command utils')
    _fill_parser_with_defaults(helper)
    helper.add_argument('-d', '--docs', action='store_true', help='Print all known commands and their arguments')
    helper.set_defaults(func=_commands, _flaunch_parser=helper)

    # -- Registration
    register = subparsers.add_parser('release', description='Register a version with Flux. Do this last')
    _fill_parser_with_defaults(register)
    register.add_argument('package', help='The package that we want to register with Flux')
    register.add_argument('version', help='The version of the package that we\'re sending to Flux')
    register.add_argument('-b', '--beta', action='store_true', help='This is a pre-release, not production current')
    register.add_argument('-f', '--force', action='store_true', help='Force the version even if it already exists on Atom')
    register.add_argument('-s', '--skip-validation', action='store_true', help='Skip global file validation (careful)')
    register.add_argument('-c', '--custom', nargs=2, metavar=('YAML', 'SOURCE'), help='Custom yaml file and source directory location')
    register.set_defaults(func=_register, _flaunch_parser=register)

    # -- Raw Command Toolkit
    raw_commands = subparsers.add_parser('raw', description='Run loose structured commands from our build.yaml files')
    _fill_parser_with_defaults(raw_commands)
    raw_commands.add_argument('package', help='The package that we\'re running commands through')
    raw_commands.add_argument('command_name', nargs='?', help='The command list to execute (key underneath the "raw" section of the build.yaml)')
    raw_commands.add_argument('-l', '--list-commands', action='store_true', help='Provide a listing of possible commands')
    raw_commands.add_argument('-c', '--custom', nargs=2, metavar=('YAML', 'SOURCE'), help='Custom yaml file and source directory location')
    raw_commands.set_defaults(func=_raw, _flaunch_parser=raw_commands)

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
    composer.add_argument('-e', '--env', action='append', help='The environment variables to set when running this launcher (VAR_NAME=value)')
    composer.add_argument('-f', '--force-update', action='store_true', help='Force update if the version exists')
    composer.set_defaults(func=_compose, _flaunch_parser=composer)

    # -- Test toolkit
    tester = subparsers.add_parser('test', description='Execute tests on a package')
    _fill_parser_with_defaults(tester)
    tester.add_argument('-c', '--custom', nargs=2, metavar=('YAML', 'SOURCE'), help='Custom yaml file and source directory location')
    tester.add_argument('package', help='The package that we\'re running the test on')
    tester.set_defaults(func=_test, _flaunch_parser=tester)

    # -- Transfer Utilities
    transferer = subparsers.add_parser('transfer', description='Transfer packages about the world')
    _fill_parser_with_defaults(transferer)
    transferer.add_argument('-p', '--package', action='append', help='Package(s) that we want to shuttle. If a specific version should be transfered, use <package>/<version>')
    transferer.add_argument('-a', '--all-platforms', action='store_true', help='Transfer all platforms available')
    transferer.add_argument('-d', '--destination', action='append', help='Facility codes to transfered')
    transferer.add_argument('version', nargs='?', help='Default version to use if not ')
    transferer.set_defaults(func=_transfer, _flaunch_parser=transferer)

    initializer = subparsers.add_parser('init', description='Initialize a package with a build.yaml')
    _fill_parser_with_defaults(initializer)
    initializer.add_argument('-f', '--file', action='append', help='Add files to the build command')
    initializer.add_argument('-m', '--merge', help='yaml file that will be merged into the new build.yaml')
    initializer.set_defaults(func=_initialize, _flaunch_parser=initializer)

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
