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
from collections import deque

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

        if len(data) > 1 and not os.path.exists(self.data.destination):
            os.makedirs(self.data.destination)

        ignore_patterns = self.data.exclude or []
        ignore_func = shutil.ignore_patterns(*ignore_patterns)

        for d in data:
            base = d.replace('\\', '/').replace(root, '')
            if base.startswith('/'):
                base = base[1:]
            dest = self.data.destination + '/' + base

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

        if not self.data.force and os.path.exists(self.data.destination):
            raise RuntimeError(
                'Destination Already Exists: {} (Consider using the --force flag)' \
                .format(self.data.destination)
            )

        logging.info('Moving: {} -> {}'.format(self.data.source, self.data.destination))

        # FIXME: This needs an upgrade like COPY got for glob
        for d in glob.glob(self.data.source):
            shutil.move(d, self.data.destination)


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
        build_file.add_attribute(self.data.property, self.data.value)
