#####################
String Expression API
#####################

.. autoclass:: common.strexpr._StringExpression
    :members: launch_data, run, evaluate

Current Expressions
===================

.. execute_code::
    :hide_code:
    :hide_headers:

    from common.strexpr import _StringExpression
    print (_StringExpression._get_expressions_info())
