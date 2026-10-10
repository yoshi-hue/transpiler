from .lexer import Lexer, Token
from .ast_nodes import *


class ParserError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    @property
    def current(self):
        return self.tokens[self.i]

    def peek(self, typ=None):
        t = self.current
        return t.type == typ if typ else t

    def advance(self):
        t = self.current
        self.i += 1
        return t

    def expect(self, typ):
        if not self.peek(typ):
            t = self.current
            raise ParserError(
                f"Line {t.line}, column {t.column}: expected {typ}, got {t.type} ({t.value!r})."
            )
        return self.advance()

    def skip_newlines(self):
        while self.peek("NEWLINE"):
            self.advance()

    def parse(self):
        statements = []
        self.skip_newlines()
        while not self.peek("EOF"):
            statements.append(self.statement())
            self.skip_newlines()
        return Program(statements)

    def statement(self):
        if self.peek("IF"):
            return self.parse_if()
        if self.peek("WHILE"):
            return self.parse_while()
        if self.peek("DEF"):
            return self.parse_function()
        if self.peek("RETURN"):
            self.advance()
            if self.peek("NEWLINE"):
                self.advance()
                return ReturnStatement(None)
            expr = self.expression()
            self.expect("NEWLINE")
            return ReturnStatement(expr)
        if self.peek("PRINT"):
            self.advance()
            self.expect("LPAREN")
            expr = self.expression()
            self.expect("RPAREN")
            self.expect("NEWLINE")
            return PrintStatement(expr)

        expr = self.expression()
        if isinstance(expr, Name) and self.peek("ASSIGN"):
            self.advance()
            value = self.expression()
            self.expect("NEWLINE")
            return Assignment(expr.value, value)

        self.expect("NEWLINE")
        return ExpressionStatement(expr)

    def parse_if(self):
        self.expect("IF")
        condition = self.expression()
        self.expect("COLON")
        body = self.parse_block()

        elifs = []
        while self.peek("ELIF"):
            self.advance()
            cond = self.expression()
            self.expect("COLON")
            elifs.append((cond, self.parse_block()))

        else_body = []
        if self.peek("ELSE"):
            self.advance()
            self.expect("COLON")
            else_body = self.parse_block()

        return IfStatement(condition, body, elifs, else_body)

    def parse_while(self):
        self.expect("WHILE")
        condition = self.expression()
        self.expect("COLON")
        return WhileStatement(condition, self.parse_block())

    def parse_function(self):
        self.expect("DEF")
        name = self.expect("NAME").value
        self.expect("LPAREN")
        params = []
        if not self.peek("RPAREN"):
            params.append(self.expect("NAME").value)
            while self.peek("COMMA"):
                self.advance()
                params.append(self.expect("NAME").value)
        self.expect("RPAREN")
        self.expect("COLON")
        return FunctionDef(name, params, self.parse_block())

    def parse_block(self):
        self.expect("NEWLINE")
        self.expect("INDENT")
        self.skip_newlines()
        body = []
        while not self.peek("DEDENT") and not self.peek("EOF"):
            body.append(self.statement())
            self.skip_newlines()
        self.expect("DEDENT")
        return body

    def expression(self):
        return self.parse_or()

    def parse_or(self):
        node = self.parse_and()
        while self.peek("OR"):
            self.advance()
            node = Binary(node, "or", self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_comparison()
        while self.peek("AND"):
            self.advance()
            node = Binary(node, "and", self.parse_comparison())
        return node

    def parse_comparison(self):
        node = self.parse_term()
        while self.peek("OP") and self.current.value in ("==", "!=", "<", "<=", ">", ">="):
            op = self.advance().value
            node = Binary(node, op, self.parse_term())
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek("OP") and self.current.value in ("+", "-"):
            op = self.advance().value
            node = Binary(node, op, self.parse_factor())
        return node

    def parse_factor(self):
        node = self.parse_unary()
        while self.peek("OP") and self.current.value in ("*", "/", "%"):
            op = self.advance().value
            node = Binary(node, op, self.parse_unary())
        return node

    def parse_unary(self):
        if self.peek("NOT"):
            self.advance()
            return Unary("not", self.parse_unary())
        if self.peek("OP") and self.current.value == "-":
            self.advance()
            return Unary("-", self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        if self.peek("NUMBER"):
            raw = self.advance().value
            return Number(float(raw) if "." in raw else int(raw))
        if self.peek("STRING"):
            return String(self.advance().value)
        if self.peek("TRUE"):
            self.advance()
            return Boolean(True)
        if self.peek("FALSE"):
            self.advance()
            return Boolean(False)

        if self.peek("NAME"):
            node = Name(self.advance().value)
            while self.peek("LPAREN"):
                self.advance()
                args = []
                if not self.peek("RPAREN"):
                    args.append(self.expression())
                    while self.peek("COMMA"):
                        self.advance()
                        args.append(self.expression())
                self.expect("RPAREN")
                node = Call(node, args)
            return node

        if self.peek("LPAREN"):
            self.advance()
            node = self.expression()
            self.expect("RPAREN")
            return node

        t = self.current
        raise ParserError(f"Line {t.line}, column {t.column}: unexpected token {t.type} ({t.value!r}).")
