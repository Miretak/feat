# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import itertools
import types

from twisted.python.reflect import qual
from twisted.spread import jelly

from feat.common.serialization import base, pytree
from feat.interface.serialization import *

from . import common_serialization


class PyTreeConvertersTest(common_serialization.ConverterTest):

    def setUp(self):
        self.serializer = pytree.Serializer()
        self.unserializer = pytree.Unserializer()

    def convertion_table(self):
        ### Basic immutable types ###

        yield str, [""], str, [""], False
        yield str, ["dummy"], str, ["dummy"], False
        yield unicode, [u""], unicode, [u""], False
        yield unicode, [u"dummy"], unicode, [u"dummy"], False
        yield unicode, [u"áéí"], unicode, [u"áéí"], False
        yield int, [0], int, [0], False
        yield int, [42], int, [42], False
        yield int, [-42], int, [-42], False
        yield long, [0L], long, [0L], False
        yield long, [2**66], long, [2**66], False
        yield long, [-2**66], long, [-2**66], False
        yield float, [0.0], float, [0.0], False
        yield float, [3.1415926], float, [3.1415926], False
        yield float, [1e24], float, [1e24], False
        yield float, [1e-24], float, [1e-24], False
        yield bool, [True], bool, [True], False
        yield bool, [False], bool, [False], False
        yield type(None), [None], type(None), [None], False

        #### Basic mutable types plus tuples ###

        # Exception for empty tuple singleton
        yield tuple, [()], tuple, [()], False
        yield tuple, [(1, 2, 3)], tuple, [(1, 2, 3)], True
        yield list, [[]], list, [[]], True
        yield list, [[1, 2, 3]], list, [[1, 2, 3]], True
        yield set, [set([])], set, [set([])], True
        yield set, [set([1, 3])], set, [set([1, 3])], True
        yield dict, [{}], dict, [{}], True
        yield dict, [{1: 2, 3: 4}], dict, [{1: 2, 3: 4}], True

        # Container with different types
        yield (tuple, [(0.1, 2**45, "a", u"z", False, None,
                        (1, ), [2], set([3]), {4: 5})],
               tuple, [(0.1, 2**45, "a", u"z", False, None,
                        (1, ), [2], set([3]), {4: 5})], True)
        yield (list, [[0.1, 2**45, "a", u"z", False, None,
                       (1, ), [2], set([3]), {4: 5}]],
               list, [[0.1, 2**45, "a", u"z", False, None,
                       (1, ), [2], set([3]), {4: 5}]], True)
        yield (set, [set([0.1, 2**45, "a", u"z", False, None, (1)])],
               set, [set([0.1, 2**45, "a", u"z", False, None, (1)])], True)
        yield (dict, [{0.2: 0.1, 2**42: 2**45, "x": "a", u"y": u"z",
                       True: False, None: None, (-1, ): (1, ),
                       8: [2], 9: set([3]), 10: {4: 5}}],
               dict, [{0.2: 0.1, 2**42: 2**45, "x": "a", u"y": u"z",
                       True: False, None: None, (-1, ): (1, ),
                       8: [2], 9: set([3]), 10: {4: 5}}], True)

        ### References and Dereferences ###

        Ref = pytree.Reference
        Deref = pytree.Dereference

        # Simple reference in list
        a = []
        b = [a, a]
        yield list, [b], list, [[Ref(1, []), Deref(1)]], True

        # Simple reference in tuple
        a = ()
        b = (a, a)
        yield tuple, [b], tuple, [(Ref(1, ()), Deref(1))], True

        # Simple dereference in dict value.
        a = ()
        b = [a, {1: a}]
        yield list, [b], list, [[Ref(1, ()), {1: Deref(1)}]], True

        # Simple reference in dict value.
        a = ()
        b = [{1: a}, a]
        yield list, [b], list, [[{1: Ref(1, ())}, Deref(1)]], True

        # Simple dereference in dict keys.
        a = ()
        b = [a, {a: 1}]
        yield list, [b], list, [[Ref(1, ()), {Deref(1): 1}]], True

        # Simple reference in dict keys.
        a = ()
        b = [{a: 1}, a]
        yield list, [b], list, [[{Ref(1, ()): 1}, Deref(1)]], True

        # Multiple reference in dictionary values, because dictionary order
        # is not predictable all possibilities have to be tested
        a = {}
        b = {1: a, 2: a, 3: a}
        yield (dict, [b], dict,
               [{1: Ref(1, {}), 2: Deref(1), 3: Deref(1)},
                {1: Deref(1), 2: Ref(1, {}), 3: Deref(1)},
                {1: Deref(1), 2: Deref(1), 3: Ref(1, {})}],
               True)

        # Multiple reference in dictionary keys, because dictionary order
        # is not predictable all possibilities have to be tested
        a = (1, )
        b = {(1, a): 1, (2, a): 2, (3, a): 3}
        yield (dict, [b], dict,
               [{(1, Ref(1, (1, ))): 1, (2, Deref(1)): 2, (3, Deref(1)): 3},
                {(1, Deref(1)): 1, (2, Ref(1, (1, ))): 2, (3, Deref(1)): 3},
                {(1, Deref(1)): 1, (2, Deref(1)): 2, (3, Ref(1, (1, ))): 3}],
               True)

        # Simple dereference in set.
        a = ()
        b = [a, set([a])]
        yield list, [b], list, [[Ref(1, ()), set([Deref(1)])]], True

        # Simple reference in set.
        a = ()
        b = [set([a]), a]
        yield list, [b], list, [[set([Ref(1, ())]), Deref(1)]], True

        # Multiple reference in set, because set values order
        # is not predictable all possibilities have to be tested
        a = (1, )
        b = set([(1, a), (2, a), (3, a)])
        yield (set, [b], set,
               [set([(1, Ref(1, (1, ))), (2, Deref(1)), (3, Deref(1))]),
                set([(1, Deref(1)), (2, Ref(1, (1, ))), (3, Deref(1))]),
                set([(1, Deref(1)), (2, Deref(1)), (3, Ref(1, (1, )))])],
               True)

        # List self-reference
        a = []
        a.append(a)
        yield list, [a], Ref, [Ref(1, [Deref(1)])], True

        # Dict self-reference
        a = {}
        a[1] = a
        yield dict, [a], Ref, [Ref(1, {1: Deref(1)})], True

        # Multiple references
        a = []
        b = [a]
        c = [a, b]
        d = [a, b, c]
        yield (list, [d], list, [[Ref(1, []), Ref(2, [Deref(1)]),
                                 [Deref(1), Deref(2)]]], True)

        # Complex structure without dict or set
        a = ()
        b = (a, )
        b2 = set(b)
        c = (a, b)
        c2 = [c]
        d = (a, b, c)
        d2 = [a, b2, c2]
        e = (b, c, d)
        e2 = [b2, c2, e]
        g = (b, b2, c, c2, d, d2, e, e2)

        yield (tuple, [g], tuple, [(Ref(2, (Ref(1, ()), )),
                                    Ref(4, set([Deref(1)])),
                                    Ref(3, (Deref(1), Deref(2))),
                                    Ref(5, [Deref(3)]),
                                    Ref(6, (Deref(1), Deref(2), Deref(3))),
                                    [Deref(1), Deref(4), Deref(5)],
                                    Ref(7, (Deref(2), Deref(3), Deref(6))),
                                    [Deref(4), Deref(5), Deref(7)])], True)

        Inst = pytree.Instance
        Dummy = common_serialization.SerializableDummy

        # Default instance
        o = Dummy()
        yield (Dummy, [o], Inst,
               [Inst(qual(Dummy),
                     {"str": "dummy",
                      "unicode": u"dummy",
                      "int": 42,
                      "long": 2**66,
                      "float": 3.1415926,
                      "bool": True,
                      "none": None,
                      "list": [1, 2, 3],
                      "tuple": (1, 2, 3),
                      "set": set([1, 2, 3]),
                      "dict": {1: 2, 3: 4},
                      "ref": None})], True)
