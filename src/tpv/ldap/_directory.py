import ldap
import pyldap

from .exceptions import KeyCollision

from ._entry import Entry


class Directory(object):
    Entry = Entry
    _ldap = None

    @property
    def ldap(self):
        if self._ldap is not None:
            if self._ldap.whoami_s() == '':
                del self._ldap
        if self._ldap is None:
            self._ldap = pyldap.PyReconnectLDAPObject(self.uri)
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
            raise KeyCollision(key)

    def __delitem__(self, dn):
        try:
            self.ldap.delete_s(dn)
        except ldap.NO_SUCH_OBJECT:
            raise KeyError(dn)

    def _search(self, base, scope=pyldap.SCOPE_SUBTREE, criteria=None,
                attrlist=None, timeout=10):
        filterstr = self._criteria_to_filterstr(*criteria)
        return (self.Entry(dn=x[0], cached_attributes=x[1], directory=self)
                for x in self.ldap.search_s(base=base, scope=scope,
                                            filterstr=filterstr,
                                            attrlist=attrlist)
                if x[0] != base or scope == pyldap.SCOPE_BASE
        )

    def _criteria_to_filterstr(self, *criteria):
        filter = pyldap.filter.LDAPDictFilter(criteria.pop(0))
        while criteria:
            filter = filter | pyldap.filter.LDAPDictFilter(criteria.pop(0))
        filterstr = unicode(filter)
        return filterstr
