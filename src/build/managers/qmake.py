"""
QMake buid manager
"""
from __future__ import absolute_import

from build import manage

class QmakeBuilder(manage.BuildManager):
    """
    QMake specific build manager
    """
    alias = 'qmake'

    def build(self):
        """
        Time to build...
        """
        pass


manage.BuildManager.register(QmakeBuilder)
