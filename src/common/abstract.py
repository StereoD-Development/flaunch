"""
Utilities for handling platforms and expanding variables
based on environment.
"""
import re
import os
import sys
import logging

from .platformdict import PlatformDict

class FLaunchDataError(Exception):
    """ Error related to booting up a flaunch data """
    pass


class _AbstractFLaunchData(object):
    """
    Abstract class that handles the expansion of values based
    on various input.
    """
    SEARCH_REGEX = re.compile(r"\{+[^\{]+\}")

    def __init__(self, package, path, data):
        self._package = package
        self._path = path
        self._data = data


    def __repr__(self):
        return "<({}, {})>".format(self.__class__.__name__, self._package)


    def __getitem__(self, key):
        if key not in self._data:
            return None
        return self._data[key]


    @property
    def path(self):
        return os.path.abspath(os.path.dirname(self._path))


    @property
    def platform(self):
        return platform.system()


    @property
    def package(self):
        return self._package


    def attributes(self):
        return {}


    def expand(self, value, env=None, key=None):
        """
        Resolve a value as much as needed
        :param value: The value possibly containing attributes to
        be resolved.
        :param env: The environment we're overhauling - this will
        augment if key is a valid string
        :param key: The environment variable that will be set
        """
        if env is None:
            env = self.attributes()
            # Environ Variables take precedent
            env.update(os.environ)

        should_append = False
        if isinstance(value, list):
            """
            We attempt to build the strings one by one
            """
            should_append = True
            total = []
            for item in value:
                total.append(self.expand(item, env))
            value = total

        else:

            found_to_resolve = _AbstractFLaunchData.SEARCH_REGEX.findall(value)
            for needs_resolve in found_to_resolve:
                variable = needs_resolve[1:-1]

                if hasattr(self, variable):
                    # For things like path, platform, etc.
                    value = value.replace(needs_resolve, getattr(self, variable))

                elif variable.upper() in env:
                    value = value.replace(needs_resolve, env[variable.upper()])

        if key is not None:
            if should_append:
                #
                # We want to push multiple items in
                #
                if key in env:
                    env[key.upper()] += os.pathsep + os.pathsep.join(value)
                else:
                    env[key.upper()] = os.pathsep.join(value)
            else:
                env[key.upper()] = value

            with log.log_indent():
                logging.debug('Set: {}={}'.format(key.upper(), env[key.upper()]))

        return value
