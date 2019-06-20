"""
Management tools for building/deploying things
"""
from __future__ import absolute_import

import os
import sys
import platform
import subprocess
import logging
import traceback
import json
from copy import deepcopy

try:
    import yaml
except:
    try:
        import pureyaml as yaml # Current version is broken but you never know
        yaml.safe_load = yaml.load
    except:
        raise ImportError("A yaml parser is required to use fbuild - " \
                          "developers should use \"pip install PyYAML\"")

from common.platformdict import PlatformDict
from common.abstract import _AbstractFLaunchData, FLaunchDataError
from common import log
from common import utils
from common import constants

from .parse import BuildCommandParser


class BuildFile(_AbstractFLaunchData):
    """
    A build file describes the processes required for constructing and
    deploying packages with flaunchdev
    """
    def __init__(self, package, path, manager=None):
        try:
            with open(path) as f:
                d = yaml.safe_load(f.read())

                if not d.get('props'):
                    d['props'] = {} # Make sure for plugin setup

                data = PlatformDict(d)
        except Exception as e:
            logging.error(path + ' - invalid yaml file')
            raise FLaunchDataError(str(e))

        _AbstractFLaunchData.__init__(self, package, path, data)
        self._load()

        self._build_manager = manager

    def set_manager(self, manager):
        """
        Link ourselves back to a build manager
        :param manager: The BuildManager that owns this item
        """
        self._build_manager = manager

    @property
    def additional(self):
        if self._build_manager:
            return self._build_manager.additional
        return []


    @property
    def build_dir(self):
        if self._build_manager:
            return self._build_manager.build_dir
        return ''


    @property
    def install_path(self):
        if self._build_manager:
            return self._build_manager.install_path
        return ''


    @property
    def source_dir(self):
        if self._build_manager:
            return self._build_manager.source_dir
        return ''


    def add_attribute(self, key, value):
        """
        Add an attribute to our properties
        """
        if self['props'] is None:
            self._data.update({'props' : {}})
        self._data['props'].update({key : value})


    def attributes(self):
        """
        For variable expansion, we handle it at the build file level
        """
        return deepcopy(self['props']) or PlatformDict()


    def command_environment(self, env):
        """
        The environment that we run when working with a command
        based tool
        :return: dict{str:str}
        """
        if self['env']:
            for k,v in utils._iter(self['env']):
                # Passing key will update the environment
                self.expand(v, env, key=k)


    def get_function_commands(self, name):
        """
        Get a function based on it's name as well as any arguments it
        requires
        :param namne: The name of the function to look up (this should
        exclude the func__)
        :return: tuple(list[<COMMAND>,], list[str])
        """
        commands = []
        arguments = []

        if '(' in name:
            name = name[:name.index('(')]

        for key, value in utils._iter(self._data):
            if key.startswith('func__'):
                func_name = key[:key.index('(')].replace('func__', '')
                if func_name == name:
                    commands = self[key]

                    # We've found the function, now check for arguments
                    # we need to supply
                    func_args_string = key[key.index('(')+1:key.index(')')]
                    if func_args_string:
                        func_args_string = func_args_string.split(',')
                        arguments = [a.strip() for a in func_args]

        return commands, arguments


    def _load(self):
        """
        The BuildFile manages some additional features. See docs/plugins.md for
        for information
        """

        #
        # Start with any plugins. Our local build file will overload anything in
        # said plugin but it's good to have
        #
        if self['include']:
            if not isinstance(self['include'], (list, tuple)):
                raise TypeError('build.yaml -> include: must be a list of plugins')

            for plugin in self['include']:
                plugin_filepath = utils.path_ancestor(os.path.abspath(__file__), 3)
                plugin_filepath = os.path.join(plugin_filepath, 'plugins', plugin + '.yaml')

                if not os.path.isfile(plugin_filepath):
                    logging.error("Invalid plugin: {}".format(plugin_filepath))
                    return

                with open(plugin_filepath) as f:
                    plugin_data = yaml.safe_load(f)
                    self._data = PlatformDict(
                        dict(utils.merge_dicts(plugin_data, self._data.to_dict()))
                    )


