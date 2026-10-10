import json
from .ast_nodes import *


class JavaCodeGenerator:
    def __init__(self):
        self.lines = []
        self.indent = 0
        self.rules_used = []

    def emit(self, text=''):
        self.lines.append('    ' * self.indent + text)

    def rule(self, text):
        if text not in self.rules_used:
            self.rules_used.append(text)

    def generate(self, program):
        self.emit('public class Main {')
        self.indent += 1
        for statement in program.statements:
            if isinstance(statement, FunctionDef):
                self.function(statement)
        self.emit('public static void main(String[] args) {')
        self.indent += 1
        for statement in program.statements:
            if not isinstance(statement, FunctionDef):
                self.statement(statement)
        self.indent -= 1
        self.emit('}')
        self.indent -= 1
        self.emit('}')
        return '\n'.join(self.lines)

    def function(self, node):
        self.rule('def -> static Java method')
        params = ', '.join(f'double {param}' for param in node.params)
        self.emit(f'public static double {node.name}({params}) {{')
        self.indent += 1
        for statement in node.body:
            self.statement(statement)
        self.indent -= 1
        self.emit('}')

    def statement(self, node):
        if isinstance(node, Assignment):
            self.rule('assignment -> typed Java local')
            if node.type_name == 'int':
                type_name = 'int'
            elif node.type_name == 'float':
                type_name = 'float'
            else:
                type_name = 'var'
            value = self.expr(node.value)
            if node.type_name == 'float' and isinstance(node.value, Number) and isinstance(node.value.value, float):
                value += 'f'
            self.emit(f'{type_name} {node.name} = {value};')
        elif isinstance(node, PrintStatement):
            self.rule('print -> System.out.println')
            values = [self.expr(expression) for expression in node.expressions]
            if len(values) == 1:
                output = values[0]
            else:
                output = ' + " " + '.join(f'String.valueOf({value})' for value in values)
            self.emit(f'System.out.println({output});')
        elif isinstance(node, ExpressionStatement):
            self.emit(f'{self.expr(node.expression)};')
        elif isinstance(node, ReturnStatement):
            self.rule('return -> return')
            self.emit('return;' if node.expression is None else f'return {self.expr(node.expression)};')
        elif isinstance(node, IfStatement):
            self.rule('if/elif/else -> Java braces')
            self.emit(f'if ({self.expr(node.condition)}) {{')
            self.indent += 1
            for statement in node.body:
                self.statement(statement)
            self.indent -= 1
            for condition, body in node.elifs:
                self.emit(f'}} else if ({self.expr(condition)}) {{')
                self.indent += 1
                for statement in body:
                    self.statement(statement)
                self.indent -= 1
            if node.else_body:
                self.emit('} else {')
                self.indent += 1
                for statement in node.else_body:
                    self.statement(statement)
                self.indent -= 1
            self.emit('}')
        elif isinstance(node, WhileStatement):
            self.rule('while -> Java while')
            self.emit(f'while ({self.expr(node.condition)}) {{')
            self.indent += 1
            for statement in node.body:
                self.statement(statement)
            self.indent -= 1
            self.emit('}')
        elif isinstance(node, SwitchStatement):
            self.rule('switch/case/default -> Java switch')
            self.emit(f'switch ({self.expr(node.expression)}) {{')
            self.indent += 1
            for case in node.cases:
                self.emit(f'case {self.expr(case.value)}:')
                self.indent += 1
                for statement in case.body:
                    self.statement(statement)
                self.emit('break;')
                self.indent -= 1
            if node.default_body:
                self.emit('default:')
                self.indent += 1
                for statement in node.default_body:
                    self.statement(statement)
                self.indent -= 1
            self.indent -= 1
            self.emit('}')
        else:
            raise ValueError(f'No Java rule for {type(node).__name__}')

    def expr(self, node):
        if isinstance(node, Number):
            return str(node.value)
        if isinstance(node, String):
            return json.dumps(node.value)
        if isinstance(node, Boolean):
            self.rule('True/False -> true/false')
            return 'true' if node.value else 'false'
        if isinstance(node, Name):
            return node.value
        if isinstance(node, Unary):
            if node.op == 'not':
                self.rule('not -> !')
                return f'(!{self.expr(node.operand)})'
            return f'(-{self.expr(node.operand)})'
        if isinstance(node, Binary):
            operator = {'and': '&&', 'or': '||'}.get(node.op, node.op)
            if node.op in ('and', 'or'):
                self.rule(f'{node.op} -> {operator}')
            return f'({self.expr(node.left)} {operator} {self.expr(node.right)})'
        if isinstance(node, Call):
            return f'{self.expr(node.function)}({", ".join(self.expr(arg) for arg in node.args)})'
        raise ValueError(f'No Java expression rule for {type(node).__name__}')
