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

We can initialize this project with a simple ``fbuild`` command.

.. note::

  Make sure you have the flaunch and fbuild location added to your PATH environment variable otherwise the cli may not work.

.. code-block:: shell

  ~$> cd <code_repo>
  ~$> fbuild init
  # ...

That should get you started with a ``build.yaml``. It should look something like:

.. code-block:: yaml

  #
  # The MyPackage build.yaml
  #

  # The name of the package
  name: MyPackage

  # The build procedure
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

If you're wondering where the commands are for the actuall build, check out the :ref:`Basic build type <Basic>`.
