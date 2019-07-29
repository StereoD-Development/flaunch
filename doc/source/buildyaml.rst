***************
Building Blocks
***************

**Polymorphism, meet DevOps**

The ``fbuild`` framework helps merge the worlds of building a package, testing it in development and production environments, along with deployment when required.

At the heart of `flaunch` packages is the ``build.yaml`` files and our utility of them.

Rather than creating complicated python build scripts for everything or handling much of the same code over and over, we use a simple yaml file that can handle both basic file organization as well as dynamic builds and pre/post process procedures.

Starting Out
============

Let's build a simple package to work with ``fbuild``.

.. note::

  To use ``fbuild``, you'll need a yaml parser. Use ``pip install PyYAML`` to obtain one.

The Package
-----------

Let's say we have the follow package structure:

.. code-block::

    MyPackge
        `- MyPackage
            `- __init__py

And inside the `__init__.py` file, we have the following:

.. code-block:: python

  import decimal  # default python lib

  def dollars_from_cents(cents):
      decimal.getcontext().prec = 2
      return decimal.Decimal(0.01) * descimal.Decimal(cents)

Now we want to hook it up to ``flaunch`` for use with other packages and applications. To do so, let's create a ``build.yaml`` file on the top directory.

The build.yaml
--------------

.. code-block:: yaml

  # build.yaml

  name: MyPackage # The name of our package

  # -- The build procedure
  build:
    type: basic

.. note::

  That's the absolute minimum ``build.yaml`` file there is. Odds are you'll be creating one with a bit more complexity.

So our structure should look like this:

.. code-block::

  MyPackage
      `- MyPackage/
      `- build.yaml

Once we have that, and we're looking to build our package, we head to the command line. To use ``fbuild`` you'll want to set the following environment variables:

.. code-block:: shell

  export FLAUNCH_BUILD_DIR=<default location you want to build packages>
  export FLAUNCH_DEV_DIR=<default location your source files exist in (e.g. your local git repo)>

In this case, ``FLAUNCH_DEV_DIR`` will be set to the directory above the *root* ``MyPackage``.

.. note::

  Check out the :ref:`Set your Environment` section to understand all available environment variables!

These two can be overwritten by the ``fbuild`` command but for now, with them set, we can build our package.

.. note::

  Make sure you have the flaunch and fbuild location added to your PATH environment variable otherwise the cli may not work.

.. code-block::

  fbuild MyPackage

With that we get a bit of information:

.. code-block:: shell

  [28/05/2019 01:30:59 PM - INFO]: Build Path: C:/repo/build/MyPackage
  [28/05/2019 01:30:59 PM - INFO]: Create Build Directory...
  [28/05/2019 01:30:59 PM - INFO]: Copying Files...
  [28/05/2019 01:30:59 PM - WARNING]: launch.json file not found! Expect issues when launching!
  [28/05/2019 01:32:11 PM - INFO]: Build Complete

This tells us that the build completed! You should be able to find the build files within the ``FLAUNCH_BUILD_DIR`` you defined earlier.

launch.json
-----------

You may have noticed the ``WARNING`` we received while building. The ``launch.json`` file wasn't included within our package and so ``flaunch`` won't be able to use it.

A ``launch.json`` file describes how we interact with a package. Some things this file handles:

- Listing other packages this package relies on
- Prepping an environment
- Executable path for using the ``launch`` command

We'll get into more details surrounding the ``launch.json`` soon but, for now, let's get one in our package for use.

At this point you have two options:

1. Add a ``launch.json`` file to the root of your package
2. Add a ``launch_json`` argument to the build section of the ``build.yaml`` file.

For the second option, your build.yaml might look like the following:

.. code-block:: yaml

  name: MyPackage

  build:
    type: basic

    #
    # Basic dictionary that will map to our launch.json
    #
    launch_json:
      env:
          PATH: ["{path}"]

