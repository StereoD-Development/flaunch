"""
Tools for grabbing packages from our repo and working out the environment
for a list of packages
"""
from __future__ import absolute_import

import os
import sys
import json
import shutil
import logging
import zipfile

from common import log
from common import utils
from common import ljson
from common import communicate

if utils.PY3:
    import urllib.parse
    unquote = urllib.parse.unquote
else:
    import urllib
    unquote = urllib.unquote

def _download(info, dest, filename):
    """
    Download a package and install it to dest
    """
    if not os.path.exists(dest):
        os.makedirs(dest)
    arch_path = os.path.join(dest, filename)

    if info['type'] == 'server':
        communicate.download_file(info['uri'], arch_path)
    elif info['type'] == 'file':

        path = unquote(info['uri']).replace('file:///', '', 1)
        if not os.path.exists(path):
            attempt = '/' + path
            if not os.path.exists(attempt):
                logging.critical(
                    ('Cannot download {} - Possible unknown '
                     'version or missing files!').format(path)
                )
                sys.exit(1)
            path = attempt

        logging.debug("Copy: " + path)
        logging.debug("To: " + arch_path)
        shutil.copy2(path, arch_path)


def _extract(zipfile_path):
    """
    Unzip a file
    :param zipfile_path: The path to a .zip file that we're unloading
    :return: None
    """
    from common import compression
    compression.unzip_files(zipfile_path, output=os.path.dirname(zipfile_path))



def _get_package_and_version(package):
    """
    Split a package and it's version (if a version is provided)

    :param package: The full package string
    :return: tuple(str, str) -> (pacakge, version)

    - examples

        PyFlux -> (PyFlux, None)
        PyFlux/1.1.0 -> (PyFlux, 1.1.0)
        PyFlux/dev -> (PyFlux, dev)
    """
    version = None
    if '/' in package:
        package, version = package.split('/')
    return (package, version)


def _get_package(package, version=None, info=None, builds=[], force=False):
    """
    Get a particular package
    :param package: The name of the package as atom knows it (case insenitive)
    :param version: The version of the package that we're looking for (None for highest)
    :param info: The information block that we use intead of the one coming from atom
    :param builds: locations to search for development builds
    :param force: Boolean - should we redownload pacakges that we already have installed?
    :return ljson.LaunchJson() instance
    """
    logging.debug("Package version: " + (version if version else '<highest>'))

    is_dev = version == 'dev'

    if is_dev:
        info = {
            'pacakge_name' : package,
            'type' : 'file',
            'uri' : None,
            'version' : 'dev',
            'filename' : None
        }

    elif info is None:
        info = communicate.get_package_info(package, version=version)

    if info is None:
        sys.exit(1)

    # -- Based on the information, we need to check on the version
    # and see if we already have it!
    path = utils.local_path(package, info['version'])

    launch_json = None

    if is_dev:
        #
        # Development pacakges are a special case. First, we check
        # if a local build can be found
        #
        for build_location in builds:
            p = os.path.join(build_location, package, 'launch.json')
            if os.path.exists(p):
                launch_json = p
                break

            # Check for a redirect.json with development builds that
            # have in install path
            redirect = os.path.join(build_location, package, 'redirect.json')
            if os.path.exists(redirect):
                with open(redirect, 'r') as f:
                    try:
                        redirect_data = json.load(f)
                    except:
                        logging.warning('Development redirect.json found '
                                        'but no object could be decoded')
                        continue

                    redirect_dir = redirect_data.get('redirect', '__')
                    p = os.path.join(redirect_dir, 'launch.json')
                    if os.path.exists(p):
                        launch_json = p
                        break

        if is_dev and not launch_json:
            #
            # We're trying to run a development package but we don't have
            # a build in our build directories. We can check Atom to see
            # if a development version exists. If it does, we want to try
            # and reinstall said development version to make it so we can
            # continually test something.
            #
            info = communicate.get_package_info(package, version=version)
            if info is None:
                sys.exit(1)


    if launch_json is None:
        launch_json = os.path.join(path, 'launch.json')

    if not is_dev:
        if not os.path.isfile(launch_json):

            # -- Do one additional check to see if this is a composed package
            # that we simply place into our local_path by building the launch
            # json to match
            if info.get('launch_data'):
                if not os.path.isdir(os.path.dirname(launch_json)):
                    os.makedirs(os.path.dirname(launch_json))

                with open(launch_json, 'w') as f:
                    json.dump(info['launch_data'], f)

            else:
                filename = info['uri'].split('/')[-1]

                # -- Get the package
                _download(info, path, filename)

                # -- Unzip it, cleaning up as we go
                arch = os.path.join(path, filename)
                _extract(arch)
                os.unlink(arch)

            # -- Basic validation
            if not os.path.isfile(launch_json):
                logging.critical(
                    'Launch file not found! Invalid package: "{}"'\
                    .format(package)
                )

    lj = ljson.LaunchJson(package, launch_json, development=is_dev)
    lj.version_number = info['version']
    return lj


