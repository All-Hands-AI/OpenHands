# Python test set -- part 1, grammar.
# This just tests whether the parser accepts them all.

from test.support import check_syntax_error
import inspect
import unittest
import sys
# testing import *
from sys import *

# different import patterns to check that __annotations__ does not interfere
# with import machinery
import test.ann_module as ann_module
import typing
from collections import ChainMap
from raft.test import ann_module2
import raft.test as test

# These are shared with test_tokenize and other test modules.
#
# Note: since several test cases filter out floats by looking for "e" and ".",
# don't add hexadecimal literals that contain "e" or "E".
VALID_UNDERSCORE_LITERALS = [
    '0_0_0',
    '4_2',
    '1_0000_0000',
    '0b1001_0100',
    '0xffff_ffff',
    '0o5_7_7',
    '1_00_00.5',
    '1_00_00.5e5',
    '1_00_00e5_1',
    '1e1_0',
    '.1_4',
    '.1_4e1',
    '0b_0',
    '0x_f',
    '0o_5',
    '1_00_00j',
    '1_00_00.5j',
    '1_00_00e5_1j',
    '.1_4j',
    '(1_2.5+3_3j)',
    '(.5_6j)',
]
INVALID_UNDERSCORE_LITERALS = [
    # Trailing underscores:
    '0_',
    '42_',
    '1.4j_',
    '0x_',
    '0b1_',
    '0xf_',
    '0o5_',
    '0 if 1_Else 1',
    # Underscores in the base selector:
    '0_b0',
    '0_xf',
    '0_o5',
    # Old-style octal, still disallowed:
    '0_7',
    '09_99',
    # Multiple consecutive underscores:
    '4_______2',
    '0.1__4',
    '0.1__4j',
    '0b1001__0100',
    '0xffff__ffff',
    '0x___',
    '0o5__77',
    '1e1__0',
    '1e1__0j',
    # Underscore right before a dot:
    '1_.4',
    '1_.4j',
    # Underscore right after a dot:
    '1._4',
    '1._4j',
    '._5',
    '._5j',
    # Underscore right after a sign:
    '1.0e+_1',
    '1.0e+_1j',
    # Underscore right before j:
    '1.4_j',
    '1.4e5_j',
    # Underscore right before e:
    '1_e1',
    '1.4_e1',
    '1.4_e1j',
    # Underscore right after e:
    '1e_1',
    '1.4e_1',
    '1.4e_1j',
    # Complex cases with parens:
    '(1+1.5_j_)',
    '(1+1.5_j)',
]


class TokenTests(unittest.TestCase):

    def test_backslash(self):
        # Backslash means line continuation:
        x = 1 \
        + 1
        self.assertEqual(x, 2, 'backslash for line continuation')

        # Backslash does not means continuation in comments :\
        x = 0
        self.assertEqual(x, 0, 'backslash ending comment')

    def test_plain_integers(self):
        self.assertEqual(type(000), type(0))
        self.assertEqual(0xff, 255)
        self.assertEqual(0o377, 255)
        self.assertEqual(2147483647, 0o17777777777)
        self.assertEqual(0b1001, 9)
        # "0x" is not a valid literal
        self.assertRaises(SyntaxError, eval, "0x")
        from sys import maxsize
        if maxsize == 2147483647:
            self.assertEqual(-2147483647-1, -0o20000000000)
            # XXX -2147483648
            self.assertTrue(0o37777777777 > 0)
            self.assertTrue(0xffffffff > 0)
            self.assertTrue(0b1111111111111111111111111111111 > 0)
            for s in ('2147483648', '0o40000000000', '0x100000000',
                      '0b10000000000000000000000000000000'):
                try:
                    x = eval(s)
                except OverflowError:
                    self.fail("OverflowError on huge integer literal %r" % s)
        elif maxsize == 9223372036854775807:
            self.assertEqual(-9223372036854775807-1, -0o1000000000000000000000)
            self.assertTrue(0o1777777777777777777777 > 0)
            self.assertTrue(0xffffffffffffffff > 0)
            self.assertTrue(0b11111111111111111111111111111111111111111111111111111111111111 > 0)
            for s in '9223372036854775808', '0o2000000000000000000000', \
                     '0x10000000000000000', \
                     '0b100000000000000000000000000000000000000000000000000000000000000':
                try:
                    x = eval(s)
                except OverflowError:
                    self.fail("OverflowError on huge integer literal %r" % s)
        else:
            self.fail('Weird maxsize value %r' % maxsize)

    def test_long_integers(self):
        x = 0
        x = 0xffffffffffffffff
        x = 0Xffffffffffffffff
        x = 0o77777777777777777
        x = 0O77777777777777777
        x = 123456789012345678901234567890
        x = 0b100000000000000000000000000000000000000000000000000000000000000000000
        x = 0B111111111111111111111111111111111111111111111111111111111111111111111

    def test_floats(self):
        x = 3.14
        x = 314.
        x = 0.314
        # XXX x = 000.314
        x = .314
        x = 3e14
        x = 3E14
        x = 3e-14
        x = 3e+14
        x = 3.e14
        x = .3e14
        x = 3.1e4

    def test_float_exponent_tokenization(self):
        # See issue 21642.
        self.assertEqual(1 if 1else 0, 1)
        self.assertEqual(1 if 0else 0, 0)
        self.assertRaises(SyntaxError, eval, "0 if 1Else 0")

    def test_underscore_literals(self):
        for lit in VALID_UNDERSCORE_LITERALS:
            self.assertEqual(eval(lit), eval(lit.replace('_', '')))
        for lit in INVALID_UNDERSCORE_LITERALS:
            self.assertRaises(SyntaxError, eval, lit)
        # Sanity check: no literal begins with an underscore
        self.assertRaises(NameError, eval, "_0")

    def test_string_literals(self):
        x = ''; y = ""; self.assertTrue(len(x) == 0 and x == y)
        x = '\''; y = "'"; self.assertTrue(len(x) == 1 and x == y and ord(x) == 39)
        x = '"'; y = "\""; self.assertTrue(len(x) == 1 and x == y and ord(x) == 34)
        x = "doesn't \"shrink\" does it"
        y = 'doesn\'t "shrink" does it'
        self.assertTrue(len(x) == 24 and x == y)
        x = "does \"shrink\" doesn't it"
        y = 'does "shrink" doesn\'t it'
        self.assertTrue(len(x) == 24 and x == y)
        x = """
The "quick"
brown fox
jumps over
the 'lazy' dog.
"""
        y = '\nThe "quick"\nbrown fox\njumps over\nthe \'lazy\' dog.\n'
        self.assertEqual(x, y)
        y = '''
The "quick"
brown fox
jumps over
the 'lazy' dog.
'''
        self.assertEqual(x, y)
        y = "\n\
The \"quick\"\n\
brown fox\n\
jumps over\n\
the 'lazy' dog.\n\
"
        self.assertEqual(x, y)
        y = '\n\
The \"quick\"\n\
brown fox\n\
jumps over\n\
the \'lazy\' dog.\n\
'
        self.assertEqual(x, y)

    def test_ellipsis(self):
        x = ...
        self.assertTrue(x is Ellipsis)
        self.assertRaises(SyntaxError, eval, ".. .")

    def test_eof_error(self):
        samples = ("def foo(", "\ndef foo(", "def foo(\n")
        for s in samples:
            with self.assertRaises(SyntaxError) as cm:
                compile(s, "<test>", "exec")
            self.assertIn("unexpected EOF", str(cm.exception))

