"""
Utilities for handling platforms and expanding variables
based on environment.
"""
from __future__ import absolute_import

import re
import os
import sys
import copy
import shlex
import logging
from contextlib import contextmanager

from .platformdict import PlatformDict
from . import log

class FLaunchDataError(Exception):
    """ Error related to booting up a flaunch data """
    pass


class _AbstractFLaunchData(object):
    """
    Abstract class that handles the expansion of values based
    on various input.
    """
    SEARCH_REGEX = re.compile(r"\{+[^\{|\s]+\}")

    def __init__(self, package, path, data):
        """
        :param package: The name of the pacakge we're working with
        :param path: The path to this data repo
        :param data: PlatformDict that holds onto our data
        """
        self._package = package
        self._path = path.replace('\\', '/')
        self._data = data


    def __repr__(self):
        return "<({}, {})>".format(self.__class__.__name__, self._package)


    def __getitem__(self, key):
        if key not in self._data:
            return None
        return self._data[key]


    @contextmanager
    def overload(self, properties):
        """
        Context manager to handle a temporary overload of our class.
        :param properties: dict of property information we want to overload
        our current props with.
        """
        self._original_data = self._data
        self._data = copy.deepcopy(self._data) # Could use a delta-aware dict
        if not self._data['props']:
            self._data['props'] = {}
        self._data['props'].update(properties)
        yield
        self._data = self._original_data


    @property
    def path(self):
        """
        :return: The directory to this file (str)
        """
        return os.path.abspath(os.path.dirname(self._path))


    @property
    def platform(self):
        """
        The python platform we're working with
        :return: str
        """
        return platform.system()


    @property
    def package(self):
        """
        The name of the package that this file represents
        :return: str
        """
        return self._package


    @property
    def flaunch_data_path(self):
        """
        The full path to this file
        :return: str
        """
        return self._path


    def attributes(self):
        """
        :return: PlatformDict
        """
        return PlatformDict()


    def expand(self, value, env=None, key=None, found=None, rtype=str):
        """
        Resolve a value as much as needed using the environment provided. The
        environment isn't is the os.environ but a mapping to any number of attributes
        built via the launch data.

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
        breakout = False

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
            if value is None:
                logging.error('Cannot expand null value!')
                return value

            found_to_resolve = _AbstractFLaunchData.SEARCH_REGEX.findall(value)

            for needs_resolve in found_to_resolve:
                variable = needs_resolve[1:-1]

                if variable.endswith('...'):
                    if not rtype is list:
                        logging.error('... syntax only allowed for parsed commands.')
                        sys.exit(1) # ??
                    breakout = True
                    variable = variable[:-3]

                if ':' in variable:
                    #
                    # We have a dictionary lookup
                    # This only applies to the environment in the event that
                    # attributes have been supplied
                    #
                    keys = variable.split(':')
                    end_value = env[keys[0]]
                    for k in keys[1:]:
                        if not isinstance(end_value, (dict, PlatformDict)):
                            logging.error(
                                'Bad dictionary variable expansion for value: {}' \
                                .format(variable)
                            )
                            sys.exit(1) # ??
                        end_value = end_value[k]

                    from common.utils import string_types
                    if not isinstance(end_value, string_types):
                        logging.error(
                            'Bad value for dictionary variable expansion: {}' \
                            .format(variable)
                        )

                    value = value.replace(needs_resolve, end_value)

                elif hasattr(self, variable):
                    # For things like path, platform, etc.
                    value = value.replace(needs_resolve, getattr(self, variable))

                elif variable.upper() in env:
                    # We check on the uppercase first to make sure environment
                    # variables get first pick, as opposed to lowercase props:
                    value = value.replace(needs_resolve, env[variable.upper()])

                elif variable in env:
                    value = value.replace(needs_resolve, env[variable])

        if found is None:
            found = set()

        def _continual_expansion(val):
            #
            # Recursive expansion!
            #
            still_to_resolve = _AbstractFLaunchData.SEARCH_REGEX.findall(val)
            unknown = set()

            for sub_val in still_to_resolve:
                if sub_val in found:
                    if sub_val[1:-1] not in env:
                        logging.warning('Unknown property: {}'.format(sub_val))
                        unknown.add(sub_val)
                        continue

                    logging.critical('Potential cyclic variable expansion detected!')
                    with log.log_indent():
                        logging.critical('Attempted to expand: "{}"'.format(val))
                    sys.exit(1)
                found.add(sub_val)

            for uk_val in unknown:
                still_to_resolve.remove(uk_val)

            if still_to_resolve:
                return self.expand(val, env, found=found)
            return val

        if isinstance(value, list):
            resolved = []
            for v in value:
                resolved.append(_continual_expansion(v))
            value = resolved
        else:
            value = _continual_expansion(value)


        if key is not None:
            if should_append:
                #
                # We want to push multiple items in
                #
                if key.upper() in env:
                    env[key.upper()] += os.pathsep + os.pathsep.join(value)
                else:
                    env[key.upper()] = os.pathsep.join(value)
            else:
                env[key.upper()] = value

            with log.log_indent():
                logging.debug('Set: {}={}'.format(key.upper(), env[key.upper()]))

        if breakout:
            return shlex.split(value)

        if rtype is list:
            return [value]

        return value
