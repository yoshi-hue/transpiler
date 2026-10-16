import json
from .ast_nodes import *

class CodeGenerator:
    def __init__(self):
        self.lines = []
        self.indent = 0
        self.rules_used = []
        self.declared_names = [set()]
        self.declaration_depth = [0]

    def emit(self, text=''):
        self.lines.append('    ' * self.indent + text)

    def rule(self, text):
        if text not in self.rules_used:
            self.rules_used.append(text)

    def generate(self, program):
        for stmt in program.statements:
            self.statement(stmt)
        return '\n'.join(self.lines)

    def statement(self, n):
        if isinstance(n, Assignment):
            self.rule('assignment -> let')
            declared = self.declared_names[-1]
            prefix = '' if n.name in declared else ('var ' if self.declaration_depth[-1] else 'let ')
            declared.add(n.name)
            self.emit(f'{prefix}{n.name} = {self.expr(n.value)};')
        elif isinstance(n, PrintStatement):
            self.rule('print -> console.log')
            self.emit(f'console.log({self.expr(n.expression)});')
        elif isinstance(n, ExpressionStatement):
            self.rule('expression statement -> JavaScript statement')
            self.emit(f'{self.expr(n.expression)};')
        elif isinstance(n, ReturnStatement):
            self.rule('return -> return')
            self.emit('return;' if n.expression is None else f'return {self.expr(n.expression)};')
        elif isinstance(n, FunctionDef):
            self.rule('def -> function')
            self.rule('function parameters -> JavaScript parameter list')
            self.rule('block nesting -> JavaScript braces and indentation')
            self.emit(f'function {n.name}({", ".join(n.params)}) {{')
            self.indent += 1
            self.declared_names.append(set(n.params))
            self.declaration_depth.append(0)
            for s in n.body:
                self.statement(s)
            self.declaration_depth.pop()
            self.declared_names.pop()
            self.indent -= 1
            self.emit('}')
        elif isinstance(n, IfStatement):
            self.rule('if/elif/else -> JavaScript braces')
            self.rule('block nesting -> JavaScript braces and indentation')
            self.emit(f'if ({self.expr(n.condition)}) {{')
            self.indent += 1
            self.declaration_depth[-1] += 1
            for s in n.body:
                self.statement(s)
            self.declaration_depth[-1] -= 1
            self.indent -= 1
            for cond, body in n.elifs:
                self.emit(f'}} else if ({self.expr(cond)}) {{')
                self.indent += 1
                self.declaration_depth[-1] += 1
                for s in body:
                    self.statement(s)
                self.declaration_depth[-1] -= 1
                self.indent -= 1
            if n.else_body:
                self.emit('} else {')
                self.indent += 1
                self.declaration_depth[-1] += 1
                for s in n.else_body:
                    self.statement(s)
                self.declaration_depth[-1] -= 1
                self.indent -= 1
            self.emit('}')
        elif isinstance(n, WhileStatement):
            self.rule('while -> JavaScript while')
            self.rule('block nesting -> JavaScript braces and indentation')
            self.emit(f'while ({self.expr(n.condition)}) {{')
            self.indent += 1
            self.declaration_depth[-1] += 1
            for s in n.body:
                self.statement(s)
            self.declaration_depth[-1] -= 1
            self.indent -= 1
            self.emit('}')
        else:
            raise ValueError(f'No deterministic rule for {type(n).__name__}')

    def expr(self, n):
        if isinstance(n, Number):
            self.rule('numeric/string literal -> JavaScript literal')
            return str(n.value)
        if isinstance(n, String):
            self.rule('numeric/string literal -> JavaScript literal')
            return json.dumps(n.value)
        if isinstance(n, Boolean):
            self.rule('True/False -> true/false')
            return 'true' if n.value else 'false'
        if isinstance(n, Name):
            self.rule('name reference -> JavaScript identifier')
            return n.value
        if isinstance(n, Unary):
            self.rule('unary expression -> JavaScript unary operator')
            if n.op == 'not':
                self.rule('not -> !')
                return f'(!{self.expr(n.operand)})'
            return f'(-{self.expr(n.operand)})'
        if isinstance(n, Binary):
            self.rule('arithmetic/comparison expression -> JavaScript operator')
            if n.op in ('==', '!=', '<', '<=', '>', '>='):
                self.rule('comparison expression -> JavaScript comparison')
            op = {'and': '&&', 'or': '||'}.get(n.op, n.op)
            if n.op in ('and', 'or'):
                self.rule(f'{n.op} -> {op}')
            return f'({self.expr(n.left)} {op} {self.expr(n.right)})'
        if isinstance(n, Call):
            self.rule('function call -> JavaScript call')
            return f'{self.expr(n.function)}({", ".join(self.expr(a) for a in n.args)})'
        raise ValueError(f'No expression rule for {type(n).__name__}')
