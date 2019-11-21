****************
Platform Routing
****************

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
----

.. note::

  Because Linux, macOS, and other posix systems are typically a similar processes, you can use `unix` as a representation for any unix machine.
