*********
requires:
*********

The ``build.yaml`` root can contain the key ``requires`` to signify what packages may be needed when running a package.

.. code-block:: yaml

    name: MyPackage

    requires:
        - AnotherPackage

    build:
        type: basic

To save on additional commands, we can pass the ``-r`` flag when building ``MyPackage`` to have ``fbuild`` build ``AnotherPackage`` automatically.

.. code-block:: shell

    ~$> fbuild MyPackage -r

.. note::

    The long form arg of ``-r`` is ``--build-required``

Build Required Options
======================

The list of packages underneath ``requires`` is not just a package name but rather a command sequence to execute. This means you can add specific build options to each package.

.. code-block:: yaml
    
    name: MyPackage

    requires:
        - AnotherPackage --some-specific-arg {a_local_prop}

    build:
        type: basic

Again, this is ``build.yaml`` where :ref:`Variable Expansion` is *nearly* everywhere, so feel free!
