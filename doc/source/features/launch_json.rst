***********
Launch JSON
***********

While ``fbuild`` uses the ``build.yaml`` to control the developer environment, the ``launch.json`` file is used by ``flaunch`` in order to control the running command.

.. note::

    We use the JSON format for the client side as it comes standard with Python and it's a bit safer to run with.


An example ``launch.json``:

.. code-block:: json

    {
        "executable" : "python \"{path}/main.py\"",
        "env" : {
            "PATH" : ["{path}", "{path}/thirdparty"],
            "APP_ID" : "3d52-d24v-78cc-ee31-c13f"
        },
        "requires" : {
            "Windows" : [
                "AppBase"
            ],
            "Linux" : [
                "AppBase", "CompatLib/10.0.3.0240"
            ]
        }
    }


env
===

Most packages will want to affect the environment in some way. The ``env`` key is for doing just that. When adding environment variables, you can provide either a ``list[str,]`` of a ``str``.

list
----

If passing a list of strings, this will append the values together with any currently held value in the environment. So...

.. code-block:: json
    
    {
        "env" : {
            "PATH" : ["{path}"]
        }
    }

This will use :ref:`Variable Expansion` to resolve ``{path}`` and then append it to the current ``PATH`` value using the proper operating systems path split (e.g. ``:`` on Unix, ``;`` on Windows)

str
---

This will simple overload the value with whatever string is provided.

.. code-block:: json

    {
        "env" : {
            "MY_VAR" : "{package}_foo"
        }
    }

Variable Expansion still takes place but we set ``MY_VAR`` to that value explicitly.

.. warning::

    It's always frowned upon to set system default envrionment values (e.g. ``PATH``) to a string as it would clear away any binary lookup paths that may be required for later execution.


executable
==========

If your package can be run via ``flaunch``, you'll need this to tell the toolkit how to do so.

.. code-block:: json

    {
        "executable" : "python \"{path}/main.py\""
    }

This command will expand the command and execute. The ``main.py`` file with the path is surrounded in quotes to make sure we handle ``{path}`` to resolving with a space in it.


requires
========

If your package utilizes another package in order to run properly, this is where you would include that.


.. code-block:: json

    {
        "requires" : {
            "Windows" : [
                "AppBase"
            ],
            "Linux" : [
                "AppBase", "CompatLib/10.0.3.0240"
            ]
        }
    }

.. note::

    You'll notice this example uses an additional dictionary layer that contains platforms. This is for :ref:`Platform Routing` and, like the ``build.yaml``, it can be used *anywhere*.

This will resolve the required packages without us having to explicitly mark them in our ``flaunch`` command.


extends
=======

Templating is a powerful feature of ``build.yaml`` and we want to be sure that ``launch.json`` contains some of the same potency. With the ``extends`` key, you can select a package that you want this package to "inherit". This is useful for Composed launchers.

.. code-block:: json

    {
        "extends" : "BasePackage",
        "executable" : "\"{path}/mytool\""
    }

This could be a complete ``launch.json`` as it would extend ``BasePackage`` and inherit any settings from that.

.. warning::

    It's vital to note that ``{path}`` on an extended package is set to the **base** package and **not** the overloaded one.


default_args
============

Use this to set default arguments passed to the command if none are manually set. This is a ``list[str,]``


.. code-block:: json

    {
        "executable" : "python foo.py",
        "default_args" : ["--use-additional", "-r", "--file", "blarg.txt"]
    }

If we're to run this through ``flaunch`` without any arguments the defaults are used.

.. code-block:: shell

    ~$> flaunch -v SomePackage
    # ...
    # Running command: foo.py --use-additional -r --file blarg.txt

Otherwise, should we provide args:

.. code-block:: shell

    ~$> flaunch -v SomePackage --file boog.txt
    # ...
    # Running command: foo.py --file boog.txt
