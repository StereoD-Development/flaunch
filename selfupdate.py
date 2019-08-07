"""
Utility for updating flaunch without having to reinstall
or manage it separately
"""
import os
import sys
import shutil

class TempTree(object):
    """
    Context utility to make the update process as much of a "transaction"
    as possible. This way, in the event of an error while updating, we
    can try to restore normal use as much as possible
    """
    def __init__(self, folder, temp_dir_name, log_error=True):
        self._folder = folder
        self._temp_dir_name = temp_dir_name
        self._log = log_error
        self._additional = []
        self._revert = False

    def add_temp_item(self, f, t):
        self._additional.append((f, t))
        os.rename(f, t)

    def revert_on(self):
        """
        Ingore the request
        """
        self._revert = True

    def __enter__(self):
        os.rename(self._folder, self._temp_dir_name)
        return self


    def __exit__(self, type, value, traceback):
        import logging
        if (type is not None) or self._revert:
            if self._log and not self._revert:
                logging.error("Error while updating! Attempting to revert any changes!")
            if os.path.exists(self._folder):
                shutil.rmtree(self._folder)
            os.rename(self._temp_dir_name, self._folder)

            for file, temp_item in self._additional:
                if os.path.isfile(file):
                    os.unlink(file)
                elif os.path.isdir(file):
                    shutil.rmtree(file)
                os.rename(temp_item, file)

        else:
            shutil.rmtree(self._temp_dir_name)
            for file, temp_item in self._additional:
                if os.path.isfile(temp_item):
                    os.unlink(temp_item)
                elif os.path.isdir(temp_item):
                    shutil.rmtree(temp_item)
            if self._log:
                logging.debug('Completed update process!')


def update_flaunch():
    """
    Assert that we're using the latest version of flaunch available. If we're
    not - let's update our code right away
    :param flaunch_info: dict of information sent from atom about this package
    :return: None
    """
    # First, we actually copy the current src files into a second location
    # so we can use them in case an upgrade is required
    this_dir = os.path.dirname(os.path.abspath(__file__))

    if os.path.exists(os.path.join(this_dir, '.git')):
        print ("fupdate is desgined for deployments of flaunch only. Not a git repo")
        return 1

    #
    # We need the src and py directories to run our update, but they'll be
    # things that we update, so we create a mirror of them for temporary
    # use.
    #
    with TempTree(this_dir + '/src', this_dir + '/src_old') as tt:
        tt.add_temp_item(this_dir + '/py', this_dir + '/py_old')

        sys.path.append(this_dir + '/src_old')
        sys.path.append(this_dir + '/py_old/flaunch_packages.zip')

        from launch import pkgrep
        from common import communicate
        from common import log
        log.start(True, None)
        import logging

        flaunch_info = communicate.get_flaunch_info()
        version_file = os.path.join(this_dir, 'version.txt')

        current_version = ''
        with open(version_file, 'r') as f:
            f.seek(0)
            current_version = f.readline().strip()

        if current_version == flaunch_info['version']:
            logging.info('flaunch is up to date! Version: {}'.format(current_version))
            tt.revert_on()
            return 0

        # -- We have the the wrong version, time to upgrade
        launch_json = pkgrep._get_package('flaunch', info=flaunch_info)

        new_version_dir = launch_json.path
        for file_or_dir in os.listdir(new_version_dir):
            logging.debug("Updating: {}".format(file_or_dir))

            this_path = os.path.join(this_dir, file_or_dir)
            if os.path.exists(this_path):
                tt.add_temp_item(this_path, os.path.join(this_dir, file_or_dir + '_old'))

            new_file = os.path.join(new_version_dir, file_or_dir)
            if os.path.isdir(new_file):
                shutil.copytree(new_file, this_path)
            else:
                if file_or_dir.startswith('fupdate') or file_or_dir == 'selfupdate.py':
                    # The self update files are manually rewritten to attempt
                    # keeping clean between uses
                    with open(this_path, 'w') as writeme:
                        with open(new_file, 'r') as readme:
                            writeme.write(readme.read())
                else:
                    shutil.copy2(new_file, this_path)

        # Last but not least, let's update the version number
        with open(version_file, 'w') as f:
            f.write(launch_json.version_number)

    return 0

if __name__ == '__main__':
    sys.exit(update_flaunch())