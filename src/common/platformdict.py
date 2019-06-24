"""
Utility dictionary
"""
from __future__ import absolute_import

import os
import platform
from copy import deepcopy

_this_platform = platform.system()
_is_unix = _this_platform in ['Linux', 'Darwin']

class PlatformDict(object):
    """
    Dictionary proxy that auto-routes based on platform.

    :example:

        my_map = {
            'foo' : {
                'Windows' : 'some_val',
                'Linux' : 'another_val'
            }
        }
        my_pfd = PlatformDict(mp_map)
        print (my_pfd['foo'])

        # On Windows:
        >>> some_val

        # On Linux:
        >>> another_val

    This can also recurse (although you shouldn't really need it to)

    :example:

        my_fpd = PlatformDict({
            'foo' : { 'Windows' : { 'bar' : 'Windows' : 'baz' } }
        })

        print (my_pfd['foo']['bar'])
        # On Windows
        >>> baz

    For unix systems (e.g. platform.system() in ('Linux', 'Darwin')), you
    can use the 'unix' key to represent both.

    :example:

        my_fpd = PlatformDict({ 'foo' : { 'unix' : 'bar', 'windows': 'baz' } })

        print (my_fpd['foo'])
        # On both Linux and macOS
        >>> bar

    :WARNING: This will return None for missing keys rather than raise
    an error!

    :Note: The platform names are semi-case sensitive. For keywords stick
    to first capital or all lower (e.g. 'Unix' or 'unix' (NOT 'UNIX'))
    """
    def __init__(self, og_dict = {}):
        if not isinstance(og_dict, dict):
            raise LaunchJsonError('Build/Launch data must be a dictionary!')
        self.__d = og_dict


    def __get_dict_entry(self, val):
        if _this_platform in val:
            val = val[_this_platform]
        elif _is_unix and 'unix' in val or 'Unix' in val:
            val = val[('unix' if 'unix' in val else 'Unix')]
        else:
            val = val.get(_this_platform.lower(), val)
        if isinstance(val, dict):
            return PlatformDict(val)
        return val


    def __getitem__(self, key):
        val = self.__d.get(key, None)
        if isinstance(val, dict):
            val = self.__get_dict_entry(val)
        return val


    def __setitem__(self, key, value):
        self.__d[key] = value


    def __iter__(self):
        return self.__d.__iter__()


    def __str__(self):
        return str(self.__d)


    def __deepcopy__(self, memo=None):
        return PlatformDict(deepcopy(self.__d))


    @classmethod
    def simple(cls, dct):
        """
        Given a simple dictionary of { platform : value, }, return
        the value of the active platform
        :param dct: dict
        :return: variant (PlatformDict if dictionary is value)
        """
        return cls({'_' : dct})['_']


    def to_dict(self):
        """
        :return: internal python dict object
        """
        return self.__d


    def update(self, other_mapping):
        """
        Typical dictionary update call
        """
        self.__d.update(other_mapping)


    def items(self):
        """
        Generator to iterate through
        """
        from common import utils
        for k,v in utils._iter(self.__d):
            if isinstance(v, dict):
                v = self.__get_dict_entry(v)
            yield (k,v)


    def iteritems(self):
        """
        Py2 compat
        """
        return self.items()
