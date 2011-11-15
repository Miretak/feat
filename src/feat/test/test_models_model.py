# F3AT - Flumotion Asynchronous Autonomous Agent Toolkit
# Copyright (C) 2010,2011 Flumotion Services, S.A.
# All rights reserved.

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# See "LICENSE.GPL" in the source distribution for more information.

# Headers in this file shall remain intact.

import types

from zope.interface import implements

from feat.common import defer, adapter
from feat.models import interface, model, action, value
from feat.models import call, getter, setter

from . import common


class DummyView(object):

    def __init__(self, num=None):
        self.num = num


class DummyContext(object):

    implements(interface.IContext)

    def __init__(self, models=[], names=[], remaining=[]):
        self.models = tuple(models)
        self.names = tuple(names)
        self.remaining = tuple(remaining)


class DummySource(object):

    def __init__(self):
        self.attr2 = None
        self.attrs = {u"attr3": None}
        self.child = None
        self.views = {u"view1": DummyView(),
                      u"view2": DummyView()}
        self.items = {}

    def get_attr2(self):
        return self.attr2

    def get_attr(self, name):
        return self.attrs[name]

    def set_attr(self, name, value):
        self.attrs[name] = value

    def get_view(self, name):
        return self.views[name]

    def iter_names(self):
        return self.items.iterkeys()

    def get_value(self, name):

        def retrieve(key):
            return self.items[key]

        d = defer.succeed(name)
        d.addCallback(common.delay, 0.01)
        d.addCallback(retrieve)
        return d


class DummyAspect(object):

    implements(interface.IAspect)

    def __init__(self, name, label=None, desc=None):
        self.name = unicode(name)
        self.label = unicode(label) if label is not None else None
        self.desc = unicode(desc) if desc is not None else None


class DummyAction(action.Action):
    __slots__ = ()
    action.label("Default Label")
    action.desc("Default description")


@adapter.register(DummySource, interface.IModel)
class DummyModel1(model.Model):
    model.identity("dummy-model1")


class DummyModel2(model.Model):
    model.identity("dummy-model2")


class DummyModel3(model.Model):
    model.identity("dummy-model3")


class TestModel(model.Model):
    __slots__ = ()
    model.identity("test-model")
    model.action("action1", DummyAction)
    model.action("action2", DummyAction,
                 label="Action2 Label",
                 desc="Action2 description")
    model.attribute("attr1", value.Integer())
    model.attribute("attr2", value.String(),
                    getter=call.source_call("get_attr2"),
                    label="Attribute 2",
                    desc="Some attribute")
    model.attribute("attr3", value.Integer(),
                    getter=getter.source_get("get_attr"),
                    setter=setter.source_set("set_attr"))
    model.child("child1", label="Child 1")
    model.child("child2", getter.source_attr("child"),
                model="dummy-model2", label="Child 2")
    model.child("child3", getter.source_attr("child"),
                model=DummyModel3, desc="Third child")
    model.view("view1", "test-view", getter.source_get("get_view"))
    model.view("view2", "test-view", getter.source_get("get_view"),
               label="View 2", desc="Second view")
    model.view("view3", "test-view")
    model.children("values",
                   child_names=call.source_call("iter_names"),
                   child_source=getter.source_get("get_value"),
                   child_label="Some Value", child_desc="Some dynamic value",
                   label="Some Values", desc="Some dynamic values")


class TestView(model.Model):
    __slots__ = ()
    model.identity("test-view")
    model.attribute("num", value.Integer(),
                    getter=getter.view_attr("num"),
                    setter=setter.view_attr("num"))


class TestCollection(model.Collection):
    __slots__ = ()
    model.identity("test-collection")
    model.child_names(call.source_call("iter_names"))
    model.child_source(getter.source_get("get_value"), DummyModel2,
                       label="Some Child", desc="Some dynamic child")
    model.action("action", DummyAction)


