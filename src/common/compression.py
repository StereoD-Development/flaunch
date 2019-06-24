"""
ZipFile utilities for flaunch - perhaps one day adding tarfile support too
"""

import os
import sys
import zipfile
import logging


class ZFile(object):
    """
    py2/3 compat context manager for a zipfile
    """
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def __enter__(self):
        try:
            self._zfile = zipfile.ZipFile(
                *self._args, compression=zipfile.ZIP_LZMA
            )
        except RuntimeError as e:
            logging.warning('LZMA not found: {}, trying zlib'.format(str(e)))
            self._zfile = zipfile.ZipFile(
                *self._args, compression=zipfile.ZIP_DEFLATED
            )

        return self._zfile

    def __exit__(self, type, value, traceback):
        self._zfile.close()


def zip_files(name, files, root=None, mode='w', ignore=[]):
    """
    Zip up a given set of files. This will handle symlinks and empty directories as
    well to make things a bit easier.

    # https://stackoverflow.com/questions/35782941/archiving-symlinks-with-python-zipfile

    :param name: The name of this archive
    :param files: list[str] of paths to files
    :param root: The root directory of our archive to base the files
    off of
    :param mode: The mode to open our zip file with ('w' or 'a')
    """
    if not name.endswith('.zip'):
        name += '.zip'

    if root is None:
        root = ''

    def _clean(p):
        return p.replace('\\', '/').lstrip('/')

    with ZFile(name, mode) as zfile:
        for file_name in files:
            file_name = file_name.replace("\\", "/")

            all_files = []
            if os.path.isdir(file_name):
                for base, dirs, files in os.walk(file_name):

                    #
                    # Check for empty directories
                    #
                    for dir_ in dirs:
                        for pattern in ignore:
                            if fnmatch.fnmatch(dir_, pattern):
                                break
                        else:
                            fn = os.path.join(base, dir_)
                            if os.listdir(fn) == []:
                                directory_path = _clean(fn.replace(root, '', 1))
                                zinfo = zipfile.ZipInfo(directory_path + '/')
                                zfile.writestr(zinfo, '')

                    for file in files:

                        for pattern in ignore:
                            if fnmatch.fnmatch(file, pattern):
                                break
                        else:
                            fn = os.path.join(base, file)
                            archive_root = _clean(fn.replace(root, '', 1))

                            if os.path.islink(fn):
                                #
                                # Math for equating symlinks
                                #
                                zinfo = zipfile.ZipInfo(archive_root)
                                zinfo.create_system = 3
                                # zinfo.external_attr = 0xA1ED0000L
                                # zinfo.external_attr = 2716663808L
                                zinfo.external_attr = 0xA0000000
                                zfile.writestr(zinfo, os.readlink(fn))
                            else:
                                zfile.write(fn, archive_root)

            elif os.path.isfile(file_name):
                zfile.write(file_name, file_name.replace(root, '', 1))

            else:
                raise RuntimeError('File not found: {}')
