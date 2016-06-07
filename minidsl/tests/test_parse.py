# -*- coding:utf-8 -*-
import unittest
from minidsl.parse import Op, Ref, Assign, Call, Return, If, For, While, Reserved


class ParseTests(unittest.TestCase):
    def _callFUT(self, code):
        from minidsl.parse import parse
        return parse(code)

    def test_it(self):
        candidates = [
            ("2 * (1 + 2)", [Op(name="Mult", args=[2, Op(name="Add", args=[1, 2])])]),
            ("~1", [Op(name="Invert", args=[1])]),
            ("~a", [Op(name="Invert", args=[Ref(name="a")])]),
            ("x = 10", [Assign(name="x", value=10)]),
            ("f(10, x, y=2)", [Call(ref=Ref(name="f"), args=[10, Ref(name="x")], kwargs=[2])]),
            ("10 < x and x < 20 and y == 100 or 10", [Op(name='Or', args=[Op(name='And', args=[Op(name='Lt', args=[10, Ref(name='x')]), Op(name='Lt', args=[Ref(name='x'), 20]), Op(name='Eq', args=[Ref(name='y'), 100])]), 10])]),
            ("d = {'10': 20, 'x': y}", [Assign(name='d', value={Ref(name='y'): 20, 'x': '10'})]),
            ("i += 1", [Assign(name='i', value=Op(name='Add', args=[Ref(name='i'), 1]))]),
            ("i -= 1", [Assign(name='i', value=Op(name='Sub', args=[Ref(name='i'), 1]))]),
        ]
        for code, expected in candidates:
            with self.subTest(code=code, expected=expected):
                actual = self._callFUT(code)
                self.assertEqual(str(actual), str(expected))

    def test_if__simple(self):
        code = """
if x == 10:
    return 10
"""
        actual = self._callFUT(code)
        expected = [
            If(test=Op(name='Eq', args=[Ref(name='x'), 10]),
               body=[Return(value=10)],
               orelse=[])
        ]
        self.assertEqual(str(actual), str(expected))

    def test_if__complex(self):
        code = """
if x == 10:
    print("oo")
    print("o")
elif x == 20:
    print("hmm")
else:
    print("oyoyo")
"""
        actual = self._callFUT(code)
        expected = [
            If(test=Op(name='Eq', args=[Ref(name='x'), 10]),
               body=[Call(ref=Ref(name='print'), args=['oo'], kwargs=[]),
                     Call(ref=Ref(name='print'), args=['o'], kwargs=[])],
               orelse=[If(test=Op(name='Eq', args=[Ref(name='x'), 20]),
                          body=[Call(ref=Ref(name='print'), args=['hmm'], kwargs=[])],
                          orelse=[Call(ref=Ref(name='print'), args=['oyoyo'], kwargs=[])])])
        ]
        self.assertEqual(str(actual), str(expected))

    def test_for__simple(self):
        code = """
for i in L:
    print(i)
"""
        actual = self._callFUT(code)
        expected = [
            For(target=Ref(name='i'),
                iter=Ref(name='L'),
                body=[Call(ref=Ref(name='print'), args=[Ref(name='i')], kwargs=[])])
        ]
        self.assertEqual(str(actual), str(expected))

    def test_for__complex(self):
        code = """
for i in [1, 2, 3]:
    for j in [1, 2, 3]:
        if j == 2:
            continue
        print(i, j)
"""
        actual = self._callFUT(code)
        expected = [
            For(target=Ref(name='i'),
                iter=[1, 2, 3],
                body=[
                    For(target=Ref(name='j'),
                        iter=[1, 2, 3],
                        body=[
                            If(test=Op(name='Eq', args=[Ref(name='j'), 2]), body=[Reserved(name='Continue')], orelse=[]),
                            Call(ref=Ref(name='print'), args=[Ref(name='i'), Ref(name='j')], kwargs=[])])])]
        self.assertEqual(str(actual), str(expected))

    def test_while__simple(self):
        code = """
while True:
    i += 1
    print(i)
    if i == 10:
        break
"""
        actual = self._callFUT(code)
        expected = [
            While(test=Reserved(name='True'),
                  body=[
                      Assign(name='i', value=Op(name='Add', args=[Ref(name='i'), 1])),
                      Call(ref=Ref(name='print'), args=[Ref(name='i')], kwargs=[]),
                      If(test=Op(name='Eq', args=[Ref(name='i'), 10]),
                         body=[Reserved(name='Break')], orelse=[])])
        ]
        self.assertEqual(str(actual), str(expected))
