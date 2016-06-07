# -*- coding:utf-8 -*-
import ast
from collections import namedtuple
# https://greentreesnakes.readthedocs.io/
# . access
# loop
# syntax error
# function definition
# list/set/dict comprehension

Expr = namedtuple("Expr", "value")
Op = namedtuple("Op", "name args")
Ref = namedtuple("Ref", "name")
Reserved = namedtuple("Reserved", "name")  # True, False, break, continue, pass
Return = namedtuple("Return", "value")
Assign = namedtuple("Assign", "name value")
Call = namedtuple("Call", "ref, args, kwargs")
If = namedtuple("If", "test, body, orelse")
For = namedtuple("For", "target, iter, body")
While = namedtuple("While", "test, body")


class ParseError(Exception):
    def __init__(self, node, lineno, msg):
        self.node = node
        self.lineno = lineno
        msg = "(node: {}, lineno: {}) {}".format(node.__class__.__name__, lineno, msg)
        super().__init__(msg)


def parse_error(node, msg):
    raise ParseError(node, node.lineno, msg)


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
        elif isinstance(node, (ast.Break, ast.Continue, ast.Pass)):
            self.s.append(Reserved(name=node.__class__.__name__))
        elif isinstance(node, ast.NameConstant):
            self.s.append(Reserved(name=repr(node.value)))  # xxx:
        elif isinstance(node, ast.Tuple):
            for v in node.elts:
                self.visit(v)
            self.s.append(tuple(reversed([self.s.pop() for _ in node.elts])))
        elif isinstance(node, ast.List):
            for v in node.elts:
                self.visit(v)
            self.s.append(list(reversed([self.s.pop() for _ in node.elts])))
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
        self.s.append(Op(name=name, args=list(reversed([self.s.pop() for _ in node.values]))))

    def visit_Compare(self, node):
        # left, ops, comparators
        if len(node.ops) > 1:
            parse_error(node, "x < y < z is not supported")
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
                parse_error(node, "destructuring is not supported")
            self.s.append(Assign(name=name.id, value=self.s.pop()))

    def visit_AugAssign(self, node):
        # target, op, value
        # x += 1 => x = x + 1
        self.visit(node.value)
        op_name = node.op.__class__.__name__
        value = Op(name=op_name, args=[Ref(name=node.target.id), self.s.pop()])
        self.s.append(Assign(name=node.target.id, value=value))

    def visit_Call(self, node):
        # func, args, keywords, starargs, kwargs
        self.generic_visit(node)
        kwargs = list(reversed([self.s.pop() for _ in node.keywords]))
        args = list(reversed([self.s.pop() for _ in node.args]))
        ref = self.s.pop()
        self.s.append(Call(kwargs=kwargs, args=args, ref=ref))

    def visit_Return(self, node):
        # value
        self.generic_visit(node)
        self.s.append(Return(value=self.s.pop()))

    def visit_If(self, node):
        # test, body, orelse
        self.generic_visit(node)
        orelse = list(reversed([self.s.pop() for _ in node.orelse]))
        body = list(reversed([self.s.pop() for _ in node.body]))
        self.s.append(If(orelse=orelse, body=body, test=self.s.pop()))

    def visit_For(self, node):
        # target, iter, body
        if node.orelse:
            parse_error(node, "for-else is not supprted")
        self.visit(node.target)
        body = list(reversed([self.s.pop() for _ in node.body]))
        self.s.append(For(body=body, iter=self.s.pop(), target=self.s.pop()))

    def visit_While(self, node):
        # test, body
        if node.orelse:
            parse_error(node, "while-else is not supprted")
        self.generic_visit(node)
        body = list(reversed([self.s.pop() for _ in node.body]))
        self.s.append(While(body=body, test=self.s.pop()))


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
    pass
