************
Installation
************

Grab the Developer Source
=========================

If you're using a production machine, odds are you'll have access to the basic flaunch command but most of the key utilities for building are in the source files only.

Depending on which network you're on, you'll select the right repository:

Internal_

.. _Internal: http://git/flux/flaunch

External_

.. _External: https://github.com/StereoD-Development/flaunch

.. code-block:: shell

    ~$> git clone <repo_location>


Set Your Environment
====================

Mandatory Vars
--------------

The following environment variables are available.

.. glossary::

    ``FLAUNCH_DEV_DIR``
        The location of the packages you will build and manage. This is typically the location to your git repositor(ies)

    ``FLAUNCH_BUILD_DIR``
        The location that your want building to occur. We use this to build outside of source and keep the repositories clean where possible.

Optional Vars
-------------

The following environment variables are optional.

.. glossary::

    ``FLAUNCH_VERBOSE``
        Setting this to a "true" value (e.g. ``1``, ``on``, ``true``, ``True``, etc.) will enable the verbose output of commands as though the ``-v`` flag was passed

    ``FLAUNCH_COMMANDS_PATH``
        Paths (``__import__('os').pathsep`` delimited) that point to custom :ref:`fbuild Commands` which can be used when creating :ref:`Command Lists`

    ``FLAUNCH_CUSTOM_INDEX``
        By default, ``flaunch`` and ``fbuild`` will attempt to look through various endpoints for the Flux backend to report to/work with. This defines an explicit index that should point at an atom backend (e.g. ``http://10.66.24.12``)
