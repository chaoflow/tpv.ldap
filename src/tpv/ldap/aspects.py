from __future__ import absolute_import

import ldap

import tpv

from metachao import aspect
from metachao.aspect import Aspect

from tpv.ordereddict import OrderedDict


class add(Aspect):
    def add(self, attributes):
        dn = attributes.pop('dn')
        entry = self.Child(dn=dn, attributes=attributes)
        self[dn] = entry
        return dn


class id_instead_of_dn(Aspect):
    @aspect.plumb
    def __getitem__(_next, self, id):
        dn = self._dn_from_id(id)
        node = _next(dn)
        node._id = id
        return node

    @aspect.plumb
    def add(_next, self, attributes):
        dn = _next(attributes)
        id = self._id_from_dn(dn)
        return id

    @aspect.plumb
    def __iter__(_next, self):
        return (self._id_from_dn(dn) for dn in _next())

    @aspect.plumb
    def iteritems(_next, self):
        return ((self._id_from_dn(dn), node) for dn, node in _next())

    def _dn_from_id(self, id):
        """Application needs to overwrite this
        """
        raise NotImplemented

    def _id_from_dn(self, dn):
        """Application needs to overwrite this
        """
        raise NotImplemented

    @aspect.plumb
    def search(_next, self, *args, **kw):
        for node in _next(*args, **kw):
            id = self._id_from_dn(node.dn)
            node._id = id
            yield node


class attribute_name_mapping_base(Aspect):
    attribute_name_map = aspect.aspectkw(None)

    @property
    def incoming_attribute_map(self):
        return dict(self.attribute_name_map or ())

    @property
    def outgoing_attribute_map(self):
        return dict((v,k) for k,v in (self.attribute_name_map or ()))


class attribute_name_mapping(attribute_name_mapping_base):
    @property
    def attribute_name_map(self):
        return self.directory.attribute_name_map

    @aspect.plumb
    def __getitem__(_next, self, key):
        key = self.incoming_attribute_map.get(key, key)
        value = _next(key)
        return value

    @aspect.plumb
    def __setitem__(_next, self, key, value):
        key = self.incoming_attribute_map.get(key, key)
        return _next(key, value)

    @aspect.plumb
    def iteritems(_next, self):
        return ((self.outgoing_attribute_map.get(k, k), v) for k, v in _next())

    def items(self):
        return self.iteritems()

    @aspect.plumb
    def update(_next, self, attributes):
        attributes = OrderedDict(
            (self.incoming_attribute_map.get(k, k), v)
            for k, v in attributes.items()
        )
        return _next(attributes)


class children_attribute_name_mapping(attribute_name_mapping_base):
    @aspect.plumb
    def add(_next, self, attributes):
        attributes = OrderedDict(
            (self.incoming_attribute_map.get(k, k), v)
            for k, v in attributes.items()
        )
        return _next(attributes)

    # @aspect.plumb
    # def __getitem__(_next, self, key):
    #     node = _next(key)
    #     if self.attribute_name_map:
    #         dn = node.dn
    #         id = node._id
    #         node = attribute_name_mapping(
    #             node,
    #             attribute_name_map=self.attribute_name_map,
    #         )
    #         node.dn = dn
    #         node._id = id
    #     return node

    # @aspect.plumb
    # def search(_next, self, *args, **kw):
    #     # XXX: criteria mapping
    #     for node in _next(*args, **kw):
    #         dn = node.dn
    #         id = node._id
    #         node = attribute_name_mapping(
    #             node,
    #             attribute_name_map=self.attribute_name_map,
    #         )
    #         node.dn = dn
    #         node._id = id
    #         yield node

    # XXX: we need a way to block this, but let add from earlier
    # on use the unblocked version. Actually @add should take care
    # of that
    # @aspect.plumb
    # def __setitem__(_next, self, key, value):
    #     pass


@tpv.aspects.keys
@tpv.aspects.values
@tpv.aspects.items
class view(aspect.Aspect):
    """A view of an ldap directory
    """
    scope = aspect.aspectkw(scope=ldap.SCOPE_SUBTREE)
    base_dn = aspect.aspectkw(None)
    filterstr = aspect.aspectkw(None)

    # dn_from_id = aspect.aspectkw(dn_from_id=None)
    # id_from_dn = aspect.aspectkw(id_from_dn=None)

    def __iter__(self):
        return self.search(attrlist=[''])

    def itervalues(self):
        return self.search()

    def iteritems(self):
        return ((node.dn, node) for node in self.itervalues())

    @aspect.plumb
    def search(_next, self, attrlist=None, criteria=None, filterstr=None):
        if filterstr is not None:
            filterstr = '(&%s%s)' % (filterstr, self.filterstr)
        else:
            filterstr = self.filterstr
        return _next(base=self.base_dn,
                     scope=self.scope,
                     filterstr=filterstr,
                     attrlist=attrlist,
                     criteria=criteria)
