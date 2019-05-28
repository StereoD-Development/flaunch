"""
CMake specific build manager
"""

from build import manage

class CmakeBuilder(manage.BuildManager):
    """
    CMake specific build manager
    """
    alias = 'cmake'

    def build(self):
        """
        Time to build...
        """
        pass


manage.BuildManager.register(CmakeBuilder)
