"""
launch.json helper tools
"""

from __future__ import absolute_import

from . import log
from .platformdict import PlatformDict
from .abstract import _AbstractFLaunchData, FLaunchDataError

from .utils import merge_dicts

class LaunchJson(_AbstractFLaunchData):
    """
    Basic tool for handling launch.json files
    """
    def __init__(self, package, path):
        try:
            with open(path, 'r') as f:
                data = PlatformDict(json.load(f))
        except Exception as e:
            logging.error(path + ' - invalid json file')
            raise FLaunchDataError(str(e))

        _AbstractFLaunchData.__init__(self, package, path, data)


    def requires(self):
        """
        :return: list[str] of required packages
        """
        return self['requires'] or []


    def extends(self):
        """
        :return: str of package this one extends
        """
        return self['extends'] or None


    def default_args(self):
        """
        :return: list of default arguments
        """
        return self['default_args'] or None


    def set_base(self, base_ljson):
        """
        :param base_ljson: The LaunchJson that this instance overrides
        :return: None
        """
        self._path = base_ljson._path
        self._data = PlatformDict(
            dict(merge_dicts(base_ljson._data.to_dict(), self._data.to_dict()))
        )
