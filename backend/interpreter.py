import io
from contextlib import redirect_stdout
from .ast_nodes import *

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class UserFunction:
    def __init__(self, params, body, closure):
        self.params, self.body, self.closure = params, body, closure

    def __call__(self, args):
        if len(args) != len(self.params):
            raise RuntimeError(f'expected {len(self.params)} arguments, got {len(args)}')
        env = dict(self.closure)
        env.update(zip(self.params, args))
        try:
            execute_statements(self.body, env)
        except ReturnSignal as r:
            return r.value
        return None

def evaluate(node, env):
    if isinstance(node, Number): return node.value
    if isinstance(node, String): return node.value
    if isinstance(node, Boolean): return node.value
    if isinstance(node, Name): return env[node.value]
    if isinstance(node, Unary):
        x = evaluate(node.operand, env)
        return (not x) if node.op == 'not' else -x
    if isinstance(node, Binary):
        a = evaluate(node.left, env)
        b = evaluate(node.right, env)
        return {
            '+': lambda: a+b, '-': lambda: a-b, '*': lambda: a*b,
            '/': lambda: a/b, '%': lambda: a%b, '==': lambda: a==b,
            '!=': lambda: a!=b, '<': lambda: a<b, '<=': lambda: a<=b,
            '>': lambda: a>b, '>=': lambda: a>=b,
            'and': lambda: a and b, 'or': lambda: a or b,
        }[node.op]()
    if isinstance(node, Call):
        fn = evaluate(node.function, env)
        return fn([evaluate(a, env) for a in node.args])
    raise RuntimeError(f'Unsupported expression: {type(node).__name__}')

def execute_statement(node, env):
    if isinstance(node, Assignment):
        env[node.name] = evaluate(node.value, env)
    elif isinstance(node, PrintStatement):
        print(evaluate(node.expression, env))
    elif isinstance(node, ExpressionStatement):
        evaluate(node.expression, env)
    elif isinstance(node, ReturnStatement):
        raise ReturnSignal(None if node.expression is None else evaluate(node.expression, env))
    elif isinstance(node, FunctionDef):
        env[node.name] = UserFunction(node.params, node.body, env.copy())
    elif isinstance(node, IfStatement):
        if evaluate(node.condition, env):
            execute_statements(node.body, env)
            return
        for cond, body in node.elifs:
            if evaluate(cond, env):
                execute_statements(body, env)
                return
        execute_statements(node.else_body, env)
    elif isinstance(node, WhileStatement):
        guard = 0
        while evaluate(node.condition, env):
            execute_statements(node.body, env)
            guard += 1
            if guard > 10000:
                raise RuntimeError('Loop exceeded 10000 iterations.')

def execute_statements(statements, env):
    for stmt in statements:
        execute_statement(stmt, env)

def run_source(program):
    buf = io.StringIO()
    with redirect_stdout(buf):
        execute_statements(program.statements, {})
    return buf.getvalue().strip()
