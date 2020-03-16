
***********************
Pre and Post Operations
***********************

When executing, we may want to run some tasks before and after our procedure. This can be done using :ref:`Command Lists`.

.. note::

  Go read up on :ref:`Command Lists`! They're pretty cool! And they will come in handy. Not to mention this next part won't make any real sense until you do.

Once you have a basic grasp on how commands work, take a look at the following example.

.. code-block:: yaml

  props:
    put_foo_here:
      windows: C:/temp
      unix: /tmp

    use_email: foo@mycomp.com

    send_email_script: |
      import sendmail
      sendmail(email={use_email}, "Build for {package} on {platform} completed!")

  build:
    type: basic

    # -- Pre Build Work
    #
    # Copy a file, read said file into a prop, and then print it out
    # to the user
    #
    pre_build_condition: --run-prebuild
    pre_build:

      - ":COPY -m -f {source_dir}/src/some_info.txt {put_foo_here}/foo.txt"
      - ":READ {put_foo_here}/foo.txt read_data"

      # "echo {read_data}" would also be the same
      - ":PRINT {read_data}"

    # No commands: provided means fbuild will just copy source files to the build dir

    # -- Post Build Work
    #
    # Send an email if the environment variable SEND_EMAIL is set to "True"
    #
    post_build:
      - clause: 'env_set("send_email")'
        commands:
          - ":PYTHON send_email_script"

There's a lot going on there but it's quite useful for handling many of our usual tasks without having to write multiple scripts to do so.

.. glossary::

  ``pre_build_condition``
    A basic condition that looks for an argument in our initial ``fbuild`` command.
      * In the example, ``fbuild`` will look for ``--run-prebuild``

  ``pre_build``
    A Command List that we'll execute if ``pre_build_condition`` is null, not provided, or resolves to true.
      * In the example, we have a few ``fbuild`` commands that copy a file, read said file into a property, and then print that to our user

  ``post_build_condition``
    A basic condition that looks for the argument in our initial ``fbuild`` command
      * In the example, we didn't provide this so it will always resolve to ``True``

  ``post_build``
    A Command List that we'll execute if ``post_build_condition`` is null, not provided, or resolves to true.
      * In the example, we have a dictionary command that checks is an environment variable is set by using the built in function `env_set`


Other fbuild Commands
=====================

Most commands have the ``pre_<command>`` and ``post_<command>`` handles. (e.g. ``pre_deploy:``/``post_deploy``). The only command that doesn't follow this paradigm is ``fbuild prep``