
import os
import sys
import time
import unittest

import logging

# _root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(os.path.join(_root_path, 'src'))

def run_tests(package, scan, pattern):

    tests = unittest.TestLoader().discover(
        scan,
        pattern=pattern
    )
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    run_tests()