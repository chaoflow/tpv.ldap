import ldap
import pyldap

from .exceptions import KeyCollision

from ._entry import Entry


def trace(fn):
    def traced(*args, **kw):
        print 'trace fn: %s: %s\ntrace []: %s\ntrace {}:%s' % \
            (fn.__name__, fn, args, kw)
        result = fn(*args, **kw)
        print '>>>>>>: %r' % (result,)
        return result
    return traced


class Directory(object):
    trace_ldap_calls = None

    Entry = Entry
    _ldap = None

    @property
    def ldap(self):
        if self._ldap is not None:
            if self._ldap.whoami_s() == '':
                del self._ldap
        if self._ldap is None:
            self._ldap = pyldap.PyReconnectLDAPObject(self.uri)
            for name in (self.trace_ldap_calls or ()):
                setattr(self._ldap, name, trace(getattr(self._ldap, name)))
            self._ldap.bind_s(self.bind_dn, self.bind_pw)
        return self._ldap

    def __init__(self, uri=None, bind_dn=None, bind_pw=None):
        self.uri = uri
        self.bind_dn = bind_dn
        self.bind_pw = bind_pw

    def __contains__(self, dn):
        try:
            entry = self.ldap.search_s(dn, ldap.SCOPE_BASE, attrlist=[''])[0]
            return dn == entry[0]
        except ldap.NO_SUCH_OBJECT:
            return False

    def __getitem__(self, dn):
        try:
            entry = self.ldap.search_s(dn, ldap.SCOPE_BASE)[0]
        except ldap.NO_SUCH_OBJECT:
            raise KeyError(dn)
        node = self.Entry(dn=dn, attributes=entry[1], directory=self)
        return node

    def __setitem__(self, dn, node):
        addlist = node.items()
        try:
            self.ldap.add_s(dn, addlist)
        except ldap.ALREADY_EXISTS:
            raise KeyCollision(dn)

    def __delitem__(self, dn):
        try:
            self.ldap.delete_s(dn)
        except ldap.NO_SUCH_OBJECT:
            raise KeyError(dn)

    def search(self, base, scope, criteria=None, filterstr=None,
               attrlist=None, timeout=10):
        filterstr = filterstr or '(objectClass=*)'
        if criteria:
            filter = self._criteria_to_filter(criteria)
            filter = filter & filterstr
            filterstr = unicode(filter)
        if attrlist is None:
            attrlist = [''] # meaning: not attributes, ['*'] all, ['+'] internal
        return (
            self.Entry(dn=dn, cached_attributes=attributes, directory=self)
            for dn, attributes in self.ldap.search_s(base=base, scope=scope,
                                                     filterstr=filterstr,
                                                     attrlist=attrlist)
            if dn != base or scope == pyldap.SCOPE_BASE
        )

    def _criteria_to_filter(self, criteria):
        # XXX: passing of criteria feels complicated
        if type(criteria) not in (tuple, list):
            raise ValueError(
                "Criteria not list of dicts, but: %r" % criteria)
        filter = pyldap.filter.LDAPDictFilter(criteria.pop(0))
        while criteria:
            filter = filter | pyldap.filter.LDAPDictFilter(criteria.pop(0))
        return filter
