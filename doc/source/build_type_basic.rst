###########
Build Types
###########

*****
Basic
*****

The simplest build type but also the most flexible. Be default it's just a copy machine for files in your source directory but can be controlled at a command level.

When using the build type ``basic``, you have the following options available to you:

The Default
===========

When the ``commands`` keyword isn't provided the default setup for the command will simply copy the files from the source directory to the build directory. This is usually enough for basic python packages for things like third party integrations and otherwise.

File Copy Management
--------------------

When using the copy mechanism, you can provide a few keywords to help weed out/in what files you want to include.


.. glossary::

    ``files``
        A list of files that you want to include. This can be both files and directories.

    ``exclude``
        A list of files that ``fbuild`` will exclude from the source. This also takes unix matching patterns (e.g. ``*.pyc``) to help avoid a long list of files.

    ``prefix_dir``
        A directory (or slash seperated directory list) that files will go into under the ``build_dir``.

    ``use_gitignore``
        (bool) By default ``fbuild`` will search your source directory for a ``.gitignore`` file and utilize that for finding ignore patterns when copying files. If you want to forgo this behavior, set this to ``false``

Custom Commands
---------------

You can also forgo the basic file copy and simply use the ``commands`` keyword to run a [Command List](build_commands.md).

* ``commands`` : Command List that ``fbuild`` will process over copying files.