class BuildManager(object):
    """
    Base calss for build management. This handles a lot of the cruft for us when
    building with different toolkits (cmake, qmake, basic python, etc.)

    Managers for different build types can be added to to help speed up a particular
    workflow if need be.

    What's more is that the whole app meshes with the flaunch tools for some very
    powerful tools.
    """
    registry = []

    def __init__(self, app, arguments, build_file, source_dir=None):
        self._app         = app
        self._is_local    = arguments.local
        self._no_clean    = arguments.no_clean
        self._additional  = arguments.additional_arguments
        self._build_file  = build_file
        self._source_dir  = source_dir or build_file.path
        self._build_file.set_manager(self)

    # -- Registration

    @staticmethod
    def register(builder_class):
        """
        Register a build manager
        """
        BuildManager.registry.append(builder_class)

    # -- Public Interface

    def run_build(self):
        """
        Run the full extent of the build. This includes any pre and post
        commands.
        """
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir)

        os.chdir(self.build_dir)

        self._prerequisite_check()

        self._pre_build_commands()

        self.build()

        self._post_build_commands()

    @property
    def source_dir(self):
        return self._source_dir.replace('\\', '/')


    @property
    def development_path(self):
        return utils.local_path(self.package, version='dev')


    @property
    def build_dir(self):
        bf_build = self.build_file['build'] # type: PlatformDict
        if bf_build['build_path']:
            build_path = self.build_file.expand(bf_build['build_path'])
        elif os.environ.get(constants.FLAUNCH_BUILD_DIR, None):
            build_path = os.path.join(os.environ[constants.FLAUNCH_BUILD_DIR], self.package)
        else:
            build_path = self.development_path
        return build_path.replace('\\', '/')


    @property
    def install_path(self):
        raise NotImplementedError('FUTURE')


    @property
    def package(self):
        return self._app


    @property
    def build_file(self):
        return self._build_file


    @property
    def additional(self):
        return self._additional


    @classmethod
    def get_manager(cls, package, arguments):
        """
        Grab the manager based on the build.yaml file
        """
        from build import managers

        yaml_file = arguments.custom or cls._yaml_file_from_package(package)
        source_dir = None

        if isinstance(yaml_file, list):
            yaml_file, source_dir = yaml_file

        if not os.path.isfile(yaml_file):
            logging.critical('Invalid build yaml: {}'.format(yaml_file))
            sys.exit(1)

        build_data = BuildFile(package, yaml_file)
        build_type = build_data['build']['type']

        for _cls in BuildManager.registry:
            if hasattr(_cls, 'alias') and _cls.alias == build_type:
                return _cls(package,
                            arguments,
                            build_data,
                            source_dir=source_dir)

        logging.critical('Cannot find build a build manager')


    @classmethod
    def _yaml_file_from_package(cls, package):
        """
        Based on the environment, grab the package that is most likely
        to be used for the 
        :param package: The name of the package were going to use
        :return: str
        """
        return os.path.join(
            os.environ.get(constants.FLAUNCH_DEV_DIR, os.getcwd()),
            package,
            'build.yaml'
        )

    # -- "Protected" methodM

    def create_launch_json(self, build_path):
        """
        Create a launch.json file within our build directory.
        Uses the 'launch_json' key if available 
        """
        bf_build = self._build_file['build']

        ljson_path = os.path.join(build_path, 'launch.json')
        if bf_build['launch_json']:
            if not isinstance(bf_build['launch_json'], PlatformDict):
                logging.critical('launch_json must be a JSON compliant dictionary!')
                with log.log_indent():
                    s = traceback.format_stack()
                    map(logging.critical, s)
                sys.exit(1)

            with open(ljson_path, 'w') as f:
                json.dump(bf_build['launch_json'].to_dict(), f, sort_keys=True, indent=4)

        else:
            real_path = os.path.join(self._build_file.path, 'launch.json')
            if os.path.isfile(real_path):
                import shutil
                shutil.copy2(real_path, ljson_path)

        if not os.path.exists(ljson_path):
            # Not hyper critical
            logging.warning('launch.json file not found! Expect issues when launching!')


    # -- Virtual Interface

    def build(self):
        """
        Execute the build.
        """
        pass # Overload per manager

    # -- Private Methods

    def _prerequisite_check(self):
        """
        In the event our action requires select software to be available
        from it's root environment, we call that here.

        Perhaps in the future we could also include "modules" for finding
        basic tools and items.
        """
        prereq = self.build_file['build']['local_required']
        if not prereq:
            prereq = ['git']
        else:
            logging.debug('Searching for prerequisites...')

        if not isinstance(prereq, (list, tuple)):
            logging.warning('build.yaml build -> local_required must be a list')
            return


        command = PlatformDict.simple({
            'windows' : 'where',
            'unix' : 'which'
        })

        def _clean_path(p):
            d = p.decode('utf-8').replace("\r\n", "\n")
            d = d.split("\n")[0].replace("\\", "/")
            return d

        with log.log_indent():
            for requirement in prereq:
                proc = subprocess.Popen(
                    [command, requirement],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                information = proc.communicate()[0]
                if proc.returncode != 0:
                    logging.critical(
                        'Could not find prerequisite: {}'.format(requirement)
                    )
                    sys.exit(1)
                else:
                    if requirement == 'git':
                        continue # quite, this is always needed

                    logging.debug('{} found at: "{}"'.format(
                        requirement,
                        _clean_path(information)
                    ))


    def _build_commands(self, condition, build_data, type_):
        """
        General method for 
        """
        if build_data:

            ok = condition is None  # False if conditions required
            if condition:
                logging.debug('Checking {} Build Conditions...'.format(type_))

                if not isinstance(condition, (list, tuple)):
                    condition = (condition,)

                # http://book.pythontips.com/en/latest/for_-_else.html
                for c in condition:
                    if c not in self._additional:
                        break;
                else:
                    # We're good to run!
                    ok = True

            if ok:
                logging.debug('Start {} Build Execution...'.format(type_))
                parser = BuildCommandParser(
                    build_data, self.build_file, self._additional
                )

                try:
                    parser.exec_()
                except Exception as e:
                    logging.critical('Encountered a critical failure!')
                    with log.log_indent():
                        list(map(logging.critical, traceback.format_exc().split('\n')))
                    sys.exit(1)



    def _pre_build_commands(self):
        """
        Using the build file, identify if we have any commands to process
        with our environment and then do it!
        :return: None
        """

        logging.debug(':Pre Build:')
        with log.log_indent():

            build_descrpitor = self.build_file['build']

            condition = build_descrpitor['pre_build_conditions']
            pre_build = build_descrpitor['pre_build']
            self._build_commands(condition, pre_build, 'Pre')


    def _post_build_commands(self):
        """
        Using the build file, identify if we have any commands to process
        with our environment and then do it!
        :return: None
        """
        build_descrpitor = self.build_file['build']

        logging.debug(':Post Build:')
        with log.log_indent():

            build_descrpitor = self.build_file['build']

            condition = build_descrpitor['post_build_conditions']
            post_build = build_descrpitor['post_build']
            self._build_commands(condition, post_build, 'Post')