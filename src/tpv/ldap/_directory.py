import ldap
import logging
import pyldap
import pyldap.filter

from tpv import exceptions as exc

from ._entry import Entry

log = logging.getLogger('tpv.ldap')


def trace(fn):
    def traced(*args, **kw):
        log.debug('trace fn: %s: %s\n\ttrace []: %s\n\ttrace {}:%s' %
                  (fn.__name__, fn, args, kw))
        result = presult = fn(*args, **kw)
        if type(result) in (tuple, list) and len(result) > 10:
            presult = result[:10]
            presult.append('...')
        log.debug('>>>>>>: %r' % (presult,))
        return result
    return traced


class Directory(object):
    trace_ldap_calls = None

    Child = Entry
    _ldap = None

    @property
    def ldap(self):
        # if self._ldap is not None:
        #     if self._ldap.whoami_s() == '':
        #         del self._ldap
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
            entry = self.ldap.search_s(dn, ldap.SCOPE_BASE,
                                       attrlist=['*', 'memberOf'])[0]
        except ldap.NO_SUCH_OBJECT:
            raise KeyError(dn)
        node = self.Child(dn=dn, attributes=entry[1], directory=self)
        return node

    def __setitem__(self, dn, node):
        addlist = node.items()
        try:
            self.ldap.add_s(dn, addlist)
        except ldap.ALREADY_EXISTS:
            raise exc.KeyCollision(dn)

    def __delitem__(self, dn):
        try:
            self.ldap.delete_s(dn)
        except ldap.NO_SUCH_OBJECT:
            raise KeyError(dn)

    def search(self, base, scope, criteria=None, base_criteria=None,
               filterstr=None, attrlist=None, timeout=10):
        """search the ldap directory

        At the very least base dn and scope are needed. You will
        receive empty nodes that are able to fetch their attributes as
        children.

        """
        filterstr = filterstr or '(objectClass=*)'
        if criteria:
            filter = pyldap.filter.criteria_to_filter(criteria)
            filter = filter & filterstr
            filterstr = unicode(filter)
        if base_criteria:
            filter = pyldap.filter.criteria_to_filter(base_criteria)
            filter = filter & filterstr
            filterstr = unicode(filter)
        if attrlist is None:
            attrlist = ['*', 'memberOf']
        return (
            self.Child(dn=dn, attributes=attributes, directory=self)
            for dn, attributes in self.ldap.search_s(base=base, scope=scope,
                                                     filterstr=filterstr,
                                                     attrlist=attrlist)
            if dn != base or scope == pyldap.SCOPE_BASE
        )
