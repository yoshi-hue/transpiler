RULE_TABLE_VERSION = '1.2'

# Human-editable feature mapping table. In a larger system this can be moved to JSON/YAML.
RULES = [
    {'source': 'assignment', 'target': 'let name = expression;', 'status': 'implemented'},
    {'source': 'print(expression)', 'target': 'console.log(expression);', 'status': 'implemented'},
    {'source': 'True / False', 'target': 'true / false', 'status': 'implemented'},
    {'source': 'and / or / not', 'target': '&& / || / !', 'status': 'implemented'},
    {'source': 'if / elif / else', 'target': 'if / else if / else + braces', 'status': 'implemented'},
    {'source': 'while', 'target': 'while + braces', 'status': 'implemented'},
    {'source': 'def function', 'target': 'function declaration', 'status': 'implemented'},
    {'source': 'return', 'target': 'return', 'status': 'implemented'},
    {'source': 'arithmetic/comparison expressions', 'target': 'JavaScript operators', 'status': 'implemented'},
    {'source': 'unary expressions', 'target': 'JavaScript unary operators', 'status': 'implemented'},
    {'source': 'function calls', 'target': 'JavaScript calls', 'status': 'implemented'},
    {'source': 'expression statements', 'target': 'JavaScript statements', 'status': 'implemented'},
    {'source': 'numeric/string literals', 'target': 'JavaScript literals', 'status': 'implemented'},
    {'source': 'name references', 'target': 'JavaScript identifiers', 'status': 'implemented'},
    {'source': 'comparison expressions', 'target': 'JavaScript comparisons', 'status': 'implemented'},
    {'source': 'block nesting', 'target': 'JavaScript braces and indentation', 'status': 'implemented'},
    {'source': 'function parameters', 'target': 'JavaScript parameter list', 'status': 'implemented'},
]
