"""
ZipFile utilities for flaunch - perhaps one day adding tarfile support too

Also Tar files!
"""

import os
import sys
import time
import zipfile
import logging
import fnmatch

# -- Math from ziptools

SYMLINK_TYPE  = 0xA
SYMLINK_PERM  = 0o755
SYMLINK_ISDIR = 0x10
SYMLINK_MAGIC = (SYMLINK_TYPE << 28) | (SYMLINK_PERM << 16)

assert SYMLINK_MAGIC == 0xA1ED0000, 'Bit math is askew'    

def _zip_symlink(filepath, zippath, zfile):
    """
    Create: add a symlink (to a file or dir) to the archive.
    :param filepath: The (possibly-prefixed and absolute) path to the link file.
    :param zippath: The (relative or absolute) path to record in the zip itself.
    :param zfile: The ZipFile object used to format the created zip file. 
    """
    assert os.path.islink(filepath)
    linkpath = os.readlink(filepath)

    # 0 is windows, 3 is unix (e.g., mac, linux) [and 1 is Amiga!]
    createsystem = 0 if sys.platform.startswith('win') else 3 

    linkstat = os.lstat(filepath)
    origtime = linkstat.st_mtime
    ziptime  = time.localtime(origtime)[0:6]

    # zip mandates '/' separators in the zfile
    if not zippath:
        zippath = filepath
    zippath = os.path.splitdrive(zippath)[1]
    zippath = os.path.normpath(zippath)
    zippath = zippath.lstrip(os.sep)
    zippath = zippath.replace(os.sep, '/')
   
    newinfo = zipfile.ZipInfo()
    newinfo.filename      = zippath
    newinfo.date_time     = ziptime
    newinfo.create_system = createsystem
    newinfo.compress_type = zfile.compression
    newinfo.external_attr = SYMLINK_MAGIC

    if os.path.isdir(filepath):
        newinfo.external_attr |= SYMLINK_ISDIR

    zfile.writestr(newinfo, linkpath)


def _info_is_symlink(zinfo):
    """
    Extract: check the entry's type bits for symlink code.
    This is the upper 4 bits, and matches os.stat() codes.
    """
    return (zinfo.external_attr >> 28) == SYMLINK_TYPE


def _extract_symlink(zipinfo, pathto, zipfile, nofixlinks=False):
    """
    Extract: read the link path string, and make a new symlink.

    'zipinfo' is the link file's ZipInfo object stored in zipfile.
    'pathto'  is the extract's destination folder (relative or absolute)
    'zipfile' is the ZipFile object, which reads and parses the zip file.
    """
    assert zipinfo.external_attr >> 28 == SYMLINK_TYPE
    
    zippath  = zipinfo.filename
    linkpath = zipfile.read(zippath)
    linkpath = linkpath.decode('utf8')

    # drop Win drive + unc, leading slashes, '.' and '..'
    zippath  = os.path.splitdrive(zippath)[1]
    zippath  = zippath.lstrip(os.sep)
    allparts = zippath.split(os.sep)
    okparts  = [p for p in allparts if p not in ('.', '..')]
    zippath  = os.sep.join(okparts)

    # where to store link now
    destpath = os.path.join(pathto, zippath)
    destpath = os.path.normpath(destpath)

    # make leading dirs if needed
    upperdirs = os.path.dirname(destpath)
    if upperdirs and not os.path.exists(upperdirs):
        os.makedirs(upperdirs)

    # adjust link separators for the local platform
    if not nofixlinks:
        linkpath = linkpath.replace('/', os.sep).replace('\\', os.sep)

    # test+remove link, not target
    if os.path.lexists(destpath):
        os.remove(destpath)

    # windows dir-link arg
    isdir = zipinfo.external_attr & SYMLINK_ISDIR
    if (isdir and
        sys.platform.startswith('win') and
        int(sys.version[0]) >= 3):
        dirarg = dict(target_is_directory=True)
    else:
        dirarg ={}

    # make the link in dest (mtime: caller)
    os.symlink(linkpath, destpath, **dirarg)
    return destpath


class ZFile(object):
    """
    py2/3 compat context manager for a zipfile
    """
    def __init__(self, name, mode, *args, **kwargs):
        self._name = name
        self._mode = mode
        self._args = args
        self._kwargs = kwargs

    def __enter__(self):
        if self._mode == 'r':
            self._zfile = zipfile.ZipFile(self._name, self._mode)
        else:
            self._zfile = zipfile.ZipFile(
                self._name, self._mode, compression=zipfile.ZIP_DEFLATED
            )

        return self._zfile

    def __exit__(self, type, value, traceback):
        self._zfile.close()


def zip_files(name, files, root=None, mode='w', ignore=[], noisey=False):
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

    root = root.replace("\\", "/")

    def _clean(p):
        return p.replace('\\', '/').lstrip('/')

    with ZFile(name, mode) as zfile:
        for file_name in files:
            file_name = file_name.replace("\\", "/")


            if any(fnmatch.fnmatch(file_name, p) for p in ignore):
                continue

            if any(fnmatch.fnmatch(os.path.basename(file_name), p) for p in ignore):
                continue

            def _zip_action(base, files):
                """
                Recurse and do the action required
                """
                for file in files:
                    if any(fnmatch.fnmatch(file, p) for p in ignore):
                        continue

                    fpath = _clean(os.path.join(base, file))
                    if any(fnmatch.fnmatch(fpath, p) for p in ignore):
                        continue

                    if os.path.isdir(fpath):

                        files = os.listdir(fpath)
                        if not files:
                            if noisey:
                                logging.info("Zipping: {}".format(fpath))
                            directory_path = _clean(fpath.replace(root, '', 1))
                            zinfo = zipfile.ZipInfo(directory_path + '/')
                            zfile.writestr(zinfo, '')
                        else:
                            _zip_action(fpath, files)

                    else:
                        archive_root = _clean(fpath.replace(root, '', 1))
                        if os.path.islink(fpath):
                            if noisey:
                                logging.info("Zipping (symlink): {}".format(fpath))
                            _zip_symlink(fpath, archive_root, zfile)
                        else:
                            if noisey:
                                logging.info("Zipping: {}".format(fpath))
                            zfile.write(fpath, archive_root)

            if os.path.isdir(file_name):
                _zip_action(file_name, os.listdir(file_name))
            elif os.path.exists(file_name):
                _zip_action(os.path.dirname(file_name), [os.path.basename(file_name)])
            else:
                raise RuntimeError('File not found: {}',format(file_name))


