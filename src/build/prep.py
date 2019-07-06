"""
Prep work get's a set of commands as well!
"""
from __future__ import absolute_import

from common import log

from .parse import BuildCommandParser
from .buildfile import BuildFile
from .abstract_manager import _AbstractManager

class PrepManager(_AbstractManager):
    """
    Prep!

    This is the area of devops that often gets overlooked for the bigger
    stuff but none-the-less, setting up a build version should be simple
    and fun! If nothing else, it should at least be well documented and
    straight forward.
    """
    type_ = 'prep'

    def __init__(self, app, arguments, build_file, source_dir=None):
        _AbstractManager.__init__(self, app, arguments, build_file, source_dir=source_dir)
        build_file.add_attribute('version', self.version)


    def run_prep(self):
        """
        Do the prep work!
        """
        logging.debug(':Prep Post Tag:')
        with log.log_indent():
            prep_descriptor = self.build_file[self.type_]
            commands = prep_descriptor['commands']
            self.build_commands(None, commands)


    @property
    def version(self):
        return self.arguments.version