With this, we run ``fbuild MyPackage`` and we shouldn't see the ``WARNING`` anymore. You'll also notice that a ``launch.json`` file was created for you in the build directory with the ``"env"`` key.

.. note::

  Use ``fbuild -v <package>`` to see all debug information

Run Our Build
-------------

What's the point of building it if we can't actually use it? Let's give the python interpreter a shot.

.. code-block::

  flaunch --package MyPackage/dev --run python

Now you should have a python interpreter running from which you can use your package freely.

.. warning::

  Mixed Python Paths! It's a good idea to run the flaunch command from outside the source files to make sure your python interpreter isn't using your current working directory, which would use the source files by default. This really only applies to scripting languages.

Once you have the interpreter running you should be able to do something like:

.. code-block:: python

  >>> from MyPackage import dollars_from_cents
  >>> print (dollars_from_cents(1000))
  10.0
  >>>

Now we have a (re)build-able environment that we can modify, build out of source, and test with!

Next Steps
==========

Now that we have some of the basics down, let's talk about some of the features within our ``build.yaml``.

Variable Expansion
------------------

Because builds are often complex, we have made sure ``build.yaml`` and ``launch.json`` are template-able, and have many ways of reducing the overhead between platforms and packages.

Arguably the most vital feature is variable expansion. By using the syntax of ``{<keyword>}``, we declare to the toolkit that we want it to search our current environment, and possibly ``props:``, for the value to inject.

Given the following:

.. code-block:: yaml

  proper_dir: {home}/bar

The toolkit, on Unix platforms, would convert that to ``/home/<my_username>/bar``

Special Keywords
^^^^^^^^^^^^^^^^

It's worth noting that some values are baked into the ``build.yaml`` system

- ``{path}``: Path to the package (source files for ``build.yaml`` and package dir for ``launch.json``)
- ``{platform}`` : Python platform.system() that the command is being run from
- ``{package}`` : Name of this package
- ``{source_dir}`` : The directory our code is in
- ``{build_dir}`` : The directory our build will be placed into

Recursive Expansion
^^^^^^^^^^^^^^^^^^^

This expansion process is even recursive.

.. code-block:: yaml

  first_var: {second_var}/foo
  second_var: hard_value

  # ...

  third_var: {first_var}/bar
  # third_var == hard_value/foo/bar

This means you can get very in depth with your variable control. Just be careful not to introduce a cyclic dependency. ``fbuild`` will detect this and fail immediately.

Platform Routing
----------------

In the example above, we used ``{home}/bar`` which searched our environment for ``HOME`` and expanded as needed. This will work fine for Unix machines but won't work on Windows unless we set the environment variable ourselves (or pass it to props).

For both the ``build.yaml`` and ``launch.json``, the dictionary they build will "auto route" based on the platform you're using. This is based on the ``import platform; platform.system()`` that python returns.

So let's augment our example from above:

.. code-block:: yaml

  proper_dir:
    windows: {homepath}/bar
    linux: {home}/bar
    darwin: {home}/bar

This will now expand properly for all three platforms.

.. note::
  
  Platform routing can be used *anywhere*! You can even use it to change the build type if required. (Although that is a little crazy)

Unix
^^^^

.. note::

  Because Linux, macOS, and other posix systems are typically a similar processes, you can use `unix` as a representation for any unix machine.

props:
------

The root of our ``build.yaml`` can contains a ``props:`` key which should point to a dictionary of additional data we may need while building and can be used for :ref:`Variable Expansion`.

.. code-block:: yaml

  name: MyPackage

  props:
    tar_command:
      windows: 7z
      unix: tar

  build:
    type: basic

    commands:
      - {tar_command} -cvf my_file.tar.gz some_folder/

In this example, as ``fbuild`` does the build, ``{tar_command}`` will expand to the ``prop: tar_command`` of which that value will be based on the platform we're building with. Awesome!

A Note On Paths
^^^^^^^^^^^^^^^

