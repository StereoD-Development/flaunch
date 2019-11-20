*************
Command Lists
*************

Another vital and powerful feature of ``fbuild`` is it's rich command tools. By abstracting some components into easy-to-use commands, while leaving the ability to run raw command line expressions, you can get the most out of the build technology without having to have a different build procedure for each platform.

The Syntax
==========

A Command List is, unsurprisingly, a list of commands that we want to execute. A "Command" in this context *isn't* just a command line operation but potentially a tree of possible code paths to follow.

Basic Command
-------------

.. code-block:: none

  COMMAND_LIST = [ "<command>", ... ]

Let's start by just looking a simple set of commands:

.. code-block:: yaml

  - "echo This is a Command"
  - "echo Another command!"

Here, we run the first command, which pushes ``"This is a Command"`` to the stdout. Then, after completing that task, we move to the second which pushes the next command. All of this is as though you ran each command by hand in a terminal.

Argument Conditional Commands
-----------------------------

.. code-block:: none

  - [ "<required_argument>", COMMAND_LIST (True), COMMAND_LIST (False) ]

Now, let's say we only wanted to run select commands when a select argument was passed to our command:

.. code-block:: yaml

  - "echo I'll go no matter what!"
  - [ "--some-arg",
      [
          "echo I'll need an arg to run!",
          "echo I too am just another Command List!"
      ]
    ]

This command will always print out ``"I'll go no matter what!"`` but, unless ``--some-arg`` is passed to the command line of ``fbuild``, the additional commands are not going to happen!

You'll notice that this command type takes an additional ``COMMAND_LIST``. In the event the ``<required_argument>`` is not present and the additional list is available, those commands will be run. Think of this as a simple ``if``/``else`` block. 

Clause Conditional Commands
---------------------------

.. code-block:: yaml

  - clause: <python_evaluated_clause>
    commands: COMMAND_LIST
    else_commands: COMMAND_LIST


This is a conditional execution that takes in a string an evaluates it to determine in the branch should be run. This is for basic checks only and cannot run full scripts (see the ``:PYTHON`` command for that).

.. code-block:: yaml

  - clause: "env_set('MY_ENV_VARIABLE')"
    commands:
      - echo "That env was set"
      # ...
    else_commands:
      - echo "That env was _not_ set!"


This command will use the provided function ``"env_set()"`` to determine if the environment variable has any value. If it does, then the command list within ``commands`` is run.

Currently, the provided functions are:

- ``env_check(var, val)`` : Check if an environment variable is set to a specific value
- ``env_set(var)``: Check if an environment variable is set to anything
- ``prop_set(var)``: Check if our `build.yaml` has a specific property set
- ``file_exists(var)``: Check if a file at a given path exists

.. code-block:: yaml

  - clause: '"{my_variable}" == "the_right_value"'
    commands: echo "That's the right variable value!"

This, while getting into :ref:`Variable Expansion`, will resolve to check two strings value and, if right, will run the following ``echo`` command. Notice that the ``else_commands`` is optional.

Platform Routing Everywhere
---------------------------

Because this is ``build.yaml`` - *any* *time* you want to route based on platform, you are allowed to do so. Command Lists are no exception.

.. code-block:: yaml

  - "echo foo"
  - windows:
      "echo I AM WINDOWS!"
    unix:
      "echo I AM _NOT_ WINDOWS!"


fbuild Commands
===============

.. code-block:: shell

  :<COMAND_NAME> <COMMAND_ARG>...


On top of having access to your terminal from the build process, you have a small but mighty suite of additional commands at your disposal. For general actions like writing/reading from a file, to copying/moving files in a platform agnostic way.

What's more, is command plugins can be made to suit your pipelines specific needs should a problem present itself.

An fbuild Command is used by starting with a ``:`` and followed by the alias to the command itself.

