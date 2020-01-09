"""
Basic buid manager
"""
from __future__ import absolute_import

import os
import sys
import glob
import shutil
import fnmatch
import traceback
import platform
import logging
import json

from build import manage
from build.parse import BuildCommandParser
from common.constants import *
from common import log
from common.platformdict import PlatformDict

class BasicBuilder(manage.BuildManager):
    """
    Basic operations (no real build management, just organization)

    Settings:
        The 'basic' build type has the following controls as it's disposal:

        - prefix_dir : str - director(y/ies) to push our built product into (e.g. foo, foo/bar)
        - use_gitignore : bool - When moving files over, should we look for a .gitignore for
                          ignore patterns?
        - exclude : 

    """
    alias = 'basic'


    def _do_copy(self, src, dst, ignore, original_filename, per_file_ignore):
        """
        Run a copy operation - should probably migrate this to commands.py
        """
        d = os.path.dirname(dst)
        if not os.path.exists(d):
            os.makedirs(d)

        if os.path.isfile(src):

            # Files are handled one-at-a-time
            ok = True
            for pattern in per_file_ignore:
                if fnmatch.fnmatch(original_filename, pattern):
                    ok = False
                    break
            if not ok:
                return

            shutil.copy2(src, dst)

        elif os.path.isdir(src):
            shutil.copytree(src, dst, symlinks=True, ignore=ignore)


    def build(self):
        """
        Time to build...
        """
        bf_build = self.build_file['build'] # type: PlatformDict

        #
        # Where are we putting this item?
        #
        build_path = self.build_dir

        logging.info('Build Path: {}'.format(build_path))

        #
        # At this point, we check for abstract commands and,
        # if we have them, we choose them over our default
        # commands
        #
        if bf_build['commands']:
            #
            # Abstract commands that should execute the build as needed 
            #
            logging.info('Executing Build Commands...')
            with log.log_indent():
                parser = BuildCommandParser(
                    bf_build['commands'], self.build_file, self.additional
                )
                try:
                    parser.exec_()
                except Exception as e:
                    logging.critical('Encountered a critical failure!')
                    with log.log_indent():
                        list(map(logging.critical, traceback.format_exc().split('\n')))
                    sys.exit(1)

            build_root = build_path

        else:
            #
            # This is a generic build - just copy files
            # and let python do it's thing
            #
            save_files = bf_build['save_between_builds'] or []
            save_files = [self.build_file.expand(s) for s in save_files]

            if os.path.exists(build_path):
                logging.info('Clear old data...')

                # for p in os.listdir(build_path):
                to_clean = glob.glob(build_path + '/*')

                for fpath in to_clean:
                    fpath = fpath.replace('\\', '/')
                    if any(fnmatch.fnmatch(fpath, n) for n in save_files):
                        continue

                    if os.path.isdir(fpath):
                        shutil.rmtree(fpath)
                    else:
                        os.unlink(fpath)

            build_root = build_path

            #
            # Additional directories that we want place our source
            # files into within our build directory
            #
            if bf_build['prefix_dir']:
                prefix = self.build_file.expand(bf_build['prefix_dir'])
                logging.debug('Prefix Dir: {}'.format(prefix))
                build_path = os.path.join(build_path, prefix)

            if not os.path.exists(build_path):
                logging.info('Create Build Directory...')
                os.makedirs(build_path)

            #
            # Ignoring select files/directories based on the settings
            # of both the build yaml and possible the git repo
            #
            ignore_patterns = ['.git', '.gitignore', 'build.yaml']
            if bf_build['use_gitignore'] is not False:
                gitignore = os.path.join(self.source_dir, '.gitignore')
                if os.path.exists(gitignore):
                    with open(gitignore, 'r') as gi:
                        for l in gi:
                            ignore_patterns.append(l.strip())

            if bf_build['exclude']:
                ignore_patterns.extend([self.build_file.expand(v) for v in list(bf_build['exclude'])])

            logging.debug('Excluding: [{}]'.format(', '.join(ignore_patterns)))
            ignore = shutil.ignore_patterns(*ignore_patterns)

            per_file_ignore = []
            files = bf_build['files']

            if not files:
                files = os.listdir(self.source_dir)
                per_file_ignore = ignore_patterns

                def _pf_ifnore(filename):
                    for pattern in per_file_ignore:
                        if fnmatch.fnmatch(filename, pattern):
                            return False
                    return True
                files = filter(_pf_ifnore, files)

            else:
                files = [self.build_file.expand(v) for v in list(files)]

            logging.info('Copying Files...')
            with log.log_indent():
                for relative_file in files:
                    logging.debug('- {}'.format(relative_file))
                    source_path = os.path.join(self.source_dir, relative_file)
                    destination = os.path.join(build_path, relative_file)
                    self._do_copy(source_path, destination, ignore, relative_file, per_file_ignore)

        #
        # The launch.json file is used for understanding package requirements
        # and building environments.
        #
        self.create_launch_json(build_root)

manage.BuildManager.register(BasicBuilder)
