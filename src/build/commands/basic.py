"""
Basic i/o commands for fbuild

NOTE: DON'T sys.exit(1) out of here. We're trying to catch these
errors for better reporting.
"""
from __future__ import print_function, absolute_import

import os
import sys
import shutil
import logging
import argparse

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
        parser.add_argument('-m', '--make-dirs', action='store_true', help='Create the destination directory')
        parser.add_argument('-f', '--force', action='store_true', help='Overwrite any files that already exist')
        parser.add_argument('source', help='The source location')
        parser.add_argument('destination', help='The destination location')

    def run(self, build_file):
        """
        Copy files in a platform agnostic way
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

        logging.info('Copying: {} -> {}'.format(self.data.source, self.data.destination))
        if os.path.isdir(self.data.source):
            shutil.copytree(self.data.source, self.data.destination)
        else:
            shutil.copy2(self.data.source, self.data.destination)


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
        shutil.move(self.data.source, self.data.destination)


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


class WriteCommand(_BuildCommand):
    """
    Write text to a file
    """
    alias = 'WRITE'

    def description(self):
        return 'Write data to a file'


    def populate_parser(self, parser):
        """
        We need the text to commit as well as the file we're outputing
        it to.
        """
        parser.add_argument(
            '-a', '--append',
            action='store_true',
            help='Should we just append to the file. (Defaults to overwrite)'
        )
        parser.add_argument(
            'content',
            help='The content to store within out file'
        )
        parser.add_argument(
            'file',
            help='The to write our information to'
        )


    def run(self, build_file):
        """
        Run the write command (but not the wrong one bum-dum-chhh)
        """
        open_type = 'a' if self.data.append else 'w'
        if not os.path.isfile(self.data.file):
            open_type = 'w' # Nothing to append to

        logging.info('Writing to file: {}'.format(self.data.file))

        try:
            with open(self.data.file, open_type) as f:
                f.write(self.data.content)
        except OSError as e:
            raise RuntimeError("Could not open file: {} - {}".format(
                self.data.file, str(e)
            ))
