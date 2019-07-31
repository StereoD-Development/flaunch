************
Raw Commands
************

Raw commands help devops do things outside the scope of just building and releasing. This is the "blank canvas" arena that gives to complete access to the ``fbuild`` toolkit without any direction.

.. code-block :: yaml

  # build.yaml

  # ...

  # Must belong to the "raw" section
  raw:

    custom_command:
      help: |
        A custom command that can be run at any time and even
        flows through the templating system for ease of use

      arguments:
        - [foo_bar, A required parameter to be passed in, "\\d+"]

      flags:
        - [addon, Optional flag for run additional code]

      # The COMMAND_LIST to run
      commands:
        - ":FUNC a_custom_command_that_takes_an_argument({foo_bar})"
        - ["--addon", ":PRINT safe to run more code"]

Given the above ``raw`` command, we can then access it through our ``fbuild raw`` interface.

.. code-block:: shell

  ~$> fbuild raw MyPackage custom_command 1234

Because this works in templates, it turns automation procedures into pseudo object oriented design.

Raw Command Options
===================


.. glossary::

  ``help``
    A string (possible multiple lines) that describes the command

  ``epilog``
    Additional help that's displayed after the arguments. A good place for an example command.

  ``arguments``
    Sequence of arguments. This can be a string of just the command name, or list. The list syntax is ``[<name>, <help>, <regex pattern to match>]``

  ``flags``
    Switches for this command. Not explicitly required but good for documentation. Each flag can be a string of list just like the arguments

  ``commands``
    The commands to run for this action following the same syntax as all [Command Lists](build_commands.md)

Optional Arguments
==================

Occasionally, you need to have an optional argument with a value. To add this, add an element to ``arguments`` and prefix the first value with ``--``.

.. code-block:: yaml

  # ...
      arguments:
        - [foo_bar, A required parameter to be passed in, "\\d+"] # Mandatory
        - ["--schmoo", An optional parameter with a value, "\\w+"] # Optional


``--schmoo`` can be omitted from the command but it requires a value if present, which differs from a ``flags`` element which is just a boolean switch.

Templates
=========

Because of ``flaunch``\ s robust template system, raw commands are usable in derived ``build.yaml`` files as expected.


Listing Available Commands
==========================

Use the ``--list-commands`` to get a full printout of ``raw`` commands available to your package.

.. code-block:: shell

  ~$> fbuild raw MyPackage --list-commands
  Raw commands for: MyPackage

  -----------------------------------------------

  >>> COMMAND: custom_command
  usage: custom_command [--docs] [--addon ADDON] foo_bar

  A custom command that can be run at any time and even flows through the
  templating system for ease of use

  positional arguments:
    foo_bar        A required parameter to be passed in

  optional arguments:
    --docs         Print this help information and exit
    --addon ADDON  Optional flag for run additional code

  -----------------------------------------------
  # ... Additional commands (if any) ...
