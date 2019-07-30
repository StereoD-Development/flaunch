******************
Variable Expansion
******************

Because builds are often complex, we have made sure ``build.yaml`` and ``launch.json`` are template-able, and have many ways of reducing the overhead between platforms and packages.

Arguably the most vital feature is variable expansion. By using the syntax of ``{<keyword>}``, we declare to the toolkit that we want it to search our current environment, and possibly ``props:``, for the value to inject.

Given the following:

.. code-block:: yaml

  proper_dir: {home}/bar

The toolkit, on Unix platforms, would convert that to ``/home/<my_username>/bar``

Special Keywords
================

It's worth noting that some values are baked into the ``build.yaml`` system

- ``{path}``: Path to the package (source files for ``build.yaml`` and package dir for ``launch.json``)
- ``{platform}`` : Python platform.system() that the command is being run from
- ``{package}`` : Name of this package
- ``{source_dir}`` : The directory our code is in
- ``{build_dir}`` : The directory our build will be placed into

Recursive Expansion
===================

This expansion process is even recursive.

.. code-block:: yaml

  first_var: {second_var}/foo
  second_var: hard_value

  # ...

  third_var: {first_var}/bar
  # third_var == hard_value/foo/bar

This means you can get very in depth with your variable control. Just be careful not to introduce a cyclic dependency. ``fbuild`` will detect this and fail immediately.


String Expressions
==================

There is a small arsenal of expressions that can be applied to an expanded value through the ``|`` marker. If you've ever used Jijna, these are very similar.

.. code-block:: yaml

    my_variable = "foo"
    uppered_variable = "{my_variable|upp}"

For more information on these see the :ref:`String Expression API`.