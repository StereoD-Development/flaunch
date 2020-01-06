"""

"""
from __future__ import absolute_import

import os
import requests
import platform

from common import utils
from common import communicate
from build.command import _BuildCommand


# Default endpoints for the Jenkins build system
JENKINS_ENDPOINT = {
    'windows' : os.environ.get(
        'JENKINS_ENDPOINT_WINDOWS', 'http://sdt-devbuild.stereodstaff.com:8080'
    ),
    'linux' : os.environ.get(
        'JENKINS_ENDPOINT_LINUX', 'http://10.5.36.101:8080'
    )
}

JENKINS_DEFAULT_TOKEN = 'thatsnomoon'


class JenkinsCommand(_BuildCommand):
    """
    A fun interface with Jenkins and it's build utilities.
    This will ship off jobs to the front!
    """
    alias = 'JENKINS'

    def description(selfl):
        return 'Jekins build toolkit interface'


    def _submit(self, build_file):
        """
        Submit a build job to Jenkins.

        In the long run, we need to have a manager/worker setup for
        our jenkins cluster so that work can be a striaght shot
        rather than submitting to each platform's jenkins instance
        """ 
        parameters = []
        parameters.append({'name' : 'version', 'value' : self.data.version})

        job_data = { 'parameter' : parameters }
        for platform_ in self.data.platform or [platform.system()]:


            ## ____START__HERE___ISH____
            proper_jobname = '!!TODO!! -> need some kind of known system'
            proper_jobname = build_file.attributes()['']

            endpoint = JENKINS_ENDPOINT[platform_.lower()]
            endpoint += '/job/{}/build'.format(proper_jobname)

            # -- May have to handle a client session here
            result = requests.post(
                endpoint,
                json=job_data,
                headers=communicate.default_headers()
            )


    def _status(self, build_file):
        """
        Get the status of a select job

        TODO
        """
        return


    def populate_parser(self, parser):
        """
        The Jenkins parser can handle a couple different scenarios
        """
        choices = ('submit', 'status')
        parser.add_argument(
            'type',
            help='What would you like to do?',
            choices=choices
        )
        parser.add_argument('version', help='The version (git tag) to build')
        parser.add_argument(
            '-d', '--deploy',
            action='store_true',
            help='If set, Jenkins will also use fbuild '\
                 'to deploy around the globe for release'
        )
        parser.add_argument(
            '-p', '--platform',
            action='append',
            help='Act on a specific (set of) platform(s)'
        )


    def run(self, build_file):
        """
        Fire away! This is made more challenging based on the type
        of request
        """
        if self.data.type == 'submit':
            self._submit(build_file)
        elif self.data.type == 'status':
            self._status(build_file)
        else:
            logging.error('Invalid Jenkins build type: "{}"'.format(
                self.data.type
            ))

