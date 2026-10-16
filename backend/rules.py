RULE_TABLE_VERSION = '1.3'

# Human-editable feature mapping table. In a larger system this can be moved to JSON/YAML.
# The dataset intentionally covers common legacy-language constructs so the rule-first
# layer has broad coverage while still delegating rare or unsupported patterns to the LLM.
RULES = [
    {'source': 'assignment', 'target': 'let name = expression; / name = expression', 'status': 'implemented'},
    {'source': 'print(expression)', 'target': 'console.log(expression); / print(expression)', 'status': 'implemented'},
    {'source': 'DISPLAY / PRINT output', 'target': 'console.log / print', 'status': 'implemented'},
    {'source': 'True / False', 'target': 'true / false', 'status': 'implemented'},
    {'source': 'and / or / not', 'target': '&& / || / !', 'status': 'implemented'},
    {'source': 'if / elif / else', 'target': 'if / else if / else + braces', 'status': 'implemented'},
    {'source': 'while', 'target': 'while + braces', 'status': 'implemented'},
    {'source': 'def function', 'target': 'function declaration / Python def', 'status': 'implemented'},
    {'source': 'return', 'target': 'return', 'status': 'implemented'},
    {'source': 'arithmetic/comparison expressions', 'target': 'JavaScript/Python operators', 'status': 'implemented'},
    {'source': 'unary expressions', 'target': 'JavaScript/Python unary operators', 'status': 'implemented'},
    {'source': 'function calls', 'target': 'JavaScript/Python calls', 'status': 'implemented'},
    {'source': 'expression statements', 'target': 'JavaScript/Python statements', 'status': 'implemented'},
    {'source': 'numeric/string literals', 'target': 'JavaScript/Python literals', 'status': 'implemented'},
    {'source': 'name references', 'target': 'JavaScript/Python identifiers', 'status': 'implemented'},
    {'source': 'comparison expressions', 'target': 'JavaScript/Python comparisons', 'status': 'implemented'},
    {'source': 'block nesting', 'target': 'JavaScript/Python braces / indentation', 'status': 'implemented'},
    {'source': 'function parameters', 'target': 'JavaScript parameter list / Python args', 'status': 'implemented'},
    {'source': 'COBOL COMPUTE A = B + C', 'target': 'let a = b + c; / a = b + c', 'status': 'implemented'},
    {'source': 'COBOL IF A > B THEN ... END-IF', 'target': 'if ((a > b)) { ... }', 'status': 'implemented'},
    {'source': 'COBOL ELSE / END-IF', 'target': 'else { ... }', 'status': 'implemented'},
    {'source': 'COBOL PIC numeric declarations', 'target': 'number variables with initialized values', 'status': 'implemented'},
    {'source': 'COBOL DISPLAY literal', 'target': 'console.log("literal"); / print("literal")', 'status': 'implemented'},
    {'source': 'COBOL MOVE A TO B', 'target': 'b = a;', 'status': 'implemented'},
    {'source': 'FORTRAN INTEGER declaration', 'target': 'let / int / variable assignment', 'status': 'implemented'},
    {'source': 'FORTRAN DO I = start, stop', 'target': 'for (let i = start; i <= stop; i++)', 'status': 'implemented'},
    {'source': 'FORTRAN IF (cond) THEN', 'target': 'if (cond) { ... }', 'status': 'implemented'},
    {'source': 'FORTRAN PRINT *, expr', 'target': 'console.log(expr); / print(expr)', 'status': 'implemented'},
    {'source': 'Pascal var declarations', 'target': 'variable declarations in target language', 'status': 'implemented'},
    {'source': 'Pascal assignment :=', 'target': 'assignment operator =', 'status': 'implemented'},
    {'source': 'Pascal if a = 0 then ... else ...', 'target': 'if (a === 0) { ... } else { ... }', 'status': 'implemented'},
    {'source': 'Pascal for i := 1 to 3 do', 'target': 'for (let i = 1; i <= 3; i++)', 'status': 'implemented'},
    {'source': 'Pascal writeln(expr)', 'target': 'console.log(expr); / print(expr)', 'status': 'implemented'},
    {'source': 'BASIC LET A = expr', 'target': 'let a = expr; / a = expr', 'status': 'implemented'},
    {'source': 'BASIC PRINT expr', 'target': 'console.log(expr); / print(expr)', 'status': 'implemented'},
    {'source': 'BASIC FOR I = 1 TO N', 'target': 'for (let i = 1; i <= n; i++)', 'status': 'implemented'},
    {'source': 'BASIC IF A = 0 THEN', 'target': 'if ((a === 0)) { ... }', 'status': 'implemented'},
    {'source': 'BASIC IF A <> B THEN', 'target': 'if ((a !== b)) { ... }', 'status': 'implemented'},
    {'source': 'BASIC IF A <= B THEN', 'target': 'if ((a <= b)) { ... }', 'status': 'implemented'},
    {'source': 'BASIC IF A >= B THEN', 'target': 'if ((a >= b)) { ... }', 'status': 'implemented'},
    {'source': 'Python-like re-assignment in scope', 'target': 'var/let resolution across nested scope', 'status': 'implemented'},
    {'source': 'Python-like function parameter updates', 'target': 'parameters remain immutable in target output unless reassigned locally', 'status': 'implemented'},
    {'source': 'legacy string literals', 'target': 'escaped JavaScript/Python strings', 'status': 'implemented'},
    {'source': 'legacy numeric comparisons', 'target': 'strict equality / relational operators', 'status': 'implemented'},
    {'source': 'unsupported GOTO / unstructured jumps', 'target': 'LLM fallback candidate or unsupported diagnostic', 'status': 'unsupported'},
    {'source': 'comment / line numbering', 'target': 'ignored metadata or translated to no-op', 'status': 'implemented'},
]


def get_rules_report():
    status_counts = {}
    for rule in RULES:
        status = rule.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1

    family_counts = {}
    for rule in RULES:
        source = rule.get('source', '')
        if source.startswith('COBOL'):
            family = 'COBOL'
        elif source.startswith('FORTRAN'):
            family = 'FORTRAN'
        elif source.startswith('Pascal'):
            family = 'Pascal'
        elif source.startswith('BASIC'):
            family = 'BASIC'
        elif 'Python-like' in source:
            family = 'Python-like'
        else:
            family = 'general'
        family_counts[family] = family_counts.get(family, 0) + 1

    return {
        'rule_table_version': RULE_TABLE_VERSION,
        'total_rules': len(RULES),
        'catalogue_entries': len(RULES),
        'is_executable_coverage_measure': False,
        'interpretation': 'Descriptive mapping catalogue only. Catalogue size and statuses do not measure supported language coverage; use benchmark pass rates and per-case construct coverage.',
        'implemented_rules': status_counts.get('implemented', 0),
        'status_counts': dict(sorted(status_counts.items())),
        'family_counts': dict(sorted(family_counts.items())),
        'rules': RULES,
    }
