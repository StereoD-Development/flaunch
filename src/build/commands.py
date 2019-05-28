"""
Custom commands that can be run cross-platform by dealing with
the crosplatformness for us
"""

from common import utils

class _BuildCommand(object):
    """
    Abstract build command. Overload per-command
    """
    alias = None
    def __init__(self, ):
        pass

class CopyCommand(_BuildCommand):
    alias = 'COPY'
    def __init__(self, src, dst):
        pass


class MoveCommand(_BuildCommand):
    alias = 'MOVE'
    def __init__(self, src, dst):
        pass


class PrintCommand(_BuildCommand):
    aliad = 'PRINT'
    def __init__(self, text):
        pass