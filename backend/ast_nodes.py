from dataclasses import dataclass, field
from typing import Any


@dataclass
class Program:
    statements: list


@dataclass
class Number:
    value: float | int


@dataclass
class String:
    value: str


@dataclass
class Boolean:
    value: bool


@dataclass
class Name:
    value: str


@dataclass
class Unary:
    op: str
    operand: Any


@dataclass
class Binary:
    left: Any
    op: str
    right: Any


@dataclass
class Call:
    function: Any
    args: list


@dataclass
class Assignment:
    name: str
    value: Any


@dataclass
class ExpressionStatement:
    expression: Any


@dataclass
class PrintStatement:
    expression: Any


@dataclass
class ReturnStatement:
    expression: Any | None


@dataclass
class IfStatement:
    condition: Any
    body: list
    elifs: list = field(default_factory=list)
    else_body: list = field(default_factory=list)


@dataclass
class WhileStatement:
    condition: Any
    body: list


@dataclass
class FunctionDef:
    name: str
    params: list[str]
    body: list


def ast_to_dict(node):
    if isinstance(node, list):
        return [ast_to_dict(x) for x in node]
    if hasattr(node, "__dataclass_fields__"):
        result = {"type": node.__class__.__name__}
        for name in node.__dataclass_fields__:
            result[name] = ast_to_dict(getattr(node, name))
        return result
    return node
