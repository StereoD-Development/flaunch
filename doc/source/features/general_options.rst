***************
General Options
***************

Each section in our build yaml (``build:``, ``delpoy:``, ``test:`` etc.), handles a few additional keywords for managing your build.

.. glossary::

    ``local_required``
        A list of required application that the build tools must be able to use from the commands line. On Windows this runs ``where <command>`` while posix will execute ``which <command>``. If no error code comes back it is assumed to be reachable.

.. code-block:: yaml

     local_required:
       windows:
         - 7z
         - msbuild
       unix:
         - zip
         - make

.. note::

    If you required select python modules, you can prepend the requirement with ``py::`` to have ``fbuild`` test for the existence of the package/module.

    .. code-block:: yaml

        local_required:
            - py::yaml   # python required
            - py::purepy # python required
            - cmake      # binary required