def unzip_files(archive, files=[], ignore=[], output=None, noisey=False):
    """
    Extract data from an archive.
    :param archive: Path to a zipped archive that can be opened
    :param files: List of files (unix pattern matched) to extract | None for all
    :param exclude: When extracing, exclude these files
    :param output: Destination of our archive
    :return: None
    """
    with ZFile(archive, 'r') as zfile:

        def _extract(zinfo, fn):
            if noisey:
                logging.info("Extract: {}".format(fn))

            if '/' in zinfo.filename:
                dir_ = os.path.join(output, os.path.dirname(zinfo.filename))
                if not os.path.exists(dir_):
                    os.makedirs(dir_)
            else:
                dir_ = '.'
            if _info_is_symlink(zinfo):
                extracted_path = _extract_symlink(zinfo, output, zfile, False)
            else:
                extracted_path = zfile.extract(zinfo, output)
                if zinfo.create_system == 3:
                    unix_attributes = zinfo.external_attr >> 16
                    if unix_attributes:
                        os.chmod(extracted_path, unix_attributes)

        for zip_info in zfile.infolist():

            file_name = zip_info.filename

            # Check if this is a file we want
            if files:
                for ok_pattern in files:
                    if fnmatch.fnmatch(file_name, ok_pattern):
                        _extract(zip_info, file_name)
            elif ignore:
                # Check if we want to ignore this file
                for ignore_pattern in ignore:
                    if fnmatch.fnmatch(file_name, ignore_pattern):
                        break
                else:
                    # None of the ignore patterns matched
                    _extract(zip_info, file_name)
            else:
                _extract(zip_info, file_name)


# -------------------------------------------------------------------------
# -- Tar Files

import tarfile


def tar_files(name, files, root=None, mode='w', ignore=[], noisey=False):
    """
    Build a tar of a given set of files.

    :param name: The name of this archive
    :param files: list[str] of paths to files
    :param root: The root directory of our archive to base the files
    off of
    :param mode: The mode to open our zip file with ('w' or 'a')
    """

    if root is None:
        root = ''

    root = root.replace("\\", "/")

    def _clean(p):
        return p.replace('\\', '/').lstrip('/')

    comp_mode = ''
    if name.endswith('.tar.gz') or name.endswith('.tgz'):
        comp_mode = ':gz'

    with tarfile.open(name, mode + comp_mode) as tar:

        def _tar_action(base, files):
            """
            Recurse through directories to build the tar file
            """
            for file in files:
                if any(fnmatch.fnmatch(file, p) for p in ignore):
                    continue

                fpath = _clean(os.path.join(base, file))
                if any(fnmatch.fnmatch(fpath, p) for p in ignore):
                    continue

                if os.path.isdir(fpath):
                    files = os.listdir(fpath)
                    if not files:
                        if noisey:
                            logging.info("Tar Directory: {}".format(fpath))
                        directory_path = _clean(fpath.replace(root, '', 1))
                        tar.add(fpath, arcname=directory_path, recursive=False)
                    else:
                        _tar_action(fpath, files)

                else:
                    # -- This is a file (or link)
                    if noisey:
                        logging.info("Tar: {}".format(fpath))

                    file_path = _clean(fpath.replace(root, '', 1))
                    tar.add(fpath, arcname=file_path)


        for file_name in files:
            file_name = file_name.replace("\\", "/")

            if any(fnmatch.fnmatch(file_name, p) for p in ignore):
                continue

            if any(fnmatch.fnmatch(os.path.basename(file_name), p) for p in ignore):
                continue

            if os.path.isdir(file_name):
                _tar_action(file_name, os.listdir(file_name))
            elif os.path.exists(file_name):
                _tar_action(os.path.dirname(file_name), [os.path.basename(file_name)])
            else:
                raise RuntimeError('File not found: {}',format(file_name))


def untar_files(archive, files=[], ignore=[], output=None, noisey=False):
    """
    Extract data from an archive.
    :param archive: Path to a zipped archive that can be opened
    :param files: List of files (unix pattern matched) to extract | None for all
    :param exclude: When extracing, exclude these files
    :param output: Destination of our archive
    :return: None
    """
    with tarfile.open(archive, 'r:*') as tar:

        def _extract(tarinfo, fn):
            if noisey:
                logging.info("Extract: {}".format(fn))

            if '/' in tarinfo.name:
                dir_ = os.path.join(output, os.path.dirname(tarinfo.name))
                if not os.path.exists(dir_):
                    os.makedirs(dir_)
            else:
                dir_ = '.'

            tar.extract(tarinfo, path=output)

        for tar_info in tar:

            file_name = tar_info.name

            if files:
                for ok_pattern in files:
                    if fnmatch.fnmatch(file_name, ok_pattern):
                        _extract(tar_info, file_name)
            elif ignore:
                for ignore_pattern in ignore:
                    if fnmatch.fnmatch(file_name, ignore_pattern):
                        break
                else:
                    _extract(tar_info, file_name)
            else:
                _extract(tar_info, file_name)
