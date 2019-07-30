"""
Simple string expressions
"""
from __future__ import absolute_import

from . import utils

class StrExpressionRegistry(type):
    """
    A metaclass that builds a registry automatically
    """
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, '_registry'):
            cls._registry = {} # Base Class
        else:
            cls._registry[cls.alias] = cls


@utils.add_metaclass(StrExpressionRegistry)
class _StringExpression(object):
    """
    Virtual class for implementing a string expression.

    Subclass this to dynamically add expressions. Simply add an alias and
    overload the run(value) command.

    .. code-block:: python

        class TwiceExpression(_StringExpression):
            alias = 'tw'

            def run(self, value):
                return (value + value)

    This can even be utilized with the :ref:`:PYTHON Command` in a
    ``build.yaml`` file.

    .. code-block:: yaml

        # build.yaml

        props:

          my_value: "foo"

          define_new_expr: |
            from common.strexpr import _StringExpression
            class TwiceExpression(_StringExpression):
                # .. same as above

        raw:
          some_command:
            # ...
            commands:
                - ":PYTHON define_new_expr"
                - ":PRINT {my_value|tw}" # Run the custom string expression
    
    The expression instance has access to the launch data (BuildFile or LaunchJson)
    if required through the ``self.launch_data`` property
    """
    alias = None

    def __init__(self, launch_data):
        self._launch_data = launch_data


    @classmethod
    def _get_expressions_info(cls):
        output = ''
        for alias, cls_ in utils._iter(cls._registry):
            output += ' - ' + alias + ': \n'
            output += (' ' * 4) + cls_.__doc__.strip()
            output += '\n'
        return output[:-1] # Remove the last new line


    @property
    def launch_data(self):
        """
        :return: ``common.abstract._AbstractFLaunchData``
        """
        return self._launch_data
    

    def run(self, value):
        """
        Overload for each expression type
        """
        raise NotImplementedError("Must overload this run() on each expression")


    @classmethod
    def evaluate(cls, alias, value, launch_data):
        """
        Execute the evaluation. Called from the ``_AbstractFLaunchData`` while
        expanding values.

        :param alias: The alias of the expression
        :param value: The value that we're running our expresson on
        :param launch_data: ``common.abstract._AbstractFLaunchData``
        :return: str
        """
        if not alias in self._registry:
            raise ValueError('The expression: "{}" does not exist!'.format(alias))
        return self._registry[alias](launch_data).run(value)



class ForwardSlashExpr(_StringExpression):
    """
    Convert \\ slashes to /
    """
    alias = 'fs'

    def run(self, value):
        return value.replace('\\', '/')


class LowercaseExpr(_StringExpression):
    """
    lowercase the value
    """
    alias = 'low'

    def run(self, value):
        return value.lower()


class UppercaseExpr(_StringExpression):
    """
    Uppercase the value
    """
    alias = 'upp'

    def run(self, value):
        return value.upper()

