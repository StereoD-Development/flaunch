"""
Deployment utilities for transfering deployed packages 


Example transfer JSON:
{
   "source": "tor|mad|pun",
   "target": "tor|mad|pun",
   "paths": ["path1", "path2"],
   "priority": <int>,
   "notify-url": "<url>",
   "notify-payload": {"foo"}
}
The paths should be native Linux paths.

`priority`, `notify-url` and `notify-payload` are optional.
`notify-payload` is an opaque JSON blob that will be simply passed to the `notify-url` as a payload.
Pop in any identifying markers you need.
"""


class TransferUtil(object):
    """
    """
    def __init__(self):
        """
        TODO
        """
        pass # __AFTER_TDE__ -> Before this, let's start with a nice way to package crap up...