.. code-block:: yaml

  props:
    my_script: |
      x = "{version_information}"
      x = x.strip()
      if int(x[0]) >= 1:
          print ("Version is above 1!")

  # ...
    commands:
      - ":READ C:/code/project/version.txt version_information"
      - ":PYTHON my_script"
      - ":PYTHON -f C:/code/project/another_script.py"


There's a lot going on there, but hopefully it's pretty straight forward.

1. We fill our ``props:`` with a python script using yaml's multi line notation (\ ``|``\ )
2. Within the ``commands:`` of our process we have a few tasks

    1. ``:READ`` will read a file and push the contents of said file to a ``prop:`` so we can use it in later commands

    2. ``:PYTHON`` will execute python from a ``prop:`` variable that we've passed. ``my_script`` is first expanded upon, which resolves the ``{version_information}`` variable within the code

.. note::

  To find documentation on all native commands you can run the following:

  .. code-block:: shell

    fbuild command --doc

:PYTHON Command
---------------

When using the ``:PYTHON`` command and executing a ``prop:``, should you need a ``dict`` or ``set``, which would require ``{}``, then you need only put a space anywhere inside of the brackets. The expansion will ignore any captures with spaces in them.

For example:

.. code-block:: yaml

  # ...
    my_script: |
      username = 'My Cool Name'
      x = '{username}'

This resolve to something like:

.. code-block:: python

  usename = 'My Cool Name'
  x = 'John Doe'

By simply adding a space:

.. code-block:: python

  # ...
    my_script: |
      username = 'My Cool Name'
      x = {username }

You will get the desired results. Odds are this will be a very rare occurrence but worth noting none the less.

:SUPER Command
--------------

In the event we want to overload a proceedure or simple call another set of commands from a :ref:`template <buildyaml-templates>` we're overloading.

.. code-block:: yaml

  include:
    - some_package
  build:
    # ...
    commands:
      - ":PRINT foo"
      - ":SUPER some_package.build.commands"

This is akin to python's ``super()``

:FUNC Command
-------------

A useful command for refining your build procedure and componentalizing (not a word) your toolkit.

You define a function on your ``build.yaml`` root with the ``func__`` prefix. Something like:

.. code-block:: yaml

  func__my_function():
    # COMMAND_LIST

Then it's up to you what you want to do within that Command List. You can use all the same argument checking, clauses, etc. When you want to use it, simply call the ``:FUNC`` command

.. code-block:: yaml

  # ... Somewhere in a COMMAND_LIST
      - ":FUNC my_function()"

:FUNC Arguments
^^^^^^^^^^^^^^^

With the latest version of ``fbuild``, we've introduced arguments into functions.

You have the ability to provide through three interfaces.

1. Through ``props:``
    * This is pretty straight forward and allows you to provide different values as needed
2. Through the cli
3. Through the function call itself

For the second/third option, things get really interesting, let's look at an example

.. code-block:: yaml

  func__function_with_args(foo_bar, schmoo):
    - ":PRINT {foo_bar}"
    - ":PRINT {schmoo}"

Now that our function has arguments, we can supply them through the cli with a slight "converted" syntax. This systax simply prepends ``--`` and converts ``_`` to ``-``. For the example above the arguments would look like:

.. code-block:: shell

  ~$> ... --foo-bar the_first_value --schmoo another_value

We also support simply passing the arguments as you would in any other language

.. code-block:: yaml

  #...
  commands:
    - ":SET {some_expansion}/{my_file}.zip blarg"
    - ":SET {some_expansion}/{my_file}.tar.gz blarg_two"
    - ":FUNC function_with_args({blarg}, {blarg_two})" # Will expand and map accordingly

:RETURN Command
---------------

When working with COMMAND_LISTS and functions there may be a scenario where you need to return from the current scope

Comand Expansion (... Notation)
===============================

Occasionally, we have to handle command line arguments in a list fashion however, by default, any expanded varable is considered a single argument (``shlex.split()`` is run on the raw, unexpanded command which holds things like paths together but whitespace out of quote will delimit).

For example:

