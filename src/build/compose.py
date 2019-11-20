"""
Package composer utilities
"""
import logging

from common import log
from common import communicate

class Composer(object):
    """
    Basic object for building composed packages
    """

    def __init__(self, args):
        self._package = args.name
        self._version = args.version

        self._packages = args.package or []
        self._launch   = args.launch
        self._force    = args.force_update
        self._run      = args.run
        self._args     = args.arg
        self._env      = args.env
        self._pre      = args.pre_release


    def _build_launch_json(self):
        """
        Construct the launch.json dictionary that can be written to disk
        """
        launch = {}

        if self._launch:
            if self._run:
                launch['executable'] = self._launch
            else:
                launch['extends'] = self._launch

        if self._packages:
            for p in self._packages:
                launch.setdefault('requires', []).extend(p.split(':'))

        if self._args:
            launch['default_args'] = self._args

        if self._env:
            launch.setdefault('env', {})
            for env_detail in self._env:
                var, val = env_detail.split('=')
                launch['env'][var] = val

        return launch


    def exec_(self):
        """
        Communicate with Atom and register this launcher
        """

        launch_data = self._build_launch_json()
        logging.debug('Composed launch.json:')
        with log.log_indent():
            list(map(logging.debug,
                     __import__('pprint').pformat(launch_data).split('\n')))

        logging.debug('Registering composed launch data...')
        result = communicate.register_package(
            self._package,
            self._version,
            method='post', # This makes it right away because it's just a foe-launcher
            launch_data=launch_data,
            force=self._force,
            pre_release=self._pre
        )

        if result:
            logging.info("Registered!")
