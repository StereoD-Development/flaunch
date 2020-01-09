***********************
Templates and Functions
***********************

We often have similar build/deployment requirements between packages. This can be tedious if you're writing the same commands over and over and again for each subsequent package.

``fbuild`` deals with this through two interfaces.

1. The :ref:`:FUNC Command`
2. Templates

.. _buildyaml-templates:

A Template
==========

The basic concept is a template is an "overload-able" ``build.yaml`` file that you can overload by including it inside of your specific ``build.yaml``. Deriving from a template is declared with the ``include:`` keyword.

So, given the template ``my_build_template.yaml``

.. code-block:: yaml

  props:
    # We often mark "private" properties with a '_'
    _server_location:
      windows: //isilon2
      unix: /mnt/isilon2

    _platform_arch:
      windows: AMD64-Windows
      linux: x86_64-Linux

    _extra_build_dir: {_server_location}/deployments/{_platform_arch}

  func__build_template_post():
    - ":DEL {_extra_build_dir}/*"
    - ":MKDIR {_extra_build_dir}"
    - ":COPY -f {build_dir}/* {_extra_build_dir}"

  build:
    
    # This is all that we overload
    post_build:
      - ["--extra-build", "build_template_post()"]

Then, our actual ``build.yaml`` file could look something like:

.. code-block:: yaml

  name: MyDerivedBuild

  include:
    - my_build_template

  props:
    local_setting: true

  build:
    type: basic

    files:
      - docs
      - src

    launch_json:
      env:
        PATH: ["{path}"]

Now, when we build:


.. code-block:: text

  fbuild -v MyDerivedBuild

Nothing would happen! That's because the plugin ``post_build`` command looks for the argument ``--extra-build``.

.. code-block:: text

  fbuild -v MyDerivedBuild --extra-build

The ``include`` option is a list so multiple deriving from multiple templates is possible, and because this is ``build.yaml``, you can even template based on platform. Sky's the limit.

.. note::

  The order of include is important. The overloading of values will continue from the first to the last. So if package ``a`` includes template ``b`` and ``c`` in that order, ``a`` will take precedence, followed by ``c``, and then ``b``

.. warning::

  **All** ``build.yaml``\ 's have the ``global.yaml`` template as a base, even if not explicitly marked. This provides a common ground for all packages but can be completely ignored/overloaded when required.