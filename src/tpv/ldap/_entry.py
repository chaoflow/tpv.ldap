from __future__ import absolute_import

from metachao import aspect
from metachao.aspect import Aspect


# class cache_fetchall_on_miss(Aspect):
#     cache = aspect.aspectkw(cache=None)

#     @aspect.plumb
#     def __getitem__(_next, self, key):
#         try:
#             return self.cache[key]
#         except KeyError:


class Entry(object):
    """An ldap entry

    Its attributes are its children.
    """
    @property
    def ldap(self):
        return self.directory.ldap

    def __init__(self, dn=None, directory=None, attributes=None):
        self.dn = dn
        self.directory = directory

    def update(self, attributes):
        """Attributes is a dictionary
        """
