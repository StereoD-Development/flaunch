"""
Atom interface layer for working with packages.
"""
from __future__ import absolute_import

import os
import time
import json
import platform
import getpass
import logging
import base64
import sys

try:
    import requests
except ImportError as e:
    print ("Python package 'requests' is required!")
    raise

from . import log
from . import utils

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
        return os.path.abspath(os.path.join(os.path.dirname(storage_path), 'flaunch_prefs2.json'))

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

        if os.environ.get("FLAUNCH_CUSTOM_INDEX"):
            if self._test_connection(os.environ["FLAUNCH_CUSTOM_INDEX"]):
                return os.environ["FLAUNCH_CUSTOM_INDEX"]

        elif self._settings.get(self.LAST_KNOWN, None):
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


    def get_credentials(self, first_time):
        """
        Get the user credientials for the active user
        :return: tuple(username, password, bool - if the user entered in creds)
        """
        username = None
        pw = None

        if first_time:

            if 'username' in self._settings:
                username = self._settings['username']

            # Some level of obfuscation
            if 'session' in self._settings:
                pw = base64.urlsafe_b64decode(self._settings['session'].encode('utf-8')).decode('utf-8')

            if 'timestamp' in self._settings:
                current_time = time.time()
                delta = current_time - self._settings['timestamp']
                delta_days = delta // 86400
                if delta_days > 7:
                    # Once a week we have the user login
                    pw = None

        if username and pw:
            return username, pw, False

        else:
            if utils.PY3:
                inp = input
            else:
                inp = raw_input

            if username:
                entered_usename = inp('Username (leave blank to use {}):'.format(username))
            else:
                entered_usename = inp('Username:')

            if entered_usename != '':
                username = entered_usename

            pw = getpass.getpass()

        return username, pw, True


    def store_credentials(self, username, password):
        """
        Store the credentials in a basic spot for now - probably need some kind of
        cookie control
        """
        self._save_setting('username', username)
        self._save_setting('session', base64.urlsafe_b64encode(
            password.encode('utf-8')).decode('utf-8')
        )
        self._save_setting('timestamp', time.time())


def _default_headers():
    return {
        'Accept' : 'application/json',
        'X-Flux-Facility' : FLUX_FACILITY,
        'user-agent' : '{} flaunch/1.0.0'.format(platform.system())    
    }


def _get(endpoint, **params):
    """
    Run a basic request
    """
    manager = ConnectionManager()

    return requests.get(
        manager.url + '/rest/latest' + endpoint,
        params=params,
        headers = _default_headers()
    )


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
        logging.error(data['error'])
        return None
    return data


def get_package_info(package, version=None):
    """
    Request the package descriptor
    :return: dict|None 
    """
    vs = ' (' + str(version) + ')'
    logging.debug("Getting: " + package + "{}".format(vs if version else ''))

    extras = {}
    if version:
        extras['version'] = version

    result = _get(
        '/core/package/{}/{}'.format(package, FLUX_FACILITY),
        **extras
    )

    data = result.json()
    if 'error' in data:
        logging.error('Cannot locate package: \"{}\" for your facility: {}'.format(
            package,
            FLUX_FACILITY
        ))
        logging.debug('Reason:')
        with log.log_indent():
            logging.debug(data['error'])

        find_similar_pacakges(package) # Will try to find what the user meant
        return None

    return data


def register_package(package, version, method='get', launch_data=None, force=False, pre_release=False):
    """
    Registering a package requires a propper login with Atom
    """
    manager = ConnectionManager()

    if not hasattr(manager, 'client'):

        manager.client = requests.session()
        login_url = manager.url + '/accounts/login/'

        first_time = True
        try:
            while True:
                username, password, manual = manager.get_credentials(first_time)
                res_one = manager.client.get(login_url) # Set Cookie
                csrftoken = manager.client.cookies['csrftoken']
                first_time = False

                login_data = dict(
                    username=username,
                    password=password,
                    csrfmiddlewaretoken=csrftoken,
                    next='/rest/latest/core/heartbeat'
                )
                manager._login_response = manager.client.post(login_url,
                                                              data=login_data,
                                                              cookies=res_one.cookies)

                if manager._login_response.status_code not in [200, 302]:
                    logging.info('Invalid credientials! Try again')
                    continue
                elif manual:
                    manager.store_credentials(username, password)
                break

        except KeyboardInterrupt as e:
            logging.info("Breaking out of package registration.")
            return None

    kwargs = {}
    if method == 'get':
        kwargs['params'] = {
            'package' : package,
            'version' : version,
            'force'   : force,
            'prerelease' : pre_release
        }

    elif method == 'post':
        kwargs['json'] = {
            'package' : package,
            'version' : version,
            'force'   : force,
            'prerelease' : pre_release
        }

        if launch_data is not None:
            kwargs['json']['launch_data'] = launch_data

    result = getattr(manager.client, method)(
        manager.url + '/rest/latest/core/package/register',
        headers=_default_headers(),
        cookies=manager._login_response.cookies,
        **kwargs
    )

    if result.status_code != 200:
        logging.error('Could not register package: {}'.format(package))
        logging.error('Result invalid from Atom')
        return None

    else:
        data = result.json()
        if 'error' in data:
            logging.error(data['error'])
            return None

        return data


def get_packges(**params):
    """
    Simple function to gather all packages. This doesn't have
    any repository data - just name, version, and possible launch_data
    :param params: Additional search parameters for the package
        - name: string fnmatch name to search on
        - id: int id of a package to search
    """
    result = _get('/core/package/get/all', **params)

    try:
        result.raise_for_status()
    except:
        logging.critical('flaunch package not defined in your repository!')
        return []

    data = result.json()
    if isinstance(data, dict) and 'error' in data:
        logging.error('Error getting packages:')
        with log.log_indent():
            logging.error(data['error'])
        return []

    return data


def find_similar_pacakges(package_name):
    """
    Based on the available packages, let's try finding similarly named
    packages to give the user an idea of what they might need
    :param package_name: The package that was entered
    :return: None
    """
    diffs = []

    all_pacakges = get_packges()
    for package in all_pacakges:
        diff = utils.levenshtein(package_name.lower(), package['package'].lower())
        diffs.append((diff, package['package']))

    diffs.sort(key=lambda x: x[0])

    if diffs:
        with log.log_indent():
            logging.info("Did you mean: {} ?".format(diffs[0][1]))