class TestModelsModel(common.TestCase):

    def setUp(self):
        self._factories_snapshot = model.snapshot_factories()
        return common.TestCase.setUp(self)

    def tearDown(self):
        model.restore_factories(self._factories_snapshot)
        return common.TestCase.tearDown(self)

    def testFactoryRegistry(self):
        self.assertTrue(model.get_factory("test-model") is TestModel)
        self.assertTrue(model.get_factory(u"test-model") is TestModel)

    def testBasicFields(self):
        s = DummySource()
        m = TestModel(s)

        self.assertTrue(interface.IModelFactory.providedBy(TestModel))
        self.assertTrue(interface.IModel.providedBy(m))
        self.assertFalse(hasattr(m, "__dict__"))

        self.assertEqual(m.identity, u"test-model")
        self.assertTrue(isinstance(m.identity, unicode))
        self.assertEqual(m.name, None)
        self.assertEqual(m.desc, None)

        a = DummyAspect("name", "label", "desc")
        m = TestModel(s, a)

        self.assertEqual(m.identity, u"test-model")
        self.assertTrue(isinstance(m.identity, unicode))
        self.assertEqual(m.name, u"name")
        self.assertTrue(isinstance(m.name, unicode))
        self.assertEqual(m.label, u"label")
        self.assertTrue(isinstance(m.label, unicode))
        self.assertEqual(m.desc, u"desc")
        self.assertTrue(isinstance(m.desc, unicode))

    @defer.inlineCallbacks
    def testModelActions(self):
        s = DummySource()
        m = TestModel(s)

        yield self.asyncEqual(2, m.count_actions())

        yield self.asyncEqual(True, m.provides_action("action1"))
        yield self.asyncEqual(True, m.provides_action(u"action1"))
        yield self.asyncEqual(True, m.provides_action("action2"))
        yield self.asyncEqual(True, m.provides_action(u"action2"))
        yield self.asyncEqual(False, m.provides_action("dummy"))
        yield self.asyncEqual(False, m.provides_action(u"dummy"))

        yield self.asyncEqual(None, m.fetch_action("dummy"))
        yield self.asyncEqual(None, m.fetch_action(u"dummy"))

        a = yield m.fetch_action("action1")
        self.assertTrue(interface.IModelAction.providedBy(a))
        self.assertFalse(hasattr(a, "__dict__"))
        self.assertEqual(a.name, u"action1")
        self.assertTrue(isinstance(a.name, unicode))
        self.assertEqual(a.label, u"Default Label")
        self.assertTrue(isinstance(a.label, unicode))
        self.assertEqual(a.desc, u"Default description")
        self.assertTrue(isinstance(a.desc, unicode))

        a = yield m.fetch_action("action2")
        self.assertTrue(interface.IModelAction.providedBy(a))
        self.assertEqual(a.name, u"action2")
        self.assertTrue(isinstance(a.name, unicode))
        self.assertEqual(a.label, u"Action2 Label")
        self.assertTrue(isinstance(a.label, unicode))
        self.assertEqual(a.desc, u"Action2 description")
        self.assertTrue(isinstance(a.desc, unicode))

    @defer.inlineCallbacks
    def testModelItems(self):
        s = DummySource()
        m = TestModel(s)

        ITEMS = ("attr1", "attr2", "attr3",
                 "child1", "child2", "child3",
                 "view1", "view2", "view3",
                 "values")

        yield self.asyncEqual(len(ITEMS), m.count_items())

        for name in ITEMS:
            yield self.asyncEqual(True, m.provides_item(name))
            yield self.asyncEqual(True, m.provides_item(unicode(name)))

        yield self.asyncEqual(False, m.provides_item("dummy"))
        yield self.asyncEqual(False, m.provides_item(u"dummy"))
        yield self.asyncEqual(None, m.fetch_item("dummy"))
        yield self.asyncEqual(None, m.fetch_item(u"dummy"))

        items = yield m.fetch_items()
        self.assertTrue(isinstance(items, list))
        self.assertEqual(len(items), len(ITEMS))
        for item in items:
            self.assertTrue(interface.IModelItem.providedBy(item))
            self.assertFalse(hasattr(item, "__dict__"))
            self.assertTrue(isinstance(item.name, (unicode, types.NoneType)))
            self.assertTrue(isinstance(item.label, (unicode, types.NoneType)))
            self.assertTrue(isinstance(item.desc, (unicode, types.NoneType)))
            self.assertTrue(interface.IReference.providedBy(item.reference))
            ctx = DummyContext()
            self.assertEqual(item.reference.resolve(ctx), tuple([item.name]))
            model = yield item.fetch()
            self.assertTrue(interface.IModel.providedBy(model))
            model = yield item.browse()
            self.assertTrue(interface.IModel.providedBy(model))

        yield self.asyncErrback(interface.NotSupported, m.query_items)

    @defer.inlineCallbacks
    def testModelAttribute(self):
        s = DummySource()
        m = TestModel(s)

        # attr1

        attr1_item = yield m.fetch_item(u"attr1")
        self.assertFalse(hasattr(attr1_item, "__dict__"))
        self.assertEqual(attr1_item.name, u"attr1")
        self.assertEqual(attr1_item.label, None)
        self.assertEqual(attr1_item.desc, None)

        attr1 = yield attr1_item.fetch()
        self.assertFalse(hasattr(attr1, "__dict__"))
        self.assertTrue(interface.IAttribute.providedBy(attr1))
        self.assertFalse(attr1.is_readable)
        self.assertFalse(attr1.is_writable)
        self.assertFalse(attr1.is_deletable)
        self.assertEqual(attr1.value_info, value.Integer())
        yield self.asyncIterEqual([], attr1.fetch_actions())
        yield self.asyncIterEqual([], attr1.fetch_items())

        # attr2

        attr2_item = yield m.fetch_item(u"attr2")
        self.assertEqual(attr2_item.name, u"attr2")
        self.assertEqual(attr2_item.label, u"Attribute 2")
        self.assertEqual(attr2_item.desc, u"Some attribute")

        attr2 = yield attr2_item.browse()
        self.assertTrue(interface.IAttribute.providedBy(attr2))
        self.assertTrue(attr2.is_readable)
        self.assertFalse(attr2.is_writable)
        self.assertFalse(attr2.is_deletable)
        self.assertEqual(attr2.value_info, value.String())
        yield self.asyncIterEqual([], attr1.fetch_items())
        actions = yield attr2.fetch_actions()
        self.assertEqual(set([a.name for a in actions]), set([u"get"]))
        action_get = yield attr2.fetch_action(u"get")

        s.attr2 = "foo"
        val = yield attr2.fetch_value()
        self.assertEqual(val, "foo")
        s.attr2 = "bar"
        val = yield action_get.perform()
        self.assertEqual(val, "bar")

        yield self.asyncErrback(interface.NotSupported,
                                attr2.update_value, "fez")
        yield self.asyncErrback(interface.NotSupported,
                                attr2.delete_value)

        # attr3

        attr3_item = yield m.fetch_item(u"attr3")

        attr3 = yield attr3_item.fetch()
        self.assertTrue(interface.IAttribute.providedBy(attr3))
        self.assertTrue(attr3.is_readable)
        self.assertTrue(attr3.is_writable)
        self.assertFalse(attr3.is_deletable)
        self.assertEqual(attr3.value_info, value.Integer())
        yield self.asyncIterEqual([], attr1.fetch_items())
        actions = yield attr3.fetch_actions()
        self.assertEqual(set([a.name for a in actions]),
                         set([u"get", u"set"]))
        action_get = yield attr3.fetch_action(u"get")
        action_set = yield attr3.fetch_action(u"set")

        s.attrs["attr3"] = 42
        val = yield attr3.fetch_value()
        self.assertEqual(val, 42)
        self.assertEqual(42, s.attrs["attr3"])
        s.attrs["attr3"] = 66
        val = yield action_get.perform()
        self.assertEqual(val, 66)
        self.assertEqual(66, s.attrs["attr3"])

        val = yield attr3.update_value("99")
        self.assertEqual(99, s.attrs["attr3"])
        self.assertEqual(99, val)
        val = yield action_set.perform("44")
        self.assertEqual(44, s.attrs["attr3"])
        self.assertEqual(44, val)

        yield self.asyncErrback(interface.NotSupported, attr3.delete_value)

    @defer.inlineCallbacks
    def testModelChild(self):
        src = DummySource()
        src.child = object()
        mdl = TestModel(src)

        # child1

        child1_item = yield mdl.fetch_item(u"child1")
        self.assertEqual(child1_item.name, u"child1")
        self.assertEqual(child1_item.label, u"Child 1")
        self.assertEqual(child1_item.desc, None)

        child1 = yield child1_item.fetch()
        yield self.asyncIterEqual([], child1.fetch_actions())
        yield self.asyncIterEqual([], child1.fetch_items())

        self.assertTrue(child1.source is src)
        self.assertTrue(isinstance(child1, DummyModel1))

        # The model is gotten from IModel adaptation
        # so it do not have any aspect
        self.assertEqual(child1.name, None)
        self.assertEqual(child1.label, None)
        self.assertEqual(child1.desc, None)

        # child2

        child2_item = yield mdl.fetch_item(u"child2")
        self.assertEqual(child2_item.name, u"child2")
        self.assertEqual(child2_item.label, u"Child 2")
        self.assertEqual(child2_item.desc, None)

        child2 = yield child2_item.browse()
        yield self.asyncIterEqual([], child2.fetch_actions())
        yield self.asyncIterEqual([], child2.fetch_items())

        self.assertEqual(child2.name, u"child2")
        self.assertEqual(child2.label, u"Child 2")
        self.assertEqual(child2.desc, None)

        self.assertTrue(child2.source is src.child)
        self.assertTrue(isinstance(child2, DummyModel2))

        # child3

        child3_item = yield mdl.fetch_item(u"child3")
        self.assertEqual(child3_item.name, u"child3")
        self.assertEqual(child3_item.label, None)
        self.assertEqual(child3_item.desc, u"Third child")

        child3 = yield child3_item.fetch()
        yield self.asyncIterEqual([], child3.fetch_actions())
        yield self.asyncIterEqual([], child3.fetch_items())

        self.assertEqual(child3.name, u"child3")
        self.assertEqual(child3.label, None)
        self.assertEqual(child3.desc, u"Third child")

        self.assertTrue(child3.source is src.child)
        self.assertTrue(isinstance(child3, DummyModel3))

    @defer.inlineCallbacks
    def testModelView(self):
        src = DummySource()
        mdl = TestModel(src)
        src.views[u"view1"] = DummyView()
        src.views[u"view1"].num = 33
        src.views[u"view2"] = DummyView()
        src.views[u"view2"].num = 44

        # view1

        view1_item = yield mdl.fetch_item(u"view1")
        self.assertFalse(hasattr(view1_item, "__dict__"))
        self.assertEqual(view1_item.name, u"view1")
        self.assertEqual(view1_item.label, None)
        self.assertEqual(view1_item.desc, None)

        view1 = yield view1_item.fetch()
        self.assertFalse(hasattr(view1, "__dict__"))
        self.assertTrue(isinstance(view1, TestView))
        self.assertTrue(view1.source is src)
        self.assertTrue(view1.aspect is not None)
        self.assertTrue(view1.view is src.views[u"view1"])
        view1_num_item = yield view1.fetch_item("num")
        view1_num = yield view1_num_item.fetch()
        self.assertTrue(view1_num.source is src)
        self.assertTrue(view1_num.view is src.views[u"view1"])
        num = yield view1_num.fetch_value()
        self.assertEqual(num, 33)
        ret = yield view1_num.update_value("55")
        self.assertEqual(ret, 55)
        self.assertEqual(src.views[u"view1"].num, 55)

        # view2

        view2_item = yield mdl.fetch_item(u"view2")
        self.assertEqual(view2_item.name, u"view2")
        self.assertEqual(view2_item.label, u"View 2")
        self.assertEqual(view2_item.desc, u"Second view")

        view2 = yield view2_item.fetch()
        self.assertTrue(isinstance(view2, TestView))
        self.assertTrue(view2.source is src)
        self.assertTrue(view2.aspect is not None)
        self.assertTrue(view2.view is src.views[u"view2"])
        view2_num_item = yield view2.fetch_item("num")
        view2_num = yield view2_num_item.fetch()
        self.assertTrue(view2_num.source is src)
        self.assertTrue(view2_num.view is src.views[u"view2"])
        num = yield view2_num.fetch_value()
        self.assertEqual(num, 44)
        ret = yield view2_num.update_value("66")
        self.assertEqual(ret, 66)
        self.assertEqual(src.views[u"view2"].num, 66)

        # view3

        view3_item = yield mdl.fetch_item(u"view3")
        self.assertEqual(view3_item.name, u"view3")
        self.assertEqual(view3_item.label, None)
        self.assertEqual(view3_item.desc, None)

        view3 = yield view3_item.fetch()
        self.assertTrue(isinstance(view3, TestView))
        self.assertTrue(view3.source is src)
        self.assertTrue(view3.aspect is not None)
        self.assertTrue(view3.view is None)

    @defer.inlineCallbacks
    def testDeclaredCollection(self):
        asp = DummyAspect("collec")
        src = DummySource()
        mdl = TestCollection(src, asp)

        self.assertTrue(interface.IModel.providedBy(mdl))
        self.assertFalse(hasattr(mdl, "__dict__"))

        yield self.asyncEqual(1, mdl.count_actions())
        action = yield mdl.fetch_action("action")
        self.assertTrue(isinstance(action, DummyAction))
        actions = yield mdl.fetch_actions()
        self.assertEqual(set([u"action"]),
                         set([a.name for a in actions]))
        yield self.asyncEqual(None, mdl.fetch_action("spam"))


        yield self.asyncEqual(0, mdl.count_items())
        yield self.asyncEqual(False, mdl.provides_item("spam"))
        yield self.asyncErrback(interface.NotSupported,
                                mdl.query_items)

        src.items[u"source1"] = object()
        src.items[u"source2"] = object()
        src.items[u"source3"] = object()

        yield self.asyncEqual(3, mdl.count_items())
        yield self.asyncEqual(True, mdl.provides_item("source1"))
        yield self.asyncEqual(True, mdl.provides_item(u"source1"))
        yield self.asyncEqual(False, mdl.provides_item(u"spam"))

        items = yield mdl.fetch_items()
        self.assertTrue(isinstance(items, list))
        self.assertEqual(len(items), len(src.items))
        for (k, o), item in zip(src.items.items(), items):
            self.assertFalse(hasattr(item, "__dict__"))
            self.assertEqual(item.name, k)
            self.assertTrue(isinstance(item.name, unicode))
            self.assertEqual(item.label, u"Some Child")
            self.assertTrue(isinstance(item.label, unicode))
            self.assertEqual(item.desc, u"Some dynamic child")
            self.assertTrue(isinstance(item.desc, unicode))

            def check_model(m):
                self.assertTrue(isinstance(m, DummyModel2))
                self.assertTrue(m.source is o)
                self.assertEqual(m.name, k)
                self.assertTrue(isinstance(m.name, unicode))
                self.assertEqual(m.label, u"Some Child")
                self.assertTrue(isinstance(m.label, unicode))
                self.assertEqual(m.desc, u"Some dynamic child")
                self.assertTrue(isinstance(m.desc, unicode))

            fm = yield item.fetch()
            check_model(fm)

            bm = yield item.browse()
            check_model(bm)

        source1_item = yield mdl.fetch_item("source1")
        self.assertTrue(interface.IModelItem.providedBy(source1_item))
        self.assertFalse(hasattr(source1_item, "__dict__"))
        self.assertEqual(item.name, u"source1")

        source1 = yield source1_item.fetch()
        self.assertTrue(isinstance(source1, DummyModel2))
        self.assertTrue(source1.source is src.items[u"source1"])

        yield self.asyncEqual(None, mdl.fetch_item("spam"))

    @defer.inlineCallbacks
    def testAnnotatedCollection(self):
        src = DummySource()
        mdl = TestModel(src)

        yield self.asyncEqual(True, mdl.provides_item("values"))
        mdl_item = yield mdl.fetch_item("values")
        self.assertFalse(hasattr(mdl_item, "__dict__"))
        self.assertEqual(mdl_item.name, u"values")
        self.assertTrue(isinstance(mdl_item.name, unicode))
        self.assertEqual(mdl_item.label, u"Some Values")
        self.assertTrue(isinstance(mdl_item.label, unicode))
        self.assertEqual(mdl_item.desc, u"Some dynamic values")
        self.assertTrue(isinstance(mdl_item.desc, unicode))

        src.items[u"value1"] = DummySource()
        src.items[u"value2"] = DummySource()

        mdl = yield mdl_item.fetch()
        self.assertTrue(interface.IModel.providedBy(mdl))
        self.assertFalse(hasattr(mdl, "__dict__"))
        yield self.asyncEqual(2, mdl.count_items())
        yield self.asyncEqual(True, mdl.provides_item("value1"))
        yield self.asyncEqual(True, mdl.provides_item(u"value2"))
        yield self.asyncEqual(False, mdl.provides_item(u"spam"))
        items = yield mdl.fetch_items()
        self.assertEqual(2, len(items))
        self.assertEqual(set([u"value1", u"value2"]),
                         set([i.name for i in items]))
        for i in items:
            self.assertTrue(interface.IModelItem.providedBy(i))
            self.assertFalse(hasattr(i, "__dict__"))
            self.assertTrue(isinstance(i.name, unicode))
            self.assertEqual(i.label, u"Some Value")
            self.assertTrue(isinstance(i.label, unicode))
            self.assertEqual(i.desc, u"Some dynamic value")
            self.assertTrue(isinstance(i.desc, unicode))
            fm = yield i.fetch()
            self.assertTrue(interface.IModel.providedBy(fm))
            self.assertTrue(isinstance(fm, DummyModel1))
            bm = yield i.fetch()
            self.assertTrue(interface.IModel.providedBy(bm))
            self.assertTrue(isinstance(bm, DummyModel1))

        value1_item = yield mdl.fetch_item("value1")
        value1 = yield value1_item.fetch()
        self.assertTrue(value1.source is src.items[u"value1"])

        value2_item = yield mdl.fetch_item(u"value2")
        value2 = yield value2_item.fetch()
        self.assertTrue(value2.source is src.items[u"value2"])

        yield self.asyncEqual(None, mdl.fetch_item("spam"))
