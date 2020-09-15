"""
Handling the deployment of a project can change between projects. This attempts
to keep everything as flexible as possible

NOTE: DON'T sys.exit(1) out of here. We're trying to catch these
errors for better reporting.
"""
from __future__ import print_function, absolute_import

import os
import sys
import shutil
import logging
import platform

from common import utils
from common import communicate
from types import ModuleType
from build.command import _BuildCommand

from common import transfer

class DeploymentCommand(_BuildCommand):
    """
    The great deployer!
    """
    alias = 'DEPLOY'

    def description(self):
        return 'Deployment mechanism (can only be called from deploy:commands)'


    def populate_parser(self, parser):
        parser.add_argument(
            'package',
            help='Zip package to deploy - this is just the name of the zip file, not the full path'
        )
        parser.add_argument(
            '-r', '--repo',
            help='The base of the flaunch repo for this package to use when deploying'
        )


    def run(self, build_file):
        """
        Deployment time. This is where our transfer kicks in
        """
        manager = build_file.get_manager()

        from build.deploy import DeployManager
        if not isinstance(manager, DeployManager) or manager.stage != 'deploy':
            raise RuntimeError('Cannot use :DEPLOY command when not in the deploy:commands')

        # Check if we are an agnostic package we can deploy to
        # other platforms automatically
        platforms = manager.arguments.platform

        if self.data.repo:
            this_platform = platform.system()
            this_package = os.path.join(
                self.data.repo, this_platform, self.data.package
            )

            if build_file[manager.type_]['agnostic']:
                others = set(['Windows', 'Linux', 'Darwin']) - set([this_platform])
                for plat in others:
                    other_location = os.path.join(
                        self.data.repo, plat, self.data.package
                    )
                    if not os.path.exists(other_location):
                        try:
                            os.makedirs(os.path.dirname(other_location))
                        except OSError:
                            pass
                        logging.info('Agnostic deployment to: {}'.format(plat))
                        shutil.copy2(this_package, other_location)

                if not platforms:
                    platforms = list(others) + [this_platform]

        destinations = manager.arguments.destination
        exclude = manager.arguments.exclude

        transfer.transfer_package(
            build_file,
            self.data.package,
            destinations=destinations,
            exclude=exclude,
            platforms=platforms,
            wait= manager.arguments.skip_wait == False
        )
        return


class ReleaseCommand(_BuildCommand):
    """
    Execute a release of a package
    """
    alias = 'RELEASE'

    def description(self):
        return ('Custom release command. Typically used to handle '
               'custom addon packages (e.g. virtualenv)')


    def populate_parser(self, parser):
        parser.add_argument(
            'package',
            help='The package name to release'
        )

        parser.add_argument(
            'version',
            help='The version this release is under'
        )

        parser.add_argument(
            '-f', '--force',
            action='store_true',
            help='Force the release even if validation does not pass'
        )

        parser.add_argument(
            '-b', '--beta',
            action='store_true',
            help='Use to signify a pre-release of some sort'
        )

    def run(self, build_file):
        """
        Execute the registration
        """
        manager = build_file.get_manager()

        from build.deploy import DeployManager
        if not isinstance(manager, DeployManager):
            raise RuntimeError('Cannot use :RELEASE outside of the deployment scope')

        use_force = manager.arguments.force
        use_beta = manager.arguments.beta

        communicate.register_package(
            self.data.package,
            self.data.version,
            method='post',
            launch_data=None,
            force=self.data.force or use_force,
            pre_release=self.data.beta or use_beta
        )

