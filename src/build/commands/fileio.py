
from __future__ import print_function, absolute_import

import os
import sys
import glob
import shutil
import logging
import argparse
from collections import deque

from build.command import _BuildCommand


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


class ReadCommand(_BuildCommand):
    """
    The other side of the WRITE command. Push information into a property
    that can be injected into other variables later
    """
    alias = 'READ'

    def description(self):
        return 'Read data from a file - Careful! This is not built for large files'


    def populate_parser(self, parser):
        """
        We require a file to read and the property to inject the read
        information into
        """
        parser.add_argument(
            '-b', '--read-bytes',
            help='Open the file as a bytes object'
        )
        parser.add_argument(
            'file',
            help='The file that we want to read from'
        )
        parser.add_argument(
            'property',
            help='The property name to store the new information into'
        )


    def run(self, build_file):
        """
        Read our file!
        """
        read_type = 'rb' if self.data.read_bytes else 'r'

        logging.info('Reading file: {} -> PROPERTY({})'.format(
            self.data.file, self.data.property
        ))

        d = None
        try:
            with open(self.data.file, read_type) as f:
                d = f.read()
        except OSError as e:
            raise RuntimeError("Could not read file: {} - {}".format(
                self.data.file, str(e)
            ))

        build_file.add_attribute(self.data.property, d)


class MkDirCommand(_BuildCommand):
    """
    Creating directories in a platform agnostic way
    """
    alias = 'MKDIR'

    def description(self):
        return 'Create directories where required'


    def populate_parser(self, parser):
        """
        Just a few arguments to suppliment creating directories
        """
        parser.add_argument(
            '-s', '--skip-exist',
            action='store_true',
            help='Continue if the directory already exists'
        )
        parser.add_argument(
            'path',
            help='The directory(ies) to create. Recursive by default'
        )


    def run(self, build_file):
        """
        Make some dirs!
        """
        if os.path.isdir(self.data.path):
            if not self.data.skip_exist:
                raise RuntimeError(
                    ('Directory already exists! {} ' \
                    '(Consider passing --skip-exist to ignore)') \
                    .format(self.data.path)
                )
            return # All done

        # If we've made it here, we have something to make
        os.makedirs(self.data.path)


class DelCommand(_BuildCommand):
    """
    File deletion command
    """
    alias = 'DEL'

    def description(self):
        return 'Delete files/folders'


    def populate_parser(self, parser):
        """
        Pretty simple
        """
        parser.add_argument(
            'path',
            help='Files to remove (accepts * patterns)'
        )


    def run(self, build_file):
        """
        Time to run!
        """

        to_remove = glob.glob(self.data.path)

        for rem in to_remove:
            if not os.path.exists(rem):
                continue

            if os.path.isdir(rem):
                shutil.rmtree(rem)
            else:
                os.unlink(rem)