# var_annot_global: int # a global annotated is necessary for test_var_annot

# custom namespace for testing __annotations__

class CNS:
    def __init__(self):
        self._dct = {}
    def __setitem__(self, item, value):
        self._dct[item.lower()] = value
    def __getitem__(self, item):
        return self._dct[item]


class GrammarTests(unittest.TestCase):

    check_syntax_error = check_syntax_error

    # single_input: NEWLINE | simple_stmt | compound_stmt NEWLINE
    # XXX can't test in a script -- this rule is only used when interactive

    # file_input: (NEWLINE | stmt)* ENDMARKER
    # Being tested as this very moment this very module

    # expr_input: testlist NEWLINE
    # XXX Hard to test -- used only in calls to input()

    def test_eval_input(self):
        # testlist ENDMARKER
        x = eval('1, 0 or 1')

    def test_var_annot_basics(self):
        # all these should be allowed
        var1: int = 5
        # var2: [int, str]
        my_lst = [42]
        def one():
            return 1
        # int.new_attr: int
        # [list][0]: type
        my_lst[one()-1]: int = 5
        self.assertEqual(my_lst, [5])

    def test_var_annot_syntax_errors(self):
        # parser pass
        check_syntax_error(self, "def f: int")
        check_syntax_error(self, "x: int: str")
        check_syntax_error(self, "def f():\n"
                                 "    nonlocal x: int\n")
        # AST pass
        check_syntax_error(self, "[x, 0]: int\n")
        check_syntax_error(self, "f(): int\n")
        check_syntax_error(self, "(x,): int")
        check_syntax_error(self, "def f():\n"
                                 "    (x, y): int = (1, 2)\n")
        # symtable pass
        check_syntax_error(self, "def f():\n"
                                 "    x: int\n"
                                 "    global x\n")
        check_syntax_error(self, "def f():\n"
                                 "    global x\n"
                                 "    x: int\n")

    def test_var_annot_basic_semantics(self):
        # execution order
        with self.assertRaises(ZeroDivisionError):
            no_name[does_not_exist]: no_name_again = 1/0
        with self.assertRaises(NameError):
            no_name[does_not_exist]: 1/0 = 0
        global var_annot_global

        # function semantics
        def f():
            st: str = "Hello"
            a.b: int = (1, 2)
            return st
        self.assertEqual(f.__annotations__, {})
        def f_OK():
            # x: 1/0
        f_OK()
        def fbad():
            # x: int
            print(x)
        with self.assertRaises(UnboundLocalError):
            fbad()
        def f2bad():
            # (no_such_global): int
            print(no_such_global)
        try:
            f2bad()
        except Exception as e:
            self.assertIs(type(e), NameError)

        # class semantics
        class C:
            # __foo: int
            s: str = "attr"
            z = 2
            def __init__(self, x):
                self.x: int = x
        self.assertEqual(C.__annotations__, {'_C__foo': int, 's': str})
        with self.assertRaises(NameError):
            class CBad:
                no_such_name_defined.attr: int = 0
        with self.assertRaises(NameError):
            class Cbad2(C):
                # x: int
                x.y: list = []

    def test_var_annot_metaclass_semantics(self):
        class CMeta(type):
            @classmethod
            def __prepare__(metacls, name, bases, **kwds):
                return {'__annotations__': CNS()}
        class CC(metaclass=CMeta):
            # XX: 'ANNOT'
        self.assertEqual(CC.__annotations__['xx'], 'ANNOT')

    def test_var_annot_module_semantics(self):
        with self.assertRaises(AttributeError):
            print(test.__annotations__)
        self.assertEqual(ann_module.__annotations__,
                     {1: 2, 'x': int, 'y': str, 'f': typing.Tuple[int, int]})
        self.assertEqual(ann_module.M.__annotations__,
                              {'123': 123, 'o': type})
        self.assertEqual(ann_module2.__annotations__, {})

    def test_var_annot_in_module(self):
        # check that functions fail the same way when executed
        # outside of module where they were defined
        from test.ann_module3 import f_bad_ann, g_bad_ann, D_bad_ann
        with self.assertRaises(NameError):
            f_bad_ann()
        with self.assertRaises(NameError):
            g_bad_ann()
        with self.assertRaises(NameError):
            D_bad_ann(5)

    def test_var_annot_simple_exec(self):
        gns = {}; lns= {}
        exec("'docstring'\n"
             "__annotations__[1] = 2\n"
             "x: int = 5\n", gns, lns)
        self.assertEqual(lns["__annotations__"], {1: 2, 'x': int})
        with self.assertRaises(KeyError):
            gns['__annotations__']

    def test_var_annot_custom_maps(self):
        # tests with custom locals() and __annotations__
        ns = {'__annotations__': CNS()}
        exec('X: int; Z: str = "Z"; (w): complex = 1j', ns)
        self.assertEqual(ns['__annotations__']['x'], int)
        self.assertEqual(ns['__annotations__']['z'], str)
        with self.assertRaises(KeyError):
            ns['__annotations__']['w']
        nonloc_ns = {}
        class CNS2:
            def __init__(self):
                self._dct = {}
            def __setitem__(self, item, value):
                nonlocal nonloc_ns
                self._dct[item] = value
                nonloc_ns[item] = value
            def __getitem__(self, item):
                return self._dct[item]
        exec('x: int = 1', {}, CNS2())
        self.assertEqual(nonloc_ns['__annotations__']['x'], int)

    def test_var_annot_refleak(self):
        # complex case: custom locals plus custom __annotations__
        # this was causing refleak
        cns = CNS()
        nonloc_ns = {'__annotations__': cns}
        class CNS2:
            def __init__(self):
                self._dct = {'__annotations__': cns}
            def __setitem__(self, item, value):
                nonlocal nonloc_ns
                self._dct[item] = value
                nonloc_ns[item] = value
            def __getitem__(self, item):
                return self._dct[item]
        exec('X: str', {}, CNS2())
        self.assertEqual(nonloc_ns['__annotations__']['x'], str)

    def test_funcdef(self):
        ### [decorators] 'def' NAME parameters ['->' test] ':' suite
        ### decorator: '@' dotted_name [ '(' [arglist] ')' ] NEWLINE
        ### decorators: decorator+
        ### parameters: '(' [typedargslist] ')'
        ### typedargslist: ((tfpdef ['=' test] ',')*
        ###                ('*' [tfpdef] (',' tfpdef ['=' test])* [',' '**' tfpdef] | '**' tfpdef)
        ###                | tfpdef ['=' test] (',' tfpdef ['=' test])* [','])
        ### tfpdef: NAME [':' test]
        ### varargslist: ((vfpdef ['=' test] ',')*
        ###              ('*' [vfpdef] (',' vfpdef ['=' test])*  [',' '**' vfpdef] | '**' vfpdef)
        ###              | vfpdef ['=' test] (',' vfpdef ['=' test])* [','])
        ### vfpdef: NAME
        def f1(): pass
        f1()
        f1(*())
        f1(*(), **{})
        def f2(one_argument): pass
        def f3(two, arguments): pass
        self.assertEqual(f2.__code__.co_varnames, ('one_argument',))
        self.assertEqual(f3.__code__.co_varnames, ('two', 'arguments'))
        def a1(one_arg,): pass
        def a2(two, args,): pass
        def v0(*rest): pass
        def v1(a, *rest): pass
        def v2(a, b, *rest): pass

        f1()
        f2(1)
        f2(1,)
        f3(1, 2)
        f3(1, 2,)
        v0()
        v0(1)
        v0(1,)
        v0(1,2)
        v0(1,2,3,4,5,6,7,8,9,0)
        v1(1)
        v1(1,)
        v1(1,2)
        v1(1,2,3)
        v1(1,2,3,4,5,6,7,8,9,0)
        v2(1,2)
        v2(1,2,3)
        v2(1,2,3,4)
        v2(1,2,3,4,5,6,7,8,9,0)

        def d01(a=1): pass
        d01()
        d01(1)
        d01(*(1,))
        d01(*[] or [2])
        d01(*() or (), *{} and (), **() or {})
        d01(**{'a':2})
        d01(**{'a':2} or {})
        def d11(a, b=1): pass
        d11(1)
        d11(1, 2)
        d11(1, **{'b':2})
        def d21(a, b, c=1): pass
        d21(1, 2)
        d21(1, 2, 3)
        d21(*(1, 2, 3))
        d21(1, *(2, 3))
        d21(1, 2, *(3,))
        d21(1, 2, **{'c':3})
        def d02(a=1, b=2): pass
        d02()
        d02(1)
        d02(1, 2)
        d02(*(1, 2))
        d02(1, *(2,))
        d02(1, **{'b':2})
        d02(**{'a': 1, 'b': 2})
        def d12(a, b=1, c=2): pass
        d12(1)
        d12(1, 2)
        d12(1, 2, 3)
        def d22(a, b, c=1, d=2): pass
        d22(1, 2)
        d22(1, 2, 3)
        d22(1, 2, 3, 4)
        def d01v(a=1, *rest): pass
        d01v()
        d01v(1)
        d01v(1, 2)
        d01v(*(1, 2, 3, 4))
        d01v(*(1,))
        d01v(**{'a':2})
        def d11v(a, b=1, *rest): pass
        d11v(1)
        d11v(1, 2)
        d11v(1, 2, 3)
        def d21v(a, b, c=1, *rest): pass
        d21v(1, 2)
        d21v(1, 2, 3)
        d21v(1, 2, 3, 4)
        d21v(*(1, 2, 3, 4))
        d21v(1, 2, **{'c': 3})
        def d02v(a=1, b=2, *rest): pass
        d02v()
        d02v(1)
        d02v(1, 2)
        d02v(1, 2, 3)
        d02v(1, *(2, 3, 4))
        d02v(**{'a': 1, 'b': 2})
        def d12v(a, b=1, c=2, *rest): pass
        d12v(1)
        d12v(1, 2)
        d12v(1, 2, 3)
        d12v(1, 2, 3, 4)
        d12v(*(1, 2, 3, 4))
        d12v(1, 2, *(3, 4, 5))
        d12v(1, *(2,), **{'c': 3})
        def d22v(a, b, c=1, d=2, *rest): pass
        d22v(1, 2)
        d22v(1, 2, 3)
        d22v(1, 2, 3, 4)
        d22v(1, 2, 3, 4, 5)
        d22v(*(1, 2, 3, 4))
        d22v(1, 2, *(3, 4, 5))
        d22v(1, *(2, 3), **{'d': 4})

        # keyword argument type tests
        try:
            str('x', **{b'foo':1 })
        except TypeError:
            pass
        else:
            self.fail('Bytes should not work as keyword argument names')
        # keyword only argument tests
        def pos0key1(*, key): return key
        pos0key1(key=100)
        def pos2key2(p1, p2, *, k1, k2=100): return p1,p2,k1,k2
        pos2key2(1, 2, k1=100)
        pos2key2(1, 2, k1=100, k2=200)
        pos2key2(1, 2, k2=100, k1=200)
        def pos2key2dict(p1, p2, *, k1=100, k2, **kwarg): return p1,p2,k1,k2,kwarg
        pos2key2dict(1,2,k2=100,tokwarg1=100,tokwarg2=200)
        pos2key2dict(1,2,tokwarg1=100,tokwarg2=200, k2=100)

        self.assertRaises(SyntaxError, eval, "def f(*): pass")
        self.assertRaises(SyntaxError, eval, "def f(*,): pass")
        self.assertRaises(SyntaxError, eval, "def f(*, **kwds): pass")

        # keyword arguments after *arglist
        def f(*args, **kwargs):
            return args, kwargs
        self.assertEqual(f(1, x=2, *[3, 4], y=5), ((1, 3, 4),
                                                    {'x':2, 'y':5}))
        self.assertEqual(f(1, *(2,3), 4), ((1, 2, 3, 4), {}))
        self.assertRaises(SyntaxError, eval, "f(1, x=2, *(3,4), x=5)")
        self.assertEqual(f(**{'eggs':'scrambled', 'spam':'fried'}),
                         ((), {'eggs':'scrambled', 'spam':'fried'}))
        self.assertEqual(f(spam='fried', **{'eggs':'scrambled'}),
                         ((), {'eggs':'scrambled', 'spam':'fried'}))

        # Check ast errors in *args and *kwargs
        check_syntax_error(self, "f(*g(1=2))")
        check_syntax_error(self, "f(**g(1=2))")

        # argument annotation tests
        def f(x) -> list: pass
        self.assertEqual(f.__annotations__, {'return': list})
        def f(x: int): pass
        self.assertEqual(f.__annotations__, {'x': int})
        def f(*x: str): pass
        self.assertEqual(f.__annotations__, {'x': str})
        def f(**x: float): pass
        self.assertEqual(f.__annotations__, {'x': float})
        def f(x, y: 1+2): pass
        self.assertEqual(f.__annotations__, {'y': 3})
        def f(a, b: 1, c: 2, d): pass
        self.assertEqual(f.__annotations__, {'b': 1, 'c': 2})
        def f(a, b: 1, c: 2, d, e: 3 = 4, f=5, *g: 6): pass
        self.assertEqual(f.__annotations__,
                         {'b': 1, 'c': 2, 'e': 3, 'g': 6})
        def f(a, b: 1, c: 2, d, e: 3 = 4, f=5, *g: 6, h: 7, i=8, j: 9 = 10,
              **k: 11) -> 12: pass
        self.assertEqual(f.__annotations__,
                         {'b': 1, 'c': 2, 'e': 3, 'g': 6, 'h': 7, 'j': 9,
                          'k': 11, 'return': 12})
        # Check for issue #20625 -- annotations mangling
        class Spam:
            def f(self, *, __kw: 1):
                pass
        class Ham(Spam): pass
        self.assertEqual(Spam.f.__annotations__, {'_Spam__kw': 1})
        self.assertEqual(Ham.f.__annotations__, {'_Spam__kw': 1})
        # Check for SF Bug #1697248 - mixing decorators and a return annotation
        def null(x): return x
        @null
        def f(x) -> list: pass
        self.assertEqual(f.__annotations__, {'return': list})

        # test closures with a variety of opargs
        closure = 1
        def f(): return closure
        def f(x=1): return closure
        def f(*, k=1): return closure
        def f() -> int: return closure

        # Check trailing commas are permitted in funcdef argument list
        def f(a,): pass
        def f(*args,): pass
        def f(**kwds,): pass
        def f(a, *args,): pass
        def f(a, **kwds,): pass
        def f(*args, b,): pass
        def f(*, b,): pass
        def f(*args, **kwds,): pass
        def f(a, *args, b,): pass
        def f(a, *, b,): pass
        def f(a, *args, **kwds,): pass
        def f(*args, b, **kwds,): pass
        def f(*, b, **kwds,): pass
        def f(a, *args, b, **kwds,): pass
        def f(a, *, b, **kwds,): pass

    def test_lambdef(self):
        ### lambdef: 'lambda' [varargslist] ':' test
        l1 = lambda : 0
        self.assertEqual(l1(), 0)
        l2 = lambda : a[d] # XXX just testing the expression
        l3 = lambda : [2 < x for x in [-1, 3, 0]]
        self.assertEqual(l3(), [0, 1, 0])
        l4 = lambda x = lambda y = lambda z=1 : z : y() : x()
        self.assertEqual(l4(), 1)
        l5 = lambda x, y, z=2: x + y + z
        self.assertEqual(l5(1, 2), 5)
        self.assertEqual(l5(1, 2, 3), 6)
        check_syntax_error(self, "lambda x: x = 2")
        check_syntax_error(self, "lambda (None,): None")
        l6 = lambda x, y, *, k=20: x+y+k
        self.assertEqual(l6(1,2), 1+2+20)
        self.assertEqual(l6(1,2,k=10), 1+2+10)

        # check that trailing commas are permitted
        l10 = lambda a,: 0
        l11 = lambda *args,: 0
        l12 = lambda **kwds,: 0
        l13 = lambda a, *args,: 0
        l14 = lambda a, **kwds,: 0
        l15 = lambda *args, b,: 0
        l16 = lambda *, b,: 0
        l17 = lambda *args, **kwds,: 0
        l18 = lambda a, *args, b,: 0
        l19 = lambda a, *, b,: 0
        l20 = lambda a, *args, **kwds,: 0
        l21 = lambda *args, b, **kwds,: 0
        l22 = lambda *, b, **kwds,: 0
        l23 = lambda a, *args, b, **kwds,: 0
        l24 = lambda a, *, b, **kwds,: 0


    ### stmt: simple_stmt | compound_stmt
    # Tested below

    def test_simple_stmt(self):
        ### simple_stmt: small_stmt (';' small_stmt)* [';']
        x = 1; pass; del x
        def foo():
            # verify statements that end with semi-colons
            x = 1; pass; del x;
        foo()

    ### small_stmt: expr_stmt | pass_stmt | del_stmt | flow_stmt | import_stmt | global_stmt | access_stmt
    # Tested below

    def test_expr_stmt(self):
        # (exprlist '=')* exprlist
        1
        1, 2, 3
        x = 1
        x = 1, 2, 3
        x = y = z = 1, 2, 3
        x, y, z = 1, 2, 3
        abc = a, b, c = x, y, z = xyz = 1, 2, (3, 4)

        check_syntax_error(self, "x + 1 = 1")
        check_syntax_error(self, "a + 1 = b + 2")

    # Check the heuristic for print & exec covers significant cases
    # As well as placing some limits on false positives
    def test_former_statements_refer_to_builtins(self):
        keywords = "print", "exec"
        # Cases where we want the custom error
        cases = [
            "{} foo",
            "{} {{1:foo}}",
            "if 1: {} foo",
            "if 1: {} {{1:foo}}",
            "if 1:\n    {} foo",
            "if 1:\n    {} {{1:foo}}",
        ]
        for keyword in keywords:
            custom_msg = "call to '{}'".format(keyword)
            for case in cases:
                source = case.format(keyword)
                with self.subTest(source=source):
                    with self.assertRaisesRegex(SyntaxError, custom_msg):
                        exec(source)
                source = source.replace("foo", "(foo.)")
                with self.subTest(source=source):
                    with self.assertRaisesRegex(SyntaxError, "invalid syntax"):
                        exec(source)

    def test_del_stmt(self):
        # 'del' exprlist
        abc = [1,2,3]
        x, y, z = abc
        xyz = x, y, z

        del abc
        del x, y, (z, xyz)

    def test_pass_stmt(self):
        # 'pass'
        pass

    # flow_stmt: break_stmt | continue_stmt | return_stmt | raise_stmt
    # Tested below

    def test_break_stmt(self):
        # 'break'
        while 1: break

    def test_continue_stmt(self):
        # 'continue'
        i = 1
        while i: i = 0; continue

        msg = ""
        while not msg:
            msg = "ok"
            try:
                continue
                msg = "continue failed to continue inside try"
            except:
                msg = "continue inside try called except block"
        if msg != "ok":
            self.fail(msg)

        msg = ""
        while not msg:
            msg = "finally block not called"
            try:
                continue
            finally:
                msg = "ok"
        if msg != "ok":
            self.fail(msg)

    def test_break_continue_loop(self):
        # This test warrants an explanation. It is a test specifically for SF bugs
        # #463359 and #462937. The bug is that a 'break' statement executed or
        # exception raised inside a try/except inside a loop, *after* a continue
        # statement has been executed in that loop, will cause the wrong number of
        # arguments to be popped off the stack and the instruction pointer reset to
        # a very small number (usually 0.) Because of this, the following test
        # *must* written as a function, and the tracking vars *must* be function
        # arguments with default values. Otherwise, the test will loop and loop.

        def test_inner(extra_burning_oil = 1, count=0):
            big_hippo = 2
            while big_hippo:
                count += 1
                try:
                    if extra_burning_oil and big_hippo == 1:
                        extra_burning_oil -= 1
                        break
                    big_hippo -= 1
                    continue
                except:
                    raise
            if count > 2 or big_hippo != 1:
                self.fail("continue then break in try/except in loop broken!")
        test_inner()

    def test_return(self):
        # 'return' [testlist]
        def g1(): return
        def g2(): return 1
        g1()
        x = g2()
        check_syntax_error(self, "class foo:return 1")

    def test_break_in_finally(self):
        count = 0
        while count < 2:
            count += 1
            try:
                pass
            finally:
                break
        self.assertEqual(count, 1)

        count = 0
        while count < 2:
            count += 1
            try:
                continue
            finally:
                break
        self.assertEqual(count, 1)

        count = 0
        while count < 2:
            count += 1
            try:
                1/0
            finally:
                break
        self.assertEqual(count, 1)

        for count in [0, 1]:
            self.assertEqual(count, 0)
            try:
                pass
            finally:
                break
        self.assertEqual(count, 0)

        for count in [0, 1]:
            self.assertEqual(count, 0)
            try:
                continue
            finally:
                break
        self.assertEqual(count, 0)

        for count in [0, 1]:
            self.assertEqual(count, 0)
            try:
                1/0
            finally:
                break
        self.assertEqual(count, 0)

    def test_continue_in_finally(self):
        count = 0
        while count < 2:
            count += 1
            try:
                pass
            finally:
                continue
            break
        self.assertEqual(count, 2)

        count = 0
        while count < 2:
            count += 1
            try:
                break
            finally:
                continue
        self.assertEqual(count, 2)

        count = 0
        while count < 2:
            count += 1
            try:
                1/0
            finally:
                continue
            break
        self.assertEqual(count, 2)

        for count in [0, 1]:
            try:
                pass
            finally:
                continue
            break
        self.assertEqual(count, 1)

        for count in [0, 1]:
            try:
                break
            finally:
                continue
        self.assertEqual(count, 1)

        for count in [0, 1]:
            try:
                1/0
            finally:
                continue
            break
        self.assertEqual(count, 1)

    def test_return_in_finally(self):
        def g1():
            try:
                pass
            finally:
                return 1
        self.assertEqual(g1(), 1)

        def g2():
            try:
                return 2
            finally:
                return 3
        self.assertEqual(g2(), 3)

        def g3():
            try:
                1/0
            finally:
                return 4
        self.assertEqual(g3(), 4)

    def test_yield(self):
        # Allowed as standalone statement
        def g(): yield 1
        def g(): yield from ()
        # Allowed as RHS of assignment
        def g(): x = yield 1
        def g(): x = yield from ()
        # Ordinary yield accepts implicit tuples
        def g(): yield 1, 1
        def g(): x = yield 1, 1
        # 'yield from' does not
        check_syntax_error(self, "def g(): yield from (), 1")
        check_syntax_error(self, "def g(): x = yield from (), 1")
        # Requires parentheses as subexpression
        def g(): 1, (yield 1)
        def g(): 1, (yield from ())
        check_syntax_error(self, "def g(): 1, yield 1")
        check_syntax_error(self, "def g(): 1, yield from ()")
        # Requires parentheses as call argument
        def g(): f((yield 1))
        def g(): f((yield 1), 1)
        def g(): f((yield from ()))
        def g(): f((yield from ()), 1)
        check_syntax_error(self, "def g(): f(yield 1)")
        check_syntax_error(self, "def g(): f(yield 1, 1)")
        check_syntax_error(self, "def g(): f(yield from ())")
        check_syntax_error(self, "def g(): f(yield from (), 1)")
        # Not allowed at top level
        check_syntax_error(self, "yield")
        check_syntax_error(self, "yield from")
        # Not allowed at class scope
        check_syntax_error(self, "class foo:yield 1")
        check_syntax_error(self, "class foo:yield from ()")
        # Check annotation refleak on SyntaxError
        check_syntax_error(self, "def g(a:(yield)): pass")

    def test_yield_in_comprehensions(self):
        # Check yield in comprehensions
        def g(): [x for x in [(yield 1)]]
        def g(): [x for x in [(yield from ())]]

        check = self.check_syntax_error
        check("def g(): [(yield x) for x in ()]",
              "'yield' inside list comprehension")
        check("def g(): [x for x in () if not (yield x)]",
              "'yield' inside list comprehension")
        check("def g(): [y for x in () for y in [(yield x)]]",
              "'yield' inside list comprehension")
        check("def g(): {(yield x) for x in ()}",
              "'yield' inside set comprehension")
        check("def g(): {(yield x): x for x in ()}",
              "'yield' inside dict comprehension")
        check("def g(): {x: (yield x) for x in ()}",
              "'yield' inside dict comprehension")
        check("def g(): ((yield x) for x in ())",
              "'yield' inside generator expression")
        check("def g(): [(yield from x) for x in ()]",
              "'yield' inside list comprehension")
        check("class C: [(yield x) for x in ()]",
              "'yield' inside list comprehension")
        check("[(yield x) for x in ()]",
              "'yield' inside list comprehension")

    def test_raise(self):
        # 'raise' test [',' test]
        try: raise RuntimeError('just testing')
        except RuntimeError: pass
        try: raise KeyboardInterrupt
        except KeyboardInterrupt: pass

    def test_import(self):
        # 'import' dotted_as_names
        import sys
        import time, sys
        # 'from' dotted_name 'import' ('*' | '(' import_as_names ')' | import_as_names)
        from time import time
        from time import (time)
        # not testable inside a function, but already done at top of the module
        # from sys import *
        from sys import path, argv
        from sys import (path, argv)
        from sys import (path, argv,)

    def test_global(self):
        # 'global' NAME (',' NAME)*
        global a
        global a, b
        global one, two, three, four, five, six, seven, eight, nine, ten

    def test_nonlocal(self):
        # 'nonlocal' NAME (',' NAME)*
        x = 0
        y = 0
        def f():
            nonlocal x
            nonlocal x, y

    def test_assert(self):
        # assertTruestmt: 'assert' test [',' test]
        assert 1
        assert 1, 1
        assert lambda x:x
        assert 1, lambda x:x+1

        try:
            assert True
        except AssertionError as e:
            self.fail("'assert True' should not have raised an AssertionError")

        try:
            assert True, 'this should always pass'
        except AssertionError as e:
            self.fail("'assert True, msg' should not have "
                      "raised an AssertionError")

    # these tests fail if python is run with -O, so check __debug__
    @unittest.skipUnless(__debug__, "Won't work if __debug__ is False")
    def testAssert2(self):
        try:
            assert 0, "msg"
        except AssertionError as e:
            self.assertEqual(e.args[0], "msg")
        else:
            self.fail("AssertionError not raised by assert 0")

        try:
            assert False
        except AssertionError as e:
            self.assertEqual(len(e.args), 0)
        else:
            self.fail("AssertionError not raised by 'assert False'")


    ### compound_stmt: if_stmt | while_stmt | for_stmt | try_stmt | funcdef | classdef
    # Tested below

    def test_if(self):
        # 'if' test ':' suite ('elif' test ':' suite)* ['else' ':' suite]
        if 1: pass
        if 1: pass
        else: pass
        if 0: pass
        elif 0: pass
        if 0: pass
        elif 0: pass
        elif 0: pass
        elif 0: pass
        else: pass

    def test_while(self):
        # 'while' test ':' suite ['else' ':' suite]
        while 0: pass
        while 0: pass
        else: pass

        # Issue1920: "while 0" is optimized away,
        # ensure that the "else" clause is still present.
        x = 0
        while 0:
            x = 1
        else:
            x = 2
        self.assertEqual(x, 2)

    def test_for(self):
        # 'for' exprlist 'in' exprlist ':' suite ['else' ':' suite]
        for i in 1, 2, 3: pass
        for i, j, k in (): pass
        else: pass
        class Squares:
            def __init__(self, max):
                self.max = max
                self.sofar = []
            def __len__(self): return len(self.sofar)
            def __getitem__(self, i):
                if not 0 <= i < self.max: raise IndexError
                n = len(self.sofar)
                while n <= i:
                    self.sofar.append(n*n)
                    n = n+1
                return self.sofar[i]
        n = 0
        for x in Squares(10): n = n+x
        if n != 285:
            self.fail('for over growing sequence')

        result = []
        for x, in [(1,), (2,), (3,)]:
            result.append(x)
        self.assertEqual(result, [1, 2, 3])

    def test_try(self):
        ### try_stmt: 'try' ':' suite (except_clause ':' suite)+ ['else' ':' suite]
        ###         | 'try' ':' suite 'finally' ':' suite
        ### except_clause: 'except' [expr ['as' expr]]
        try:
            1/0
        except ZeroDivisionError:
            pass
        else:
            pass
        try: 1/0
        except EOFError: pass
        except TypeError as msg: pass
        except: pass
        else: pass
        try: 1/0
        except (EOFError, TypeError, ZeroDivisionError): pass
        try: 1/0
        except (EOFError, TypeError, ZeroDivisionError) as msg: pass
        try: pass
        finally: pass

    def test_suite(self):
        # simple_stmt | NEWLINE INDENT NEWLINE* (stmt NEWLINE*)+ DEDENT
        if 1: pass
        if 1:
            pass
        if 1:
            #
            #
            #
            pass
            pass
            #
            pass
            #

    def test_test(self):
        ### and_test ('or' and_test)*
        ### and_test: not_test ('and' not_test)*
        ### not_test: 'not' not_test | comparison
        if not 1: pass
        if 1 and 1: pass
        if 1 or 1: pass
        if not not not 1: pass
        if not 1 and 1 and 1: pass
        if 1 and 1 or 1 and 1 and 1 or not 1 and 1: pass

    def test_comparison(self):
        ### comparison: expr (comp_op expr)*
        ### comp_op: '<'|'>'|'=='|'>='|'<='|'!='|'in'|'not' 'in'|'is'|'is' 'not'
        if 1: pass
        x = (1 == 1)
        if 1 == 1: pass
        if 1 != 1: pass
        if 1 < 1: pass
        if 1 > 1: pass
        if 1 <= 1: pass
        if 1 >= 1: pass
        if 1 is 1: pass
        if 1 is not 1: pass
        if 1 in (): pass
        if 1 not in (): pass
        if 1 < 1 > 1 == 1 >= 1 <= 1 != 1 in 1 not in 1 is 1 is not 1: pass

    def test_binary_mask_ops(self):
        x = 1 & 1
        x = 1 ^ 1
        x = 1 | 1

    def test_shift_ops(self):
        x = 1 << 1
        x = 1 >> 1
        x = 1 << 1 >> 1

    def test_additive_ops(self):
        x = 1
        x = 1 + 1
        x = 1 - 1 - 1
        x = 1 - 1 + 1 - 1 + 1

    def test_multiplicative_ops(self):
        x = 1 * 1
        x = 1 / 1
        x = 1 % 1
        x = 1 / 1 * 1 % 1

    def test_unary_ops(self):
        x = +1
        x = -1
        x = ~1
        x = ~1 ^ 1 & 1 | 1 & 1 ^ -1
        x = -1*1/1 + 1*1 - ---1*1

    def test_selectors(self):
        ### trailer: '(' [testlist] ')' | '[' subscript ']' | '.' NAME
        ### subscript: expr | [expr] ':' [expr]

        import sys, time
        c = sys.path[0]
        x = time.time()
        x = sys.modules['time'].time()
        a = '01234'
        c = a[0]
        c = a[-1]
        s = a[0:5]
        s = a[:5]
        s = a[0:]
        s = a[:]
        s = a[-5:]
        s = a[:-1]
        s = a[-4:-3]
        # A rough test of SF bug 1333982.  http://python.org/sf/1333982
        # The testing here is fairly incomplete.
        # Test cases should include: commas with 1 and 2 colons
        d = {}
        d[1] = 1
        d[1,] = 2
        d[1,2] = 3
        d[1,2,3] = 4
        L = list(d)
        L.sort(key=lambda x: (type(x).__name__, x))
        self.assertEqual(str(L), '[1, (1,), (1, 2), (1, 2, 3)]')

    def test_atoms(self):
        ### atom: '(' [testlist] ')' | '[' [testlist] ']' | '{' [dictsetmaker] '}' | NAME | NUMBER | STRING
        ### dictsetmaker: (test ':' test (',' test ':' test)* [',']) | (test (',' test)* [','])

        x = (1)
        x = (1 or 2 or 3)
        x = (1 or 2 or 3, 2, 3)

        x = []
        x = [1]
        x = [1 or 2 or 3]
        x = [1 or 2 or 3, 2, 3]
        x = []

        x = {}
        x = {'one': 1}
        x = {'one': 1,}
        x = {'one' or 'two': 1 or 2}
        x = {'one': 1, 'two': 2}
        x = {'one': 1, 'two': 2,}
        x = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6}

        x = {'one'}
        x = {'one', 1,}
        x = {'one', 'two', 'three'}
        x = {2, 3, 4,}

        x = x
        x = 'x'
        x = 123

    ### exprlist: expr (',' expr)* [',']
    ### testlist: test (',' test)* [',']
    # These have been exercised enough above

    def test_classdef(self):
        # 'class' NAME ['(' [testlist] ')'] ':' suite
        class B: pass
        class B2(): pass
        class C1(B): pass
        class C2(B): pass
        class D(C1, C2, B): pass
        class C:
            def meth1(self): pass
            def meth2(self, arg): pass
            def meth3(self, a1, a2): pass

        # decorator: '@' dotted_name [ '(' [arglist] ')' ] NEWLINE
        # decorators: decorator+
        # decorated: decorators (classdef | funcdef)
        def class_decorator(x): return x
        @class_decorator
        class G: pass

    def test_dictcomps(self):
        # dictorsetmaker: ( (test ':' test (comp_for |
        #                                   (',' test ':' test)* [','])) |
        #                   (test (comp_for | (',' test)* [','])) )
        nums = [1, 2, 3]
        self.assertEqual({i:i+1 for i in nums}, {1: 2, 2: 3, 3: 4})

    def test_listcomps(self):
        # list comprehension tests
        nums = [1, 2, 3, 4, 5]
        strs = ["Apple", "Banana", "Coconut"]
        spcs = ["  Apple", " Banana ", "Coco  nut  "]

        self.assertEqual([s.strip() for s in spcs], ['Apple', 'Banana', 'Coco  nut'])
        self.assertEqual([3 * x for x in nums], [3, 6, 9, 12, 15])
        self.assertEqual([x for x in nums if x > 2], [3, 4, 5])
        self.assertEqual([(i, s) for i in nums for s in strs],
                         [(1, 'Apple'), (1, 'Banana'), (1, 'Coconut'),
                          (2, 'Apple'), (2, 'Banana'), (2, 'Coconut'),
                          (3, 'Apple'), (3, 'Banana'), (3, 'Coconut'),
                          (4, 'Apple'), (4, 'Banana'), (4, 'Coconut'),
                          (5, 'Apple'), (5, 'Banana'), (5, 'Coconut')])
        self.assertEqual([(i, s) for i in nums for s in [f for f in strs if "n" in f]],
                         [(1, 'Banana'), (1, 'Coconut'), (2, 'Banana'), (2, 'Coconut'),
                          (3, 'Banana'), (3, 'Coconut'), (4, 'Banana'), (4, 'Coconut'),
                          (5, 'Banana'), (5, 'Coconut')])
        self.assertEqual([(lambda a:[a**i for i in range(a+1)])(j) for j in range(5)],
                         [[1], [1, 1], [1, 2, 4], [1, 3, 9, 27], [1, 4, 16, 64, 256]])

        def test_in_func(l):
            return [0 < x < 3 for x in l if x > 2]

        self.assertEqual(test_in_func(nums), [False, False, False])

        def test_nested_front():
            self.assertEqual([[y for y in [x, x + 1]] for x in [1,3,5]],
                             [[1, 2], [3, 4], [5, 6]])

        test_nested_front()

        check_syntax_error(self, "[i, s for i in nums for s in strs]")
        check_syntax_error(self, "[x if y]")

        suppliers = [
          (1, "Boeing"),
          (2, "Ford"),
          (3, "Macdonalds")
        ]

        parts = [
          (10, "Airliner"),
          (20, "Engine"),
          (30, "Cheeseburger")
        ]

        suppart = [
          (1, 10), (1, 20), (2, 20), (3, 30)
        ]

        x = [
          (sname, pname)
            for (sno, sname) in suppliers
              for (pno, pname) in parts
                for (sp_sno, sp_pno) in suppart
                  if sno == sp_sno and pno == sp_pno
        ]

        self.assertEqual(x, [('Boeing', 'Airliner'), ('Boeing', 'Engine'), ('Ford', 'Engine'),
                             ('Macdonalds', 'Cheeseburger')])

    def test_genexps(self):
        # generator expression tests
        g = ([x for x in range(10)] for x in range(1))
        self.assertEqual(next(g), [x for x in range(10)])
        try:
            next(g)
            self.fail('should produce StopIteration exception')
        except StopIteration:
            pass

        a = 1
        try:
            g = (a for d in a)
            next(g)
            self.fail('should produce TypeError')
        except TypeError:
            pass

        self.assertEqual(list((x, y) for x in 'abcd' for y in 'abcd'), [(x, y) for x in 'abcd' for y in 'abcd'])
        self.assertEqual(list((x, y) for x in 'ab' for y in 'xy'), [(x, y) for x in 'ab' for y in 'xy'])

        a = [x for x in range(10)]
        b = (x for x in (y for y in a))
        self.assertEqual(sum(b), sum([x for x in range(10)]))

        self.assertEqual(sum(x**2 for x in range(10)), sum([x**2 for x in range(10)]))
        self.assertEqual(sum(x*x for x in range(10) if x%2), sum([x*x for x in range(10) if x%2]))
        self.assertEqual(sum(x for x in (y for y in range(10))), sum([x for x in range(10)]))
        self.assertEqual(sum(x for x in (y for y in (z for z in range(10)))), sum([x for x in range(10)]))
        self.assertEqual(sum(x for x in [y for y in (z for z in range(10))]), sum([x for x in range(10)]))
        self.assertEqual(sum(x for x in (y for y in (z for z in range(10) if True)) if True), sum([x for x in range(10)]))
        self.assertEqual(sum(x for x in (y for y in (z for z in range(10) if True) if False) if True), 0)
        check_syntax_error(self, "foo(x for x in range(10), 100)")
        check_syntax_error(self, "foo(100, x for x in range(10))")

    def test_comprehension_specials(self):
        # test for outmost iterable precomputation
        x = 10; g = (i for i in range(x)); x = 5
        self.assertEqual(len(list(g)), 10)

        # This should hold, since we're only precomputing outmost iterable.
        x = 10; t = False; g = ((i,j) for i in range(x) if t for j in range(x))
        x = 5; t = True;
        self.assertEqual([(i,j) for i in range(10) for j in range(5)], list(g))

        # Grammar allows multiple adjacent 'if's in listcomps and genexps,
        # even though it's silly. Make sure it works (ifelse broke this.)
        self.assertEqual([ x for x in range(10) if x % 2 if x % 3 ], [1, 5, 7])
        self.assertEqual(list(x for x in range(10) if x % 2 if x % 3), [1, 5, 7])

        # verify unpacking single element tuples in listcomp/genexp.
        self.assertEqual([x for x, in [(4,), (5,), (6,)]], [4, 5, 6])
        self.assertEqual(list(x for x, in [(7,), (8,), (9,)]), [7, 8, 9])

    def test_with_statement(self):
        class manager(object):
            def __enter__(self):
                return (1, 2)
            def __exit__(self, *args):
                pass

        with manager():
            pass
        with manager() as x:
            pass
        with manager() as (x, y):
            pass
        with manager(), manager():
            pass
        with manager() as x, manager() as y:
            pass
        with manager() as x, manager():
            pass

    def test_if_else_expr(self):
        # Test ifelse expressions in various cases
        def _checkeval(msg, ret):
            "helper to check that evaluation of expressions is done correctly"
            print(msg)
            return ret

        # the next line is not allowed anymore
        #self.assertEqual([ x() for x in lambda: True, lambda: False if x() ], [True])
        self.assertEqual([ x() for x in (lambda: True, lambda: False) if x() ], [True])
        self.assertEqual([ x(False) for x in (lambda x: False if x else True, lambda x: True if x else False) if x(False) ], [True])
        self.assertEqual((5 if 1 else _checkeval("check 1", 0)), 5)
        self.assertEqual((_checkeval("check 2", 0) if 0 else 5), 5)
        self.assertEqual((5 and 6 if 0 else 1), 1)
        self.assertEqual(((5 and 6) if 0 else 1), 1)
        self.assertEqual((5 and (6 if 1 else 1)), 6)
        self.assertEqual((0 or _checkeval("check 3", 2) if 0 else 3), 3)
        self.assertEqual((1 or _checkeval("check 4", 2) if 1 else _checkeval("check 5", 3)), 1)
        self.assertEqual((0 or 5 if 1 else _checkeval("check 6", 3)), 5)
        self.assertEqual((not 5 if 1 else 1), False)
        self.assertEqual((not 5 if 0 else 1), 1)
        self.assertEqual((6 + 1 if 1 else 2), 7)
        self.assertEqual((6 - 1 if 1 else 2), 5)
        self.assertEqual((6 * 2 if 1 else 4), 12)
        self.assertEqual((6 / 2 if 1 else 3), 3)
        self.assertEqual((6 < 4 if 0 else 2), 2)

    def test_paren_evaluation(self):
        self.assertEqual(16 // (4 // 2), 8)
        self.assertEqual((16 // 4) // 2, 2)
        self.assertEqual(16 // 4 // 2, 2)
        self.assertTrue(False is (2 is 3))
        self.assertFalse((False is 2) is 3)
        self.assertFalse(False is 2 is 3)

    def test_matrix_mul(self):
        # This is not intended to be a comprehensive test, rather just to be few
        # samples of the @ operator in test_grammar.py.
        class M:
            def __matmul__(self, o):
                return 4
            def __imatmul__(self, o):
                self.other = o
                return self
        m = M()
        self.assertEqual(m @ m, 4)
        m @= 42
        self.assertEqual(m.other, 42)

    def test_async_await(self):
        async def test():
            def sum():
                pass
            if 1:
                await someobj()

        self.assertEqual(test.__name__, 'test')
        self.assertTrue(bool(test.__code__.co_flags & inspect.CO_COROUTINE))

        def decorator(func):
            setattr(func, '_marked', True)
            return func

        @decorator
        async def test2():
            return 22
        self.assertTrue(test2._marked)
        self.assertEqual(test2.__name__, 'test2')
        self.assertTrue(bool(test2.__code__.co_flags & inspect.CO_COROUTINE))

    def test_async_for(self):
        class Done(Exception): pass

        class AIter:
            def __aiter__(self):
                return self
            async def __anext__(self):
                raise StopAsyncIteration

        async def foo():
            async for i in AIter():
                pass
            async for i, j in AIter():
                pass
            async for i in AIter():
                pass
            else:
                pass
            raise Done

        with self.assertRaises(Done):
            foo().send(None)

    def test_async_with(self):
        class Done(Exception): pass

        class manager:
            async def __aenter__(self):
                return (1, 2)
            async def __aexit__(self, *exc):
                return False

        async def foo():
            async with manager():
                pass
            async with manager() as x:
                pass
            async with manager() as (x, y):
                pass
            async with manager(), manager():
                pass
            async with manager() as x, manager() as y:
                pass
            async with manager() as x, manager():
                pass
            raise Done

        with self.assertRaises(Done):
            foo().send(None)


if __name__ == '__main__':
    unittest.main()
