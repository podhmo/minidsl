# -*- coding:utf-8 -*-
import ast
from collections import namedtuple
# https://greentreesnakes.readthedocs.io/


Expr = namedtuple("Expr", "value")
Op = namedtuple("Op", "name args")
Ref = namedtuple("Ref", "name")
Assign = namedtuple("Assign", "name value")
Call = namedtuple("Call", "ref, args, kwargs")


class V(ast.NodeVisitor):
    def __init__(self):
        self.s = []

    def parse(self, node):
        self.s = []
        self.visit(node)
        return self.s

    def visit(self, node):
        if isinstance(node, (ast.Str, ast.Bytes)):
            self.s.append(node.s)
        elif isinstance(node, ast.Num):
            self.s.append(node.n)
        elif isinstance(node, ast.Name):
            self.s.append(Ref(name=node.id))
        elif isinstance(node, ast.Tuple):
            for v in node.elts:
                self.visit(v)
            self.s.append(tuple(self.s.pop() for _ in node.elts))
        elif isinstance(node, ast.List):
            for v in node.elts:
                self.visit(v)
            self.s.append(list(self.s.pop() for _ in node.elts))
        elif isinstance(node, ast.Set):
            for v in node.elts:
                self.visit(v)
            self.s.append(set(self.s.pop() for _ in node.elts))
        elif isinstance(node, ast.Dict):
            for v in node.keys:
                self.visit(v)
            keys = (self.s.pop() for k in node.keys)
            for v in node.values:
                self.visit(v)
            values = (self.s.pop() for k in node.values)
            self.s.append(dict(zip(keys, values)))
        else:
            super().visit(node)

    def visit_BinOp(self, node):
        # left, op, right
        self.visit(node.left)
        self.visit(node.right)
        name = node.op.__class__.__name__
        right = self.s.pop()
        left = self.s.pop()
        self.s.append(Op(name=name, args=[left, right]))

    def visit_UnaryOp(self, node):
        # op, operand
        self.visit(node.operand)
        name = node.op.__class__.__name__
        self.s.append(Op(args=[self.s.pop()], name=name))

    def visit_BoolOp(self, node):
        # op, values
        for v in node.values:
            self.visit(v)
        name = node.op.__class__.__name__
        self.s.append(Op(name=name, args=[self.s.pop() for _ in node.values]))

    def visit_Compare(self, node):
        # left, ops, comparators
        if len(node.ops) > 1:
            raise NotImplementedError("x < y < z is not supported")
        self.visit(node.left)
        self.visit(node.comparators[0])
        name = node.ops[0].__class__.__name__
        right = self.s.pop()
        left = self.s.pop()
        self.s.append(Op(name=name, args=[left, right]))

    def visit_Assign(self, node):
        # targets, value
        self.visit(node.value)
        for name in reversed(node.targets):
            if isinstance(name, ast.Tuple):
                raise NotImplementedError("destructuring is not supported")
            self.s.append(Assign(name=name.id, value=self.s.pop()))

    def visit_Call(self, node):
        # func, args, keywords, starargs, kwargs
        self.generic_visit(node)
        kwargs = [self.s.pop() for _ in node.keywords]
        args = [self.s.pop() for _ in node.args]
        ref = self.s.pop()
        self.s.append(Call(kwargs=kwargs, args=args, ref=ref))


def parse(code):
    if isinstance(code, (str, bytes)):
        code = ast.parse(code)
    return V().parse(code)


def run(code):
    print("----------------------------------------")
    t = ast.parse(code)
    print(ast.dump(t))
    print(V().parse(t))

if __name__ == "__main__":
    """Module(body=[Expr(value=BinOp(left=Num(n=2), op=Mult(), right=BinOp(left=Num(n=1), op=Add(), right=Num(n=2))))])"""
    run("2 * (1 + 2)")
    run("~1")
    run("~a")
    run("x = 10")
    run("f(10, x, y=2)")
    run("10 < x and x < 20 and y == 100 or 10")
    run("d = {'10': 20, 'x': y}")