Paths are complicated and often a pain point for development routines. When writing ``build.yaml`` files, *always* use forward slashes (``/``) to allow for simpler parsing and common, readable code.

Command Lists Building
----------------------

When we are building, deploying, managing, etc., we're usually just running command after command and changing a few things based on the platform we're running with, and the particulars of a software package. That's why we've come up with the :ref:`Command Lists`.

These are so important it gets it's own doc. Read up on them to get the full effect of what ``fbuild`` can do for your devops optimization.

General Options
---------------

The `build:` section, no matter what ``type:`` you need, handles a few additional keywords for managing your build.

- ``launch_json``: The launch json dictionary that we want to use (see :ref:`above <launch.json>`)
- ``local_required``: A list of required application that the build tools must be able to use from the commands line. On Windows this runs ``where <command>`` while posix will execute ``which <command>``. If no error code comes back it is assumed to be reachable.

.. code-block:: yaml

     local_required:
       windows:
         - 7z
         - msbuild
       unix:
         - zip
         - make


Pre and Post Operations
-----------------------

When executing, we may want to run some tasks before and after our build procedure. This can be done using :ref:`Command Lists`.

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
      - ":PRINT {read_data}" # "echo {read_data}" would also be the same

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

Templates and Functions
-----------------------

We often have similar build/deployment requirements between packages. This can be tedious if you're writing the same commands over and over and again for each subsequent package.

``fbuild`` deals with this through two interfaces.

1. The :ref:`:FUNC Command`
2. Templates

.. _buildyaml-templates:

A Template
^^^^^^^^^^

The basic concept is a template is an "overload-able" ``build.yaml`` file that you can overload by including it inside of your specific ``build.yaml``. Deriving from a template is declared with the ``include:`` keyword.

So, given the template ``my_build_template.yaml``

.. code-block:: yaml

  props:
    # We often mark "private" properties with a '_'
    _server_location:
      windows: //isilon2
      unix: /mnt/isilon2

    _platform_arch:
      windows: AMD64-Windows
      linux: x86_64-Linux

    _extra_build_dir: {_server_location}/deployments/{_platform_arch}

  func__build_template_post():
    - ":DEL {_extra_build_dir}/*"
    - ":MKDIR {_extra_build_dir}"
    - ":COPY -f {build_dir}/* {_extra_build_dir}"

  build:
    
    # This is all that we overload
    post_build:
      - ["--extra-build", "build_template_post()"]

Then, our actual ``build.yaml`` file could look something like:

.. code-block:: yaml

  name: MyDerivedBuild

  include:
    - my_build_template

  props:
    local_setting: true

  build:
    type: basic

    files:
      - docs
      - src

    launch_json:
      env:
        PATH: ["{path}"]

Now, when we build:


.. code-block::

  fbuild -v MyDerivedBuild

Nothing would happen! That's because the plugin ``post_build`` command looks for the argument ``--extra-build``.

.. code-block::

  fbuild -v MyDerivedBuild --extra-build

The ``include`` option is a list so multiple deriving from multiple templates is possible, and because this is ``build.yaml``, you can even template based on platform. Sky's the limit.

.. note::

  The order of include is important. The overloading of values will continue from the first to the last. So if package ``a`` includes template ``b`` and ``c`` in that order, ``a`` will take precedence, followed by ``c``, and then ``b``

.. warning::

  **All** ``build.yaml``\ 's have the ``global.yaml`` template as a base, even if not explicitly marked. This provides a common ground for all packages but can be completely ignored/overloaded when required.

Raw Command Building
--------------------

Intense pipelines often present the desire for automation outside of just building and deployment. For this reason, we've included ``raw`` commands to help execute arbitrary commands.

:ref:`Raw Command Documentation <Raw Commands>`

Deployment
----------

This get it's own :ref:`document <Deployment and Release>`

Build Types Docs
----------------

:ref:`Build Types`
