import ldap
import pyldap
import pyldap.filter

import tpv.ordereddict

from tpv.ldap import Directory

from . import mixins
from . import unittest


class TestLDAPDirectory(mixins.Slapd, unittest.TestCase):
    ENTRIES = {
        'cn=cn0,o=o': (('cn', ['cn0']),
                       ('objectClass', ['organizationalRole'])),
        'cn=cn1,o=o': (('cn', 'cn1'),
                       ('objectClass', ['organizationalRole'])),
    }
    ADDITIONAL = {
        'cn=cn2,o=o': (('cn', ['cn2']),
                       ('st', 'bar'),
                       ('objectClass', ['organizationalRole'])),
        'cn=child,cn=cn1,o=o': (('cn', 'child'),
                                ('ou', 'foo'),
                                ('objectClass', ['organizationalRole'])),
        'cn=child2,cn=cn1,o=o': (('cn', 'child2'),
                                 ('ou', 'foo',),
                                 ('st', 'bar',),
                                 ('objectClass', ['organizationalRole'])),
    }

    def setUp(self):
        mixins.Slapd.setUp(self)
        self.dir = Directory(uri=self.uri, bind_dn=self.bind_dn,
                             bind_pw=self.bind_pw)

    def test_contains(self):
        self.assertTrue('cn=cn0,o=o' in self.dir)
        self.assertFalse('cn=fail,o=o' in self.dir)

    def test_getitem(self):
        def get_nonexistent():
            self.dir['cn=fail,o=o']

        dn = 'cn=cn0,o=o'
        self.assertEqual(dn, self.dir[dn].dn)
        self.assertRaises(KeyError, get_nonexistent)

    def test_setitem(self):
        dn = 'cn=cn2,o=o'
        node = self.dir.Child(dn=dn, attributes=self.ADDITIONAL[dn])

        def addnode():
            self.dir[dn] = node

        addnode()
        self.assertEquals(dn, self.dir[dn].dn)
        self.assertRaises(KeyError, addnode)

    def test_delitem(self):
        def delete():
            del self.dir['cn=cn0,o=o']

        def search_deleted():
            self.ldap.search_s('cn=cn0,o=o', ldap.SCOPE_BASE)

        delete()
        self.assertRaises(KeyError, delete)
        self.assertRaises(ldap.NO_SUCH_OBJECT, search_deleted)

    def test_search_base(self):
        # XXX: add more scopes and filters and fun
        search = list(self.dir.search(base='o=o', scope=pyldap.SCOPE_BASE))
        self.assertEqual([x.dn for x in search], ['o=o'])
        self.assertEqual(len(search), 1)
        self.assertEqual(search[0].dn, 'o=o')

    def test_search_subtree(self):
        search = list(self.dir.search(base='o=o', scope=pyldap.SCOPE_SUBTREE))
        self.assertEqual(len(search), 2)

    def test_search_subtree_filterstr(self):
        dn = 'cn=child,cn=cn1,o=o'
        node = self.dir.Child(dn=dn, attributes=self.ADDITIONAL[dn])
        self.dir[dn] = node

        search = list(self.dir.search(base='o=o',
                                      scope=pyldap.SCOPE_SUBTREE,
                                      filterstr='(cn=child)'))
        self.assertEqual(len(search), 1)

    def test_search_subtree_filterstr_criteria(self):
        dn = 'cn=child,cn=cn1,o=o'
        node = self.dir.Child(dn=dn, attributes=self.ADDITIONAL[dn])
        self.dir[dn] = node
        dn = 'cn=child2,cn=cn1,o=o'
        node = self.dir.Child(dn=dn, attributes=self.ADDITIONAL[dn])
        self.dir[dn] = node
        dn = 'cn=cn2,o=o'
        node = self.dir.Child(dn=dn, attributes=self.ADDITIONAL[dn])
        self.dir[dn] = node

        search = list(self.dir.search(base='o=o',
                                      scope=pyldap.SCOPE_SUBTREE,
                                      filterstr='(ou=foo)'))
        self.assertEqual(len(search), 2)
        search = list(self.dir.search(base='o=o',
                                      scope=pyldap.SCOPE_SUBTREE,
                                      criteria=[dict(st='bar')],
                                      filterstr='(ou=foo)'))
        self.assertEqual(len(search), 1)
        search = list(self.dir.search(base='o=o',
                                      scope=pyldap.SCOPE_SUBTREE,
                                      criteria=[dict(st='bar'),
                                                dict(cn="child")],
                                      filterstr='(ou=foo)'))
        self.assertEqual(len(search), 2)
