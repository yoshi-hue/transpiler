from .ast_nodes import *

class SemanticError(Exception):
    pass

class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def define(self, name, kind='variable'):
        self.symbols[name] = kind

    def contains(self, name):
        return name in self.symbols

    def as_dict(self):
        return dict(self.symbols)

class SemanticAnalyzer:
    """Small semantic pass used by the prototype.

    It resolves names and records variables, functions and parameters.
    Full type inference is intentionally outside the current prototype scope.
    """
    def __init__(self):
        self.table = SymbolTable()
        self.errors = []

    def analyze(self, program):
        # Predeclare top-level functions so calls can appear before their definition.
        for stmt in program.statements:
            if isinstance(stmt, FunctionDef):
                self.table.define(stmt.name, 'function')
        for stmt in program.statements:
            self.statement(stmt, self.table)
        if self.errors:
            raise SemanticError('; '.join(self.errors))
        return self.table

    def statement(self, node, table):
        if isinstance(node, Assignment):
            self.expression(node.value, table)
            table.define(node.name, 'variable')
        elif isinstance(node, PrintStatement):
            self.expression(node.expression, table)
        elif isinstance(node, ExpressionStatement):
            self.expression(node.expression, table)
        elif isinstance(node, ReturnStatement):
            if node.expression:
                self.expression(node.expression, table)
        elif isinstance(node, FunctionDef):
            local = SymbolTable()
            local.symbols.update(table.symbols)
            for p in node.params:
                local.define(p, 'parameter')
            for s in node.body:
                self.statement(s, local)
        elif isinstance(node, IfStatement):
            self.expression(node.condition, table)
            for s in node.body:
                self.statement(s, table)
            for cond, body in node.elifs:
                self.expression(cond, table)
                for s in body:
                    self.statement(s, table)
            for s in node.else_body:
                self.statement(s, table)
        elif isinstance(node, WhileStatement):
            self.expression(node.condition, table)
            for s in node.body:
                self.statement(s, table)

    def expression(self, node, table):
        if isinstance(node, Name) and not table.contains(node.value):
            self.errors.append(f"undefined name '{node.value}'")
        elif isinstance(node, Binary):
            self.expression(node.left, table)
            self.expression(node.right, table)
        elif isinstance(node, Unary):
            self.expression(node.operand, table)
        elif isinstance(node, Call):
            self.expression(node.function, table)
            for arg in node.args:
                self.expression(arg, table)
