
import unittest
import platform

from copy import deepcopy

from common.platformdict import PlatformDict

is_unkonwn_platform = platform.system() not in ('Windows', 'Linux', 'Darwin')

class TestPlatformDict(unittest.TestCase):
    """
    An important utility to maintain, the PlatformDict offers a lot of
    power in a small package
    """

    def test_basic_dictionary_existence(self):
        """
        Assert the boolean checks of a Platform match that of an empty
        dictionary
        """
        empty = PlatformDict()
        self.assertFalse(empty)

        basic = PlatformDict({
            "foo" : "bar"
        })
        self.assertTrue(basic)


    def test_basic_dictionary_checkout(self):
        """
        Do additional sanity checks
        """
        simple = PlatformDict({
            "foo" : "bar",
            "baz" : [1, 2, 3]
        })

        self.assertTrue("foo" in simple) # Tests PlatformDict.__iter__()
        self.assertEqual(simple["foo"], "bar")

        self.assertTrue(isinstance(simple["baz"], list))
        self.assertEqual(len(simple["baz"]), 3)

        self.assertEqual(simple["invalid_key"], None)


    def test_platform_dict_copy(self):
        """
        Test that we can copy a PlatformDict properly
        """
        class Obj(object):
            def __init__(self, x):
                self._x = x

            @property
            def x(self):
                return self._x

            def __deepcopy__(self, memo=None):
                return Obj(self._x)

        pd = PlatformDict({
            "foo" : { "bar" : Obj(32) },
            "baz" : 1
        })

        deep_pd = deepcopy(pd)

        obj_one = pd["foo"]["bar"]
        obj_two = deep_pd["foo"]["bar"]

        self.assertEqual(obj_one.x, obj_two.x)
        self.assertNotEqual(id(obj_one), id(obj_two))


    @unittest.skipIf(is_unkonwn_platform, 'Unkown platform')
    def test_platform_routing_basics(self):
        """
        Assert that the default PlatformDict picks up this
        platform.system()
        """
        basic_dict = { "Windows" : "foo", "Linux" : "bar", "Darwin" : "baz" }
        value = basic_dict[platform.system()]

        pd = PlatformDict({ 'get_me' : deepcopy(basic_dict) })
        self.assertEqual(value, pd['get_me'])

        # This is for the simple grab
        self.assertEqual(value, PlatformDict.simple(basic_dict))


    @unittest.skipIf(is_unkonwn_platform, 'Unkown platform')
    def test_platform_unix(self):
        """
        Test custom platform setting as well as unix directive
        """
        pd = PlatformDict({
                'get_me' : {
                    'windows' : 'foo',
                    'unix' : 'bar'
                }
            },
            platform_ = 'Linux'
        )

        self.assertEqual(pd['get_me'], 'bar')


    def test_pd_to_dict(self):
        """
        Test getting the dictionary of a PlatformDict
        """
        data = { 'foo' : 'bar' }

        pd = PlatformDict(data)
        self.assertEqual(id(pd.to_dict()), id(data))
        self.assertNotEqual(id(pd.to_dict(copy=True)), id(data))


    def test_update_and_set(self):
        """
        Setting values within a platformdict with routing
        """
        pd = PlatformDict({
            'foo' : 'bar',
            'baz' : { 'windows' : 'schmoo', 'unix' : 'spanner' }
        })

        pd['foo'] = 'new_value'
        self.assertEqual(pd['foo'], 'new_value')

        self.assertEqual(len(pd), 2)

        pd.update({ 'foo' : 'another_new_value', 'okay' : { 'windows' : 'ok', 'unix' : 'ok' }})

        self.assertEqual(len(pd), 3)

        # Adding dict with platforms give us auto routing
        self.assertEqual(pd['okay'], 'ok')

        self.assertEqual(type(pd['baz']), str) # Platform routing
        pd['baz'] = [1, 2, 3]
        self.assertEqual(type(pd['baz']), list) # No routing

    def test_string(self):
        """
        Test the string output of our item
        """
        data = { "foo" : "bar" }
        self.assertEqual(str(PlatformDict(data)), str(data))


    def test_items_generator(self):
        """
        Make sure we can iterate through a PlatformDict
        """
        pd = PlatformDict({
            "foo" : "bar",
            "baz" : "schmoo",
            "okay" : { "glarg" : "spanner" }
        })


        # Items
        output = {}
        for key, value in pd.items():
            output[key] = value

        self.assertEqual(len(output), len(pd))


    def test_set_platform(self):
        """
        Make sure we can change the platform on the fly
        """
        pd = PlatformDict({'get_me' : {'windows' : 'ok', 'linux' : 'foo'}})

        pd.set_platform('Darwin')
        self.assertEqual(type(pd['get_me']), PlatformDict) # No entry would return a pd of the get_me

        pd.set_platform('Windows')
        self.assertEqual(pd['get_me'], 'ok')

        pd.set_platform('Linux')
        self.assertEqual(pd['get_me'], 'foo')


    def test_invalid_type(self):
        """
        We only support dictionaries at the moment for a root item
        """
        def _test_call():
            return PlatformDict(["fail me", "I'm a list"])

        self.assertRaises(TypeError, _test_call)
