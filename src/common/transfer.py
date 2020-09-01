"""
Deployment utilities for transfering deployed packages 


Example transfer JSON:
{
   "source": "tor|mad|pun",
   "target": "tor|mad|pun",
   "paths": ["path1", "path2"],
   "priority": <int>,
   "notify-url": "<url>",
   "notify-payload": {"foo"}
}
The paths should be native Linux paths.

`priority`, `notify-url` and `notify-payload` are optional.
`notify-payload` is an opaque JSON blob that will be simply passed to the `notify-url` as a payload.
Pop in any identifying markers you need.
"""
from __future__ import absolute_import

import os
import time
import sys
import copy
import logging
import requests
import platform
import threading

from . import log
from .communicate import FLUX_FACILITY, get_facilities, default_headers
from .service import _HandlerBase, new_server
from .constants import TRANSFER_PORT

# Need a way to augment this...
TRANSFER_ENDPOINT = 'http://10.1.60.54:8002/latest/transfer'

WAIT_TIMEOUT = (60.0 * 5.0) # Five minute max
SLEEP_TIME = 0.5 # In seconds

class TransferHandler(_HandlerBase):
    """
    Handler to wait for transfer information to be returned
    """
    def do_POST(self):
        """
        When we get back from our transfer agents with information,
        we need to know what to do and how to do it.
        """

        # TODO: Get this working a bit better
        data = self.get_post_data()
        with self.server.transfer_lock:
            logging.debug('-- Transfer Status Returned --')
            with log.log_indent():
                loggine.debug(__import__('pprint').pformat(data).split('\n'))
            self.server.transfer_to.remove(data['payload']['destination'])


def transfer_package(
    build_file,
    package_file,
    destinations=None,
    exclude=None,
    platforms=None,
    wait=True
    ):
    """
    Transfer a package to other facilities so they might use it.
    :param build_file: BuildFile instance for this package
    :param destinations: list[str] of facilities to transfer to (default is all others)
    :param exclude: list[str] of facilities to ignore (default is none)
    :param platforms: list[str] of python platform.system() to transfer (default is current)
    :param wait: Should we wait for the transfer to complete?
    :return: bool - if everything went as planned 
    """
    server = new_server(TransferHandler, port=TRANSFER_PORT)

    # -- Switch setup for the server thread to alert our main thread when it's alright
    # to continue

    # Lock that we maintain above for accessing the transfer_to list
    server.transfer_lock = threading.Lock()

    # List that can be accessed by the handler instances above
    server.transfer_to = set()

    # Result data from our transfer to make it easy to handle the 
    server.transfer_resuls = {}

    exclude = exclude or []
    facilities = get_facilities()
    source = None

    for info in facilities:
        if info['Facility.Alias'] == FLUX_FACILITY:
            source = info['Facility.Code']

    if source is None:
        raise RuntimeError('Cannot determine source facility!')

    if not destinations:
        destinations = [f['Facility.Code'] for f in facilities if f['Facility.Code'] != source]

    #
    # The transfer service for the time being is Linux paths only
    # which means we need to convert that data however we can.
    #
    with build_file.platform_override('linux'):
        deploy_folder = build_file.expand(
            build_file['props']['flaunch_repo']
        )

    with server:
        # We need the path for each platform, for now we'll lock this
        # in to make sure it's all straight forward
        paths = []
        for pf in platforms or [platform.system()]:
            paths.append('/'.join([deploy_folder, pf, package_file]))

        for facility in destinations:
            if facility in exclude:
                continue

            if facility == source:
                continue

            #
            # Add the destination to our transfer_to listing
            #
            with server.transfer_lock:
                server.transfer_to.add(facility)

            transfer_info = {
                'source' : source,
                'target' : facility,
                'paths' : paths
            }

            if wait:
                transfer_info.update({
                    'notify-url' : server.http_address,
                    'notify-payload' : {
                        'destination' : facility
                    }
                })

            logging.info('Initialize Transfer: {} -> {}'.format(source, facility))
            print("Transfer info", transfer_info)
            result = requests.post(
                TRANSFER_ENDPOINT,
                json=transfer_info,
                headers=default_headers(),
                timeout=5
            )

            try:
                result.raise_for_status()
            except Exception as e:
                logging.critical('Deployment failure!')
                raise

        if wait:
            logging.info('Awaiting transfer response...')

            # -- Now that everything is submitted, we just need to
            # wait until everything has come back one way or another.
            wait_time = WAIT_TIMEOUT
            while wait_time > 0:
                with server.transfer_lock:
                    print("transfer to", server.transfer_to)
                    if len(server.transfer_to) == 0:
                        break

                # Not don't yet, give ourselves a half second
                time.sleep(SLEEP_TIME)
                wait_time -= SLEEP_TIME

            if wait_time <= 0:
                logging.warning('Transfer took longer than expected...')
                return False

    return True
