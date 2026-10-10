from dataclasses import dataclass


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int


KEYWORDS = {
    "if": "IF",
    "elif": "ELIF",
    "else": "ELSE",
    "while": "WHILE",
    "def": "DEF",
    "return": "RETURN",
    "print": "PRINT",
    "and": "AND",
    "or": "OR",
    "not": "NOT",
    "True": "TRUE",
    "False": "FALSE",
}


class LexerError(Exception):
    pass


class Lexer:
    def __init__(self, source: str):
        self.source = source.replace("\r\n", "\n").replace("\r", "\n")
        self.tokens = []
        self.indent_stack = [0]

    def emit(self, typ, value, line, col):
        self.tokens.append(Token(typ, value, line, col))

    def tokenize(self):
        lines = self.source.split("\n")

        for line_no, raw in enumerate(lines, 1):
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue

            spaces = len(raw) - len(raw.lstrip(" "))
            if "\t" in raw[:spaces]:
                raise LexerError(f"Line {line_no}: tabs are not supported; use spaces.")

            if spaces > self.indent_stack[-1]:
                self.indent_stack.append(spaces)
                self.emit("INDENT", "", line_no, 1)
            elif spaces < self.indent_stack[-1]:
                while spaces < self.indent_stack[-1]:
                    self.indent_stack.pop()
                    self.emit("DEDENT", "", line_no, 1)
                if spaces != self.indent_stack[-1]:
                    raise LexerError(f"Line {line_no}: inconsistent indentation.")

            i = spaces
            col = spaces + 1
            while i < len(raw):
                ch = raw[i]

                if ch in " \t":
                    i += 1
                    col += 1
                    continue

                if ch == "#":
                    break

                if ch == '"' or ch == "'":
                    quote = ch
                    start_col = col
                    i += 1
                    col += 1
                    value = ""
                    while i < len(raw) and raw[i] != quote:
                        if raw[i] == "\\" and i + 1 < len(raw):
                            escapes = {"n": "\n", "t": "\t", "\\": "\\", '"': '"', "'": "'"}
                            i += 1
                            col += 1
                            value += escapes.get(raw[i], raw[i])
                        else:
                            value += raw[i]
                        i += 1
                        col += 1
                    if i >= len(raw):
                        raise LexerError(f"Line {line_no}, column {start_col}: unterminated string.")
                    i += 1
                    col += 1
                    self.emit("STRING", value, line_no, start_col)
                    continue

                if ch.isdigit():
                    start = i
                    start_col = col
                    while i < len(raw) and (raw[i].isdigit() or raw[i] == "."):
                        i += 1
                        col += 1
                    self.emit("NUMBER", raw[start:i], line_no, start_col)
                    continue

                if ch.isalpha() or ch == "_":
                    start = i
                    start_col = col
                    while i < len(raw) and (raw[i].isalnum() or raw[i] == "_"):
                        i += 1
                        col += 1
                    word = raw[start:i]
                    self.emit(KEYWORDS.get(word, "NAME"), word, line_no, start_col)
                    continue

                two = raw[i:i+2]
                if two in ("==", "!=", "<=", ">="):
                    self.emit("OP", two, line_no, col)
                    i += 2
                    col += 2
                    continue

                single = {
                    "=": "ASSIGN", "+": "OP", "-": "OP", "*": "OP",
                    "/": "OP", "%": "OP", "<": "OP", ">": "OP",
                    "(": "LPAREN", ")": "RPAREN", ",": "COMMA",
                    ":": "COLON",
                }
                if ch in single:
                    self.emit(single[ch], ch, line_no, col)
                    i += 1
                    col += 1
                    continue

                raise LexerError(f"Line {line_no}, column {col}: unexpected character {ch!r}.")

            self.emit("NEWLINE", "", line_no, len(raw) + 1)

        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.emit("DEDENT", "", len(lines), 1)

        self.emit("EOF", "", len(lines), 1)
        return self.tokens
