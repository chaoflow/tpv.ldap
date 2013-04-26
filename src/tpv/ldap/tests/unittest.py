from __future__ import absolute_import

from unittest import TestCase

try:
    TestCase.selfAssertItemsEqual
except AttributeError:
    del TestCase
    from unittest2 import TestCase
