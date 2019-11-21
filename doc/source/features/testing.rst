*************
Testing Utils
*************

``fbuild`` comes with some facilitation of testing to standardize this bit of the development pipeline.

.. execute_code::
    :hide_code:
    :hide_headers:
    
    from build.start import build_parser
    args = build_parser().parse_args(['test', 'foo'])
    args._flaunch_parser.print_help()


build.yaml -> test:
===================

The ``build.yaml`` can contain a ``test:`` key with the usual command structure. ``pre_test``, ``commands``, and ``post_test``.

.. code-block:: yaml

    test:
        commands:
            - "python -m unittest foo.py"

coverage.py
===========

For python packages, there is a provided template ``coverage`` that provides automatic coverage given some optional settings.

.. note::

    Use this template with the ``include:`` key.

    .. code-block:: yaml

        # build.yaml

        include:
          - coverage

In your package, overload the variables in the package below to help dictate to ``fbuild`` how to execute the tests.

.. literalinclude:: ../../../templates/coverage.yaml
    :language: yaml
    :linenos:
