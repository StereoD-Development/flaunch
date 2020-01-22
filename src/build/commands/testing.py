"""
Testing utilities for various languages
"""
from __future__ import print_function, absolute_import

import os
import logging

from common import utils
from build.command import _BuildCommand

from types import ModuleType
def _execute_into_module(command, name, locals):
    compiled = compile(command, '', 'exec')
    module = ModuleType(name)
    exec(compiled, module.__dict__)
    return module

class PyCoverageCommand(_BuildCommand):
    """
    Use the coverage module to run coverage on a given path
    """
    alias = 'COVER'

    def description(self):
        return 'Use the coverage.py module to run coverage on a given set ' \
               'of code (python only)'


    def populate_parser(self, parser):
        """
        The PyCoverage does quite a bit
        """
        parser.add_argument('script', help='File to run the coverage on')
        parser.add_argument('callable', help='Attribute to call from our source file that will execute the covered code.')
        parser.add_argument('--arg', action='append', help='Argument we pass to our callable')

        parser.add_argument('--html', action='store_true', help='Generate html output')


    def run(self, build_file):
        """
        Execute a given test environment
        """
        import coverage

        try:
            cov = coverage.Coverage() # API changed over time
        except:
            cov = coverage.coverage()

        cov.start()

        mod = utils.load_from_source(self.data.script)
        if not hasattr(mod, self.data.callable) or not callable(getattr(mod, self.data.callable)):
            raise RuntimeError('The coverage script provided has no callable attribute {}'.format
                (self.data.callable)
            )

        logging.info('Running Coverage: {}.{}'.format(
            os.path.basename(self.data.script), self.data.callable)
        )

        # Fire up the code!
        getattr(mod, self.data.callable)(*self.data.arg)

        cov.stop()

        if self.data.html:
            cov.html_report(directory='htmlcov')
