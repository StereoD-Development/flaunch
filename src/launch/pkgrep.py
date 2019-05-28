"""
Tools for grabbing packages from our repo and working out the environment
for a list of packages
"""

import os
import sys
import shutil
import logging
import zipfile

from common import log
from common import utils
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
            logging.critical(
                ('Cannot download {} - Possible unknown '
                 'version or missing files!').format(path)
            )
            sys.exit(1)

        logging.debug("Copy: " + path)
        logging.debug("To: " + arch_path)
        shutil.copy2(path, arch_path)

def _extract(zipfile_path):
    """
    Unzip a file
    :param zipfile_path: The path to a .zip file that we're unloading
    :return: None
    """
    zip_ref = zipfile.ZipFile(zipfile_path, 'r')
    zip_ref.extractall(os.path.dirname(zipfile_path))
    zip_ref.close()

def _get_package_and_version(package):
    version = None
    if '/' in package:
        package, version = package.split('/')
    return (package, version)

def _get_package(package, version=None, info=None, repos=[]):
    """
    Get a particular package
    """
    logging.debug("Package version: " + (version if version else '<highest>'))

    if info is None:
        info = communicate.get_package_info(package, version=version)

    if info is None:
        sys.exit(1)

    # -- Based on the information, we need to check on the version
    # and see if we already have it!
    is_dev = info['version'] == 'dev'
    path = utils.local_path(package, info['version'])

    launch_json = None
    if is_dev:
        for repo_location in repos:
            p = os.path.join(repo_location, package, 'launch.json')
            if os.path.exists(p):
                launch_json = p
    
    if launch_json is None:
        launch_json = os.path.join(path, 'launch.json')

    if not is_dev:
        if not os.path.isfile(launch_json):
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

    return utils.LaunchJson(package, launch_json)

def resolve_packages(package_list, retrieved, repos=[]):
    """
    Given a set of packages, unwrap the requirements
    """
    package_order = []

    def _package_names(l):
        if '/' in l:
            return l.split('/')[0]
        return l

    def _filter_had(d):
        if _package_names(d) in retrieved:
            logging.debug('Skipping: {} - already collected'.format(d))
            return False
        return True

    # To make sure we can't go cyclic or overload explicit
    list(map(retrieved.add, map(_package_names, package_list)))

    for package in package_list:

        logging.debug('Resolve: {}'.format(package))
        package, version = _get_package_and_version(package)

        current_launch = _get_package(package, version, repos=repos)

        requirements = current_launch.requires();
        if requirements:
            logging.debug('Package: {} - requires: {}'.format(
                package, ', '.join(requirements)
            ))

        to_retrieve = list(filter(_filter_had, requirements))

        extends = current_launch.extends()
        if extends:
            logging.debug('Package: {} - extends: {}'.format(
                package, extends
            ))
            to_retrieve.append(extends)

        order = resolve_packages(to_retrieve, retrieved)

        # -- Important! Make sure we sort the packages by "I need to load
        # first" in order to resolve env and variable expansion properly
        package_order.extend(order)
        package_order.append(current_launch)

    return package_order


def resolve_exec(ljson, env):
    """
    With a LaunchJson instance, we resolve the executable path
    :param ljson: LaunchJson instance
    :param env: Environment that we're building with
    :return: str
    """
    exec_ = ljson['executable'] or ljson['execute']
    if not exec_:
        logging.critical(
            'Package: {} does not contain an executable entry! Cannot start!'\
                .format(ljson.package)
        )

    return ljson.expand(exec_, env)


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
    shutil.rmtree(root_pkg_path)


def update_flaunch(flaunch_info):
    """
    Assert that we're using the latest version of flaunch available. If we're
    not - let's update our code right away
    :param flaunch_info: dict of information sent from atom about this package
    :return: None
    """
    version_file = os.path.join(utils.path_ancestor(
        os.path.abspath(__file__), 3
    ),  'version.txt')

    current_version = ''
    with open(version_file, 'r') as f:
        f.seek(0)
        current_version = f.readline().strip()

    if current_version == flaunch_info['version']:
        logging.info('FLaunch is up to date! Version: {}'.format(current_version))
        return 0

    # -- We have the the wrong version, time to upgrade
    launch_json = _get_package('flaunch', info=flaunch_info)
    # -- TODO
