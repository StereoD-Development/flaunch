#################
Build Command API
#################

.. autoclass:: build.command._BuildCommand
  :members: description, populate_parser, run, data, get_command

****************
Current Commands
****************

Basic Commands
==============

.. class:: build.commands.basic.CopyCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.basic import CopyCommand
    CopyCommand()._parser.print_help()

.. class:: build.commands.basic.MoveCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.basic import MoveCommand
    MoveCommand()._parser.print_help()

.. class:: build.commands.basic.PrintCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.basic import PrintCommand
    PrintCommand()._parser.print_help()

.. class:: build.commands.basic.SetCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.basic import SetCommand
    SetCommand()._parser.print_help()

.. class:: build.commands.basic.EnvCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.basic import EnvCommand
    EnvCommand()._parser.print_help()

.. class:: build.commands.basic.FailCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.basic import FailCommand
    FailCommand()._parser.print_help()

.. class:: build.commands.basic.ReturnCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.basic import ReturnCommand
    ReturnCommand()._parser.print_help()

File I/O
========

.. class:: build.commands.fileio.WriteCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.fileio import WriteCommand
    WriteCommand()._parser.print_help()

.. class:: build.commands.fileio.ReadCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.fileio import ReadCommand
    ReadCommand()._parser.print_help()

.. class:: build.commands.fileio.MkDirCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.fileio import MkDirCommand
    MkDirCommand()._parser.print_help()

.. class:: build.commands.fileio.DelCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.fileio import DelCommand
    DelCommand()._parser.print_help()

.. class:: build.commands.fileio.ZipCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.fileio import ZipCommand
    ZipCommand()._parser.print_help()

Execution
=========

.. class:: build.commands.execute.PythonCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.execute import PythonCommand
    PythonCommand()._parser.print_help()

.. class:: build.commands.execute.FuncCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.execute import FuncCommand
    FuncCommand()._parser.print_help()

.. class:: build.commands.execute.SuperCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.execute import SuperCommand
    SuperCommand()._parser.print_help()

Deployment Commands
===================

.. class:: build.commands.deployment.DeploymentCommand

  .. note::

    This is a specialty command for deploying files via flaunch
    and it's network. Not for use in "everyday" commands.

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.deployment import DeploymentCommand
    DeploymentCommand()._parser.print_help()

Testing Commands
================

.. class:: build.commands.testing.PyCoverageCommand

  .. execute_code::
    :hide_code:
    :hide_headers:

    from build.commands.testing import PyCoverageCommand
    PyCoverageCommand()._parser.print_help()