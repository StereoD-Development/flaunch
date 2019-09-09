######################
Building Branches/Tags
######################

For main bulid machines, we're often concerned with a specific branch, tag, or hash of code. ``fbuild`` let's you auto-checkout the files required when building.


.. code-block:: shell

    ~$> fbuild --branch origin/master MyPackage
    # ...

.. code-block:: shell

    ~$> fbuild --tag 1.0.2.0023 MyPackage
    # ...

.. warning::

    Providing ``--branch`` or ``--tag`` will shash any changes on the current repo. Something to look out for if you're performing any deltas.

From Scratch
============

``fbuild`` *does* have the ability to clone and build a repo out the gates. It's not very well maintained as it's expected that the developer will clone what's required first.

.. code-block:: shell

    ~$> fbuild --git https://github.com/jdoe/MyPackage MyPackage
