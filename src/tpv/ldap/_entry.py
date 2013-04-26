from __future__ import absolute_import

from metachao import aspect
from metachao.aspect import Aspect

import tpv.aspects


class cache_attributes(Aspect):
    @aspect.plumb
    def __init__(_next, self, attributes=None, cached_attributes=None, **kw):
        _next(**kw)
        self.cache = dict(attributes or ())
        self.cache.update(cached_attributes or ())

    @aspect.plumb
    def iteritems(_next, self):
        return self.cache.iteritems()


@tpv.aspects.keys
@tpv.aspects.values
@tpv.aspects.items
@cache_attributes
class Entry(object):
    """An ldap entry

    Its attributes are its children.
    """
    @property
    def ldap(self):
        return self.directory.ldap

    def __init__(self, dn=None, directory=None):
        self.dn = dn
        self.directory = directory

    def __iter__(self):
        pass

    def itervalues(self):
        pass

    def iteritems(self):
        pass

    def update(self, attributes):
        """Attributes is a dictionary
        """

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.dn)
