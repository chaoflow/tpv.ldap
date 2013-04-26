import ldap

from . import mixins
from . import unittest


class TestAttrlistAttrsonly(mixins.Slapd, unittest.TestCase):
    def runTest(self):
        """Understand and document behaviour of attrlist and attrsonly
        """
        # attrlist=None, [], and ['*'] fetch all normal attributes,
        # so-called user-attributes
        self.assertEqual(
            [('o=o', {'objectClass': ['organization'], 'o': ['o']})],
            self.ldap.search_s('o=o', ldap.SCOPE_BASE))
        self.assertEqual(
            [('o=o', {'objectClass': ['organization'], 'o': ['o']})],
            self.ldap.search_s('o=o', ldap.SCOPE_BASE, attrlist=[]))
        self.assertEqual(
            [('o=o', {'objectClass': ['organization'], 'o': ['o']})],
            self.ldap.search_s('o=o', ldap.SCOPE_BASE, attrlist=['*']))

        # attrlist=['+'] fetches internal attributes, attrsonly=True
        # skips the values
        self.assertEqual(
            [('o=o', {'createTimestamp': [],
                      'creatorsName': [],
                      'entryCSN': [],
                      'entryDN': [],
                      'entryUUID': [],
                      'modifiersName': [],
                      'modifyTimestamp': [],
                      'structuralObjectClass': [],
                      'subschemaSubentry': []})],
            self.ldap.search_s('o=o', ldap.SCOPE_BASE,
                               attrlist=['+'], attrsonly=True))

        # attrlist=[''] skips all attributes
        self.assertEqual(
            [('o=o', {})],
            self.ldap.search_s('o=o', ldap.SCOPE_BASE, attrlist=['']))
