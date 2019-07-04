"""
Basic i/o commands for fbuild

NOTE: DON'T sys.exit(1) out of here. We're trying to catch these
errors for better reporting.
"""
from __future__ import print_function, absolute_import

import os
import sys
import glob
import shutil
import fnmatch
import logging
import argparse
import tempfile
import platform
from contextlib import contextmanager
from collections import deque

from common import utils
from build.command import _BuildCommand

class CopyCommand(_BuildCommand):
    """
    Copy command! Woo!
    """
    alias = 'COPY'

    def description(self):
        return 'Copy files from one location to another'


    def populate_parser(self, parser):
        """
        Copying files has many-a-caveat
        """
        parser.add_argument('-x', '--exclude', nargs='+', help="file patterns to ignore")
        parser.add_argument('-m', '--make-dirs', action='store_true', help='Create the destination directory')
        parser.add_argument('-f', '--force', action='store_true', help='Overwrite any files that already exist')
        parser.add_argument('source', help='The source location')
        parser.add_argument('destination', help='The destination location')

    def run(self, build_file):
        """
        Copy files in a platform agnostic way
        """
        if self.data.make_dirs:
            if not self.data.force and os.path.isfile(self.data.destination):
                raise RuntimeError(
                    'Destination Already Exists: {} (Consider using the --force flag)' \
                    .format(self.data.destination)
                )

            elif not os.path.exists(os.path.dirname(self.data.destination)):
                os.makedirs(os.path.dirname(self.data.destination))

        elif not os.path.isdir(os.path.dirname(self.data.destination)):
            raise RuntimeError(
                'Destination directory does not exist! {} (Consider using the --make-dirs flag)' \
                .format(os.path.dirname(self.data.destination))
            )

        if not self.data.force and os.path.isfile(self.data.destination):
            raise RuntimeError(
                'Destination Already Exists: {} (Consider using the --force flag)' \
                .format(self.data.destination)
            )

        logging.info('Copying: {} -> {}'.format(self.data.source, self.data.destination))

        # This could probably use some clean up but it'll get the job done for now

        data = glob.glob(self.data.source)

        root = ''
        if '*' in self.data.source:
            root = self.data.source[:self.data.source.index('*')].replace('\\', '/')
            if root.endswith('/'):
                root = root[:-1]

        destination = self.data.destination
        if len(data) > 1 and not os.path.exists(destination):
            os.makedirs(destination)

        elif os.path.isdir(self.data.destination) and os.path.isfile(data[0]):
            destination = os.path.join(self.data.destination, os.path.basename(data[0]))

        ignore_patterns = self.data.exclude or []
        ignore_func = shutil.ignore_patterns(*ignore_patterns)

        for d in data:
            base = d.replace('\\', '/').replace(root, '')

            # For globbing, we have to make sure the destination is up to date
            if root:
                if base.startswith('/'):
                    base = base[1:]
                dest = destination + '/' + base
            else:
                dest = destination

            ok = True
            for pattern in ignore_patterns:
                if fnmatch.fnmatch(base, pattern):
                    ok = False
                    break
            if not ok:
                continue

            if os.path.exists(dest) and self.data.force:
                if os.path.isfile(dest):
                    os.unlink(dest)
                else:
                    shutil.rmtree(dest)

            if os.path.isdir(d):
                shutil.copytree(d, dest, symlinks=True, ignore=ignore_func)
            else:
                shutil.copy2(d, dest)


