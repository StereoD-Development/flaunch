******
props:
******

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