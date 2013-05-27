from __future__ import absolute_import

import ldap

from metachao import aspect
from metachao.aspect import Aspect

import tpv.aspects


class cache_attributes(Aspect):
    @aspect.plumb
    def __init__(_next, self, attributes=None, **kw):
        _next(**kw)
        if attributes is not None:
            self.cache = dict(attributes or ())

    def __iter__(self):
        return iter(self.cache)

    def iteritems(self):
        return self.cache.iteritems()

    def itervalues(self):
        return self.cache.itervalues()

    def __getitem__(self, key):
        return self.cache[key]

    @aspect.plumb
    def update(_next, self, attributes):
        _next(attributes)
        self.cache.update(attributes)


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

    @property
    def ROOT(self):
        return self.directory.ROOT

    def __init__(self, dn=None, directory=None):
        self.dn = dn
        self.directory = directory

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        self.update({key: value})

    def __delitem__(self, key, value=None):
        self.ldap.modify_s(self.dn, [(ldap.MOD_DELETE, key, value)])

    def update(self, attributes):
        """Attributes is a dictionary
        """
        # XXX: modlist for lists
        modlist = [((k in self or k == 'userPassword') and
                    ldap.MOD_REPLACE or ldap.MOD_ADD, k, v)
                   for k, v in attributes.items()]
        self.ldap.modify_s(self.dn, modlist)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.dn)