class MoveCommand(_BuildCommand):
    """
    Simple platform-agnostic move command
    """
    alias = 'MOVE'


    def description(self):
        return 'Move files from one location to another'


    def populate_parser(self, parser):
        """
        Moving files takes at least a source and a destination
        """
        parser.add_argument('-x', '--exclude', nargs='+', help="file patterns to ignore")
        parser.add_argument('-m', '--make-dirs', action='store_true', help='Create the destination directory')
        parser.add_argument('-f', '--force', action='store_true', help='Overwrite any files that already exist')
        parser.add_argument('source', help="The source file(s)")
        parser.add_argument('destination', help="The destination location")


    def run(self, build_file):
        """
        Move our files from source to destination!
        :return : None
        """
        if self.data.make_dirs:
            if not self.data.force and os.path.exists(self.data.destination):
                raise RuntimeError(
                    'Destination Already Exists: {} (Consider using the --force flag)' \
                    .format(self.data.destination)
                )

            elif not os.path.exists(os.path.dirname(self.data.destination)):
                os.makedirs(os.path.dirname(self.data.destination))


        elif not os.path.isdir(os.path.dirname(self.data.destination)):
            raise RuntimeError(
                'Destination directory does not exist! {} (Consider using the --make-dirs flag)' \
                .format(os.path.dirname(self.data.destination))
            )

        if not self.data.force and os.path.isfile(self.data.destination):
            raise RuntimeError(
                'Destination Already Exists: {} (Consider using the --force flag)' \
                .format(self.data.destination)
            )

        logging.info('Moving: {} -> {}'.format(self.data.source, self.data.destination))

        data = glob.glob(self.data.source)

        root = ''
        if '*' in self.data.source:
            root = self.data.source[:self.data.source.index('*')].replace('\\', '/')
            if root.endswith('/'):
                root = root[:-1]

        if len(data) > 1 and not os.path.exists(self.data.destination):
            os.makedirs(self.data.destination)

        ignore_patterns = self.data.exclude or []
        ignore_func = shutil.ignore_patterns(*ignore_patterns)

        for d in data:
            base = d.replace('\\', '/').replace(root, '')

            # For globbing, we have to make sure the destination is up to date
            if root:
                if base.startswith('/'):
                    base = base[1:]
                dest = self.data.destination + '/' + base
            else:
                dest = self.data.destination

            ok = True
            for pattern in ignore_patterns:
                if fnmatch.fnmatch(base, pattern):
                    ok = False
                    break
            if not ok:
                continue

            if os.path.exists(dest) and self.data.force:
                if os.path.isfile(dest):
                    os.unlink(dest)
            shutil.move(d, dest)


class PrintCommand(_BuildCommand):
    """
    Basic print command
    """
    alias = 'PRINT'


    def description(self):
        return 'Simple print command'


    def populate_parser(self, parser):
        """
        We consume all arguments and print that string
        """
        parser.add_argument(
            '-s', '--swap-slash',
            action='store_true',
            help='Before printing, convert all \\ to /'
        )
        parser.add_argument(
            '-q', '--quote',
            action='store_true',
            help='Surround text with spaces in them with quotes'
        )
        parser.add_argument(
            'texts',
            nargs=argparse.REMAINDER,
            help='string to print'
        )


    def run(self, build_file):
        """
        Run the print command
        """
        def _clean(t):
            if self.data.swap_slash:
                t = t.replace('\\', '/')

            if self.data.quote:
                if ' ' in t:
                    t = '"{}"'.format(t)
            return t

        print (' '.join(map(_clean, self.data.texts)))


class CDCommand(_BuildCommand):
    """
    Change the working directory of the script
    """
    alias = 'CD'

    def description(self):
        return 'Change the working directory of our commands. This '\
               'remembers the location it came from to go back and forth.'


    def populate_parser(self, parser):
        """
        Very simple command with a directory to move into
        """
        parser.add_argument(
            '-p', '--pop',
            action='store_true',
            help='Similar to pushd and popd, this will return to '
                 'the previous directory that was current'
        )
        parser.add_argument(
            'directory',
            nargs='?',
            default='{build_dir}',
            help='The directory to move into. '
                 'If no directory is supplied, the '
                 '{build_dir} is selected'
        )


    def run(self, build_file):
        """
        Move this process into another directory
        """
        change_to = self.data.directory

        if self.data.pop:
            if hasattr(build_file, '_previous_directories'):
                if len(build_file._previous_directories):
                    change_to = build_file._previous_directories.pop()

        # -- We have to expand the directory in the event the
        # default it provided
        change_to = build_file.expand(change_to)

        # Push the current directory to the stack
        if not hasattr(build_file, '_previous_directories'):
            build_file._previous_directories = deque()

        if not self.data.pop:
            build_file._previous_directories.append(os.getcwd())

        logging.info('Change Directory: -> {}'.format(change_to))
        os.chdir(change_to)