.. code-block:: yaml

  props:
    some_arguments: '-t foo -vvv --another-arg "blarg bloog"'

  # ...
    commands:
      - "mytool {some_arguments} {my_filename}.foo"

All seems well but when running those commands, the terminal would recieve:

.. code-block:: shell

  ["mytool"] ["-t foo -vvv --another-arg \"blarg bloog\""] ["the_filename.foo"]

No sensible parser would be able to understand that. To help with this, while using a ``COMMAND_LIST``, you can denote that you want to separate via an ``shlex.split()``.

.. code-block:: yaml

  # ...
    commands:
      - "mytool {some_arguments...} {my_filename}.foo"


Which translates to:

.. code-block:: shell

  ["mytool"] ["-t"] ["foo"] ["-vvv"] ["--another-arg"] ["blarg bloog"] ["the_filename.foo"]

Chaining Commands
=================

With all of these concepts, and the power of the ``build.yaml`` including Variable Expansion and Platform Routing we can generate very potent commands to fit our needs.


.. code-block:: yaml

  props:
    real_build_command:
      windows: mymake
      unix: unimake
    make_right_dirs: |
      import os
      for dir_suffix in ["one", "two", "three"]:
          fp = "{build_dir}/build_component_" + dir_suffix
          if not os.path.isdir(fp):
              oa.makedirs(fp)

  # ...

  build:
    type: basic

    pre_build:
      - [ "--clean-start", ":RM -r -f {build_dir}/*" ]
      - ":PYTHON make_right_dirs"

    commands:
      # We always build component one
      - ":CD {build_dir}/build_component_one"
      - "{real_build_command} {source_dir}/component_one/buildfile ."

      - windows:
          # Only build extra components on windows if the environment is set
          - clause: 'env_check("WINDOWS_BUILD_COMP_2", "True")'
            commands:
              - ":CD {build_dir}/build_component_two"
              - "{real_build_command} {source_dir}/component_two/buildfile ."

          - clause: 'env_check("WINDOWS_BUILD_COMP_3", "True")'
            commands:
              - ":CD {build_dir}/build_component_three"
              - "{real_build_command} {source_dir}/component_two/buildfile ."

        unix:
          # Unix doesn't currently build the extra components
          - ":PRINT Unix compatibility coming soon..."

This might look a little intense, but real world situations usually call for some pretty serious build strategies and the ``build.yaml`` is prepared to get the job done.

Creating Custom Commands
========================

``fbuild`` offers an API to expand the native abilities of the the custom commands through the ``_BuildCommand`` interface.

A Simple Example
----------------

.. code-block:: python

  from build.command import _BuildCommand

  class MyExecuteCommand(_BuildCommand):
      alias = 'MY_EXEC' # Command name

      def description(self):
          return "Custom execution protocol for my company"

      def populate_parser(self, parser):
          """
          Populate a argparse.ArgumentParser with the required
          arguments.
          """ 
          parser.add_argument(
              'script',
              help='The file to execute'
          )

          parser.add_argument(
              '-f', '--file',
              action='append',
              help='An output file to push log to'
          )

      def run(self, build_file):
          """
          The actuall execution takes place here.
          All parser arguments are stored in self.data
          """
          script = self.data.script
          if not os.path.exists(script):
              raise RuntimeError('The script "{}" does not exist!'.format(script))

          output_files = self.data.file

          # ... Run the script


This is a watered down command for executing a script and possibly routing it to multiple files. The syntax for this would be slightly different depending on your platform but the command list use of this could be made platform agnostic.

To access this command, you'll have to add the file it's in (e.g. ``~/extra_fbuild_commands/foo.py``) to the environment variable ``FLAUNCH_COMMANDS_PATH``. See :ref:`Set Your Environment` for more.

.. code-block:: yaml

  # Somewhere in a build.yaml
  - ":MY_EXEC {script_location}/my_script.py -f {output_file_a} -f {output_file_b}"

See the :class:`_BuildCommand <build.command._BuildCommand>` for more.