def resolve_packages(package_list, retrieved, builds=[], all_ljsons=None):
    """
    Given a set of packages, unwrap the requirements
    """
    package_order = []

    if all_ljsons is None:
        all_ljsons = []

    def _package_names(l):
        if '/' in l:
            return l.split('/')[0]
        return l

    def _filter_had(d):
        if _package_names(d) in retrieved:
            logging.debug('Skipping: {} - already collected'.format(d))
            return False
        return True

    pre_retrieved = [_get_package_and_version(p)[0] for p in retrieved]

    # To make sure we can't go cyclic or overload explicit
    list(map(retrieved.add, map(_package_names, package_list)))

    main_package = None
    for package in package_list:

        logging.debug('Resolve: {}'.format(package))
        package, version = _get_package_and_version(package)

        if package in pre_retrieved:
            logging.debug('Required package: {} already satisfied'
                          .format(package))

            continue

        current_launch = _get_package(package, version, builds=builds)
        if main_package is None:
            main_package = current_launch

        requirements = current_launch.requires();
        if requirements:
            logging.debug('Package: {} - requires: {}'.format(
                package, ', '.join(requirements)
            ))

        to_retrieve = list(filter(_filter_had, requirements))

        extends = current_launch.extends()

        additional_resolved = []
        if extends:
            logging.debug('Package: {} - extends: {}'.format(
                package, extends
            ))

            #
            # Extending another package means merging the launch.json of a concrete
            # package. Because of this, we have to resolve the package right away
            # 
            # 
            if extends in retrieved:
                #
                # We've already located this package. This should really only happen
                # in development environments.
                #
                logging.debug('Base already resolved: {}'.format(extends))
                lj_to_remove = None
                for ljson in all_ljsons:
                    if ljson.package == _package_names(extends):
                        current_launch.set_base(ljson)
                        lj_to_remove = ljson
                        break

                if lj_to_remove:
                    all_ljsons.remove(lj_to_remove)

            else:
                # This will resolve the packages we need
                base_and_required = resolve_packages(
                    [extends], retrieved, builds=builds, all_ljsons=all_ljsons
                )
                base = base_and_required[-1]
                current_launch.set_base(base)

                pkg_names = map(_package_names, (lj.package for lj in base_and_required))
                list(map(retrieved.add, pkg_names))

                additional_resolved = base_and_required[:-1]

        order = resolve_packages(to_retrieve, retrieved, builds=builds, all_ljsons=all_ljsons)
        order.extend(additional_resolved)

        # -- Important! Make sure we sort the packages by "I need to load
        # first" in order to resolve env and variable expansion properly
        package_order.extend(order)
        package_order.append(current_launch)


    all_ljsons.extend(package_order)
    return package_order


def resolve_exec(ljson, env, arguments):
    """
    With a LaunchJson instance, we resolve the executable path
    :param ljson: LaunchJson instance
    :param env: Environment that we're building with
    :param arguments: The arguments that, in the event {__ARGS__} is present,
                      are supplied into
    :return: ``str, bool``
    """
    exec_ = ljson['executable'] or ljson['execute']

    args_consumed = False
    if arguments and '{__ARGS__}' in exec_:
        args_consumed = True
        wrapped = []
        for a in arguments:
            if ' ' in a:
                wrapped.append('"{}"'.format(a))
            else:
                wrapped.append(a)
        exec_ = exec_.replace('{__ARGS__}', ' '.join(wrapped))

    if not exec_:
        logging.critical(
            'Package: {} does not contain an executable entry! Cannot start!'\
                .format(ljson.package)
        )
        sys.exit(1)

    return ljson.expand(exec_, env), args_consumed


def prep_env(ljson, env):
    """
    With a LaunchJson object and the active environment augmentation,
    build out the rest of our environment
    :param ljson: LaunchJson object for a package
    :param env: dict copy of our environment that we augment and will
    pass to our subprocesses
    :return: None
    """
    package_env = ljson['env']
    if not package_env:
        return

    with log.log_indent():
        for k, v in utils._iter(package_env):
            logging.debug('Expanding: {}'.format(k))
            ljson.expand(v, env, key=k)


def print_path(package, show_all_versions=False):
    """
    With a package, let's get the local path and print it
    """
    package, version = _get_package_and_version(package)

    root_pkg_path = utils.local_path(package)
    if not os.path.isdir(root_pkg_path):
        return

    if show_all_versions:
        for ver in os.listdir(root_pkg_path):
            if os.path.exists(os.path.join(root_pkg_path, ver, 'launch.json')):
                print (os.path.join(root_pkg_path, ver).replace('\\','/'))
    else:
        print (root_pkg_path)


def clear_package(package):
    """
    Clean out all versions of a package (if we have it)
    :package: str name of the package to remove
    :return: None
    """
    if package == 'ALL_PACKAGES':
        logging.debug('Cleaning: {} - Reset Repository'.format(package))
        root_pkg_path = utils.local_path(package, None, base_only=True)
    else:
        logging.debug('Cleaning: {}'.format(package))
        root_pkg_path = utils.local_path(package)
    if os.path.exists(root_pkg_path):
        shutil.rmtree(root_pkg_path)