class SetCommand(_BuildCommand):
    """
    Set a property
    """
    alias = 'SET'

    def description(self):
        return 'Set a property that can be used later'


    def populate_parser(self, parser):
        """
        Simple two slot arguments
        """
        parser.add_argument(
            '-r', '--resolve-path',
            help='Resolve a path to it\'s absolute location'
        )

        parser.add_argument(
            '-g', '--global-var',
            action='store_true',
            help='Set this as a global variable regardless of scope'
        )

        parser.add_argument(
            'value',
            help='The value to pass into the property'
        )
        parser.add_argument(
            'property',
            help='The name of the variable to place the value into'
        )


    def run(self, build_file):
        """
        Set the property...
        """
        value = self.data.value
        if self.data.resolve_path:
            value = os.path.abspath(value)
        build_file.add_attribute(
            self.data.property,
            value,
            global_=self.data.global_var
        )


class EnvCommand(_BuildCommand):
    """
    Use external script (e.g .bat, .sh) to augment the environment of this
    process
    """
    alias = 'ENV'

    def description(self):
        return 'Source a file for to augment the active environment'


    def populate_parser(self, parser):
        """
        """
        parser.add_argument(
            'script_command',
            help='The script to execute'
        )


    def run(self, build_file):
        """
        Execute the script, then read back the environment into our
        active process
        """
        with utils.temp_dir() as tempdir: # For easy cleanup

            logging.info('Sourcing Environment: {}'.format(self.data.script_command))
            env_txt_file = '_setup_environment.txt'

            if platform.system() == 'Windows':
                #
                # Windows uses batch with the set command
                #
                env_file = '_setup_environment.bat'
                with open(env_file, 'w') as env_bat:
                    env_bat.write('@echo off\n')
                    env_bat.write('call %s\n' % self.data.script_command)
                    env_bat.write('set > %s\n' % env_txt_file)
            else:
                #
                # Linux uses bash with the env command
                #
                env_file = '_setup_environment.sh'
                with open(env_file, 'w') as env_sh:
                    env_sh.write('source %s\n' % self.data.script_command)
                    env_sh.write('env > %s\n' % env_txt_file)

                # Make sure bash knows to run it
                env_file = 'bash ./' + env_file

            os.system(env_file)
            with open(env_txt_file, 'r') as env_read:
                lines = env_read.read().splitlines()

            for line in lines:
                var, value = line.split('=', 1)
                os.environ[var] = value


class FailCommand(_BuildCommand):
    """
    Every language needs a throw right?
    """
    alias = 'FAIL'

    def description(self):
        return 'Stop the command process by raising a specific message'


    def populate_parser(self, parser):
        """
        The parser is very simple
        """
        parser.add_argument(
            'text',
            nargs='+',
            help='The text that we want to go along with our build failure'
        )


    def run(self, build_file):
        """
        Runit!
        """
        text = ' '.join(self.data.text)
        raise RuntimeError(text)


class ReturnCommand(_BuildCommand):
    """
    Way to return from a process without having to spin through all commands
    """
    alias = 'RETURN'

    def description(self):
        return 'Return from the current scope (function or set of commands)'


    def populate_parser(self, parser):
        return # Nothing currently


    def run(self, build_file):
        return _BuildCommand.RETURN_COMMAND