"""
Atom interface layer for working with packages.
"""

import os
import json
import platform
import logging
import sys

try:
    import requests
except ImportError as e:
    print ("Python package 'requests' is required!")
    raise

from . import log
from . import utils

ATOM_ENDPOINT = 'http://192.168.56.120:8000'
ATOM_REST_URL = ATOM_ENDPOINT + '/rest/latest'
FLUX_FACILITY = os.environ.get('FLUX_FACILITY', 'Madrid')


class ConnectionManager(object):
    """
    Minor tool for handling endpoint lookup and lock-in for future
    instances of flaunch
    """

    LAST_KNOWN = 'last_known_instance'

    def __new__(cls, *args, **kwargs):
        # Singleton pattern
        if not hasattr(cls, '_instance'):
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance


    def __init__(self):
        if not hasattr(self, '_settings'):
            self._settings = self._build_settings()
        if not hasattr(self, '_endpoint'):
            self._endpoint = self._start_connection()


    @property
    def url(self):
        return self._endpoint


    def _settings_file(self):
        storage_path = utils.local_path(None, None, base_only=True)
        return os.path.abspath(os.path.join(os.path.dirname(storage_path), 'flaunch_prefs.json'))

    def _build_settings(self):
        """
        Basic json storage for passed settings used
        """
        storage_path = utils.local_path(None, None, base_only=True)
        filepath = self._settings_file()
        if os.path.isfile(filepath):
            with open(filepath, 'r') as f:
                try:
                    return json.load(f)
                except Exception as e:
                    logging.debug('Could not load settings for connection manager: {}'\
                                  .format(str(e)))
                    pass
        return {}


    def _save_setting(self, setting, value):
        """
        Save a setting for use later
        """
        self._settings[setting] = value
        filepath = self._settings_file()
        try:
            with open(filepath, 'w') as f:
                json.dump(self._settings, f)
        except Exception as e:
            logging.debug('Could not save settings for connection manager: {}'\
                          .format(str(e)))
            pass

    def _endpoints(self):
        """
        Get the list of endpoints that we test against.
        """
        endpoint_path = os.path.join(os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        ),  'endpoints.txt')

        endpoints = []
        if os.path.isfile(endpoint_path):
            with open(endpoint_path, 'r') as f:
                for l in f:
                    endpoints.append(l)
        return endpoints


    def _test_connection(self, endpoint):
        """
        Connection test
        :param endpoint: str of the url to lookup
        """
        try:
            result = requests.head(
                endpoint + '/rest/latest/core/heartbeat', timeout = 2
            )
            result.raise_for_status()
            return True
        except:
            return False


    def _start_connection(self):
        """
        Time to find our atom instance!
        """
        if self._settings.get(self.LAST_KNOWN, None):
            # -- Test this one
            if self._test_connection(self._settings[self.LAST_KNOWN]):
                return self._settings[self.LAST_KNOWN]

        for endpoint in self._endpoints():
            endpoint = endpoint.strip()
            if self._test_connection(endpoint):
                # We've found a viable connection
                self._save_setting(self.LAST_KNOWN, endpoint)
                return endpoint

        # -- If we've made it here, none of the endpoints have
        # panned out. That's no good. Need to fail
        logging.critical('Cannot connect to a repository!')
        sys.exit(1)

def _get(endpoint, **params):
    """
    Run a basic request
    """
    manager = ConnectionManager()

    return requests.get(
        manager.url + '/rest/latest' + endpoint,
        params=params,
        headers = {
            'Accept' : 'application/json',
            'X-Flux-Facility' : FLUX_FACILITY,
            'user-agent' : '{} flaunch/1.0.0'.format(platform.system())
        })


def download_file(url, dest):
    """
    Download a file
    """
    # HACK from an old bug
    url = url.replace(
        "http://backend/servermedia", ConnectionManager().url + "/repo"
    );

    logging.info("Download: " + url)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    # f.flush()


def get_flaunch_info():
    """
    Specific call for handling updating the flaunch toolkit. This is vital
    because we have to be able to update the suite without harming any
    other parts of the toolchain - this could get interesting
    :return: dict
    """
    result = _get('/core/package/flaunch/{}'.format(FLUX_FACILITY))

    try:
        result.raise_for_status()
    except:
        logging.critical('FLaunch package not defined in your repository!')
        sys.exit(1)

    data = result.json()
    if 'error' in data:
        logging.error('Cannot locate flaunch package on your facility: {}'.format(
            FLUX_FACILITY
        ))
        return None
    return data


def get_package_info(package, version=None):
    """
    Request the package descriptor
    :return: dict|None 
    """
    vs = ' (' + str(version) + ')'
    logging.info("Getting: " + package + "{}".format(vs if version else ''))

    extras = {}
    if version:
        extras['version'] = version

    result = _get(
        '/core/package/{}/{}'.format(package, FLUX_FACILITY),
        **extras
    )

    data = result.json()
    if 'error' in data:
        logging.error('Cannot locate package: {} for your facility: {}'.format(
            package,
            FLUX_FACILITY
        ))
        logging.error('Reason:')
        with log.log_indent():
            logging.error(data['error'])
        return None
    return data
