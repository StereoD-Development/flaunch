"""
Simple string expressions
"""
from __future__ import absolute_import

from . import utils

@utils.add_metaclass(utils.SimpleRegistry)
class _StringExpression(object):
    """
    Virtual class for implementing a string expression.

    Subclass this to dynamically add expressions. Simply add an alias and
    overload the run(value) command.

    .. code-block:: python

        class TwiceExpression(_StringExpression):
            alias = 'tw'

            def run(self, value, *args):
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
    

    def run(self, value, *args):
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
        args = []
        search_alias = alias.strip()
        if '(' in alias:
            search_alias = alias[:alias.index('(')]
            # This needs work... start here...
            args_string = alias[alias.index('(') + 1: -1]

            # Mini parse for arguments - can probably move this to a more
            # robust setup - maybe even argparse because why not/
            current_arg = ''
            last_index = len(args_string) - 1

            in_quote = False
            quoute_char = ''
            escape_char = False

            for i, char in enumerate(args_string):
                if char == '\\' and not escape_char:
                    escape_char = True
                    continue

                if not escape_char:
                    if char in ('"', "'"):
                        if char == quoute_char:
                            in_quote = False
                            quoute_char = ''
                        else:
                            in_quote = True
                            quoute_char = char
                else:
                    escape_char = False

                if char == ',' and current_arg and not in_quote:
                    args.append(current_arg)
                    continue

                if char == ' ' and current_arg == '' and not in_quote:
                    continue

                current_arg += char

                if i == last_index and current_arg:
                    args.append(current_arg)

        if not search_alias in cls._registry:
            raise ValueError('The expression: "{}" does not exist!'.format(search_alias))
        return cls._registry[search_alias](launch_data).run(value, *args)



class ForwardSlashExpr(_StringExpression):
    """
    Convert \\ slashes to /
    """
    alias = 'fs'

    def run(self, value, *args):
        return value.replace('\\', '/')


class BackSlashExpr(_StringExpression):
    """
    Convert / slashes to \\
    """
    alias = 'bs'

    def run(self, value, *args):
        return value.replace('/', '\\\\')


class LowercaseExpr(_StringExpression):
    """
    lowercase the value
    """
    alias = 'low'

    def run(self, value, *args):
        return value.lower()


class UppercaseExpr(_StringExpression):
    """
    Uppercase the value
    """
    alias = 'upp'

    def run(self, value, *args):
        return value.upper()


class CapitalizeExpr(_StringExpression):
    """
    Capitalize the value
    """
    alias = 'cap'

    def run(self, value, *args):
        return " ".join(w.capitalize() for w in value.split())


class TrimExpr(_StringExpression):
    """
    Trime the string of leading and trailing whitespace
    """
    alias = 'trim'

    def run(self, value, *args):
        return value.strip()


class TruncateExpr(_StringExpression):
    """
    Truncate a string based on the arguments supplied.
    trunc(<count>, <from_start>=False)
    """
    alias = 'trunc'

    def run(self, value, *args):
        if not args:
            return value
        
        try:
            count = int(args[0])
        except ValueError as err:
            # Some kind of loggin?
            return value

        if len(args) > 1 and args[1] not in ('False'):
            return value[count:]
        return value[:count]


class ReplExpr(_StringExpression):
    """
    Replace a given chunk of text.
    repl(<replace>, <with>, <count>=None)
    """
    alias = 'repl'

    def run(self, value, *args):
        if not args:
            return value

        print ("args", args)

        count = None
        if len(args) == 3:
            try:
                count = int(args[2])
            except ValueError as err:
                return value
            except IndexError as err:
                return value

        if count:
            return value.replace(args[0], args[1], count)
        return value.replace(args[0], args[1])


class JoinExpr(_StringExpression):
    """
    Join a list of values into a common string
    join(<sep>)
    """
    alias = 'join'

    def run(self, value, *args):
        if not args:
            return ''.join(value)
        return args[0].join(map(str, value))


class QuoteExptr(_StringExpression):
    """
    Quote a given string with the provided char(s)
    quoute(<char>='"')
    """
    alias = 'quote'

    def run(self, value, *args):
        char = '"'
        if args:
            char = args[0]
        return '{}{}{}'.format(char, value, char)


class CountExpr(_StringExpression):
    """
    Given an iterable, return the number of items.
    """
    alias = 'count'

    def run(self, value, *args):
        return str(len(value))


class Dirname(_StringExpression):
    """
    Given a string, run os.path.dirname on it
    """
    alias = 'dirname'

    def run(self, value, *args):
        import os
        return os.path.dirname(value)