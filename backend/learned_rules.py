"""Exact-schema statement templates learned from validated examples.

This is a local, exact-schema cache. One example records only a rendering
template for one ordered IR schema; it does not infer new source semantics.
"""
import hashlib
import json
import re
from pathlib import Path
from threading import Lock

from .rules import RULE_TABLE_VERSION

RULE_STORE = Path(__file__).resolve().parent.parent / 'data' / 'learned_rules.jsonl'
_STORE_LOCK = Lock()
LEARNER_SCHEMA_VERSION = 2


def _atom_kind(expression):
    value = expression.strip()
    if re.fullmatch(r'-?\d+(?:\.\d+)?', value):
        return 'number'
    if re.fullmatch(r"(?:\"[^\"\n]*\"|'[^'\n]*')", value):
        return 'string'
    if value.lower() in ('true', 'false'):
        return 'boolean'
    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value):
        return 'identifier'
    return None


def _schema_from_ir(ir):
    if not isinstance(ir, list) or not 1 <= len(ir) <= 12:
        return None
    schema = []
    assigned_names = set()
    schema_names = {}
    for node in ir:
        if node.get('parent') is not None or node.get('kind') not in ('assign', 'print'):
            return None
        attributes = node.get('attributes', {})
        atom_kind = _atom_kind(attributes.get('expr', ''))
        if atom_kind is None:
            return None
        expression = attributes['expr'].strip()
        if atom_kind == 'identifier' and expression.lower() not in assigned_names:
            return None
        if node['kind'] == 'assign' and not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', attributes.get('name', '')):
            return None
        if node['kind'] == 'assign':
            name = attributes['name'].lower()
            if name in assigned_names or name in schema_names:
                return None
            assigned_names.add(name)
            schema_names[name] = f'v{len(schema_names)}'
        # Preserve identifier dependency shape while abstracting its spelling.
        value_ref = schema_names.get(expression.lower()) if atom_kind == 'identifier' else None
        schema.append({'kind': node['kind'], 'value_kind': atom_kind, 'value_ref': value_ref})
    return schema


def _target_template(target_language, node, generated_line):
    from .legacy import js_expr, py_expr

    attributes = node['attributes']
    expression = attributes['expr'].strip().rstrip(';.')
    rendered = js_expr(expression) if target_language == 'JavaScript' else py_expr(expression)
    if node['kind'] == 'assign':
        name = re.escape(attributes['name'])
        if target_language == 'JavaScript':
            pattern = rf'let\s+{name}\s*=\s*(.+);'
            template = 'let {{name}} = {{expr}};'
        else:
            pattern = rf'{name}\s*=\s*(.+)'
            template = '{{name}} = {{expr}}'
        match = re.fullmatch(pattern, generated_line)
        if match and match.group(1) == rendered:
            return template
    elif node['kind'] == 'print':
        if target_language == 'JavaScript':
            match = re.fullmatch(r'console\.log\((.*)\);', generated_line)
            template = 'console.log({{expr}});'
        else:
            match = re.fullmatch(r'print\((.*)\)', generated_line)
            template = 'print({{expr}})'
        if match and match.group(1) == rendered:
            return template
    return None


def find_generalized_rule(source_language, target_language, ir):
    schema = _schema_from_ir(ir)
    if schema is None or not RULE_STORE.exists():
        return None
    try:
        records = RULE_STORE.read_text(encoding='utf-8').splitlines()
    except OSError:
        return None
    for line in reversed(records):
        try:
            rule = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(rule, dict):
            continue
        if (rule.get('learner_schema_version') == LEARNER_SCHEMA_VERSION
                and rule.get('source_language') == source_language
                and rule.get('target_language') == target_language
                and rule.get('source_schema') == schema
                and rule.get('rule_table_version') == RULE_TABLE_VERSION
                and rule.get('status') == 'experimental_exact_schema'):
            return rule
    return None


def apply_generalized_rule(rule, ir):
    if (not rule or rule.get('learner_schema_version') != LEARNER_SCHEMA_VERSION
            or rule.get('rule_table_version') != RULE_TABLE_VERSION
            or rule.get('status') != 'experimental_exact_schema'
            or rule.get('source_schema') != _schema_from_ir(ir)
            or len(rule.get('target_templates', [])) != len(ir)):
        return None
    from .legacy import js_expr, py_expr

    convert = js_expr if rule['target_language'] == 'JavaScript' else py_expr
    output = []
    for node, template in zip(ir, rule['target_templates']):
        attributes = node.get('attributes', {})
        name = attributes.get('name', '')
        expression = attributes.get('expr', '')
        kind = node.get('kind')
        allowed_template = {
            ('assign', 'JavaScript'): 'let {{name}} = {{expr}};',
            ('assign', 'Python'): '{{name}} = {{expr}}',
            ('print', 'JavaScript'): 'console.log({{expr}});',
            ('print', 'Python'): 'print({{expr}})',
        }.get((kind, rule.get('target_language')))
        if template != allowed_template:
            return None
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name) and node.get('kind') == 'assign':
            return None
        if _atom_kind(expression) is None:
            return None
        output.append(template.replace('{{name}}', name).replace('{{expr}}', convert(expression)))
    return '\n'.join(output)


def learn_generalized_rule(source_language, target_language, source, ir, target_code, contract):
    """Induce a bounded statement-template rule from one passing example.

    Generalization is limited to flat assignment/print programs whose expressions
    are single literals or identifiers. The compiler's expression conversion remains
    authoritative; the learned part is the statement skeleton.
    """
    schema = _schema_from_ir(ir)
    if schema is None or contract.get('translation_status') != 'satisfied_for_tested_inputs':
        return None
    lines = target_code.splitlines()
    if len(lines) != len(ir):
        return None
    templates = []
    for node, line in zip(ir, lines):
        template = _target_template(target_language, node, line)
        if template is None:
            return None
        templates.append(template)
    rule_id = hashlib.sha256(json.dumps(
        [source_language, target_language, schema, templates, RULE_TABLE_VERSION],
        sort_keys=True, separators=(',', ':')
    ).encode('utf-8')).hexdigest()[:20]
    example = {
        'source_sha256': hashlib.sha256(source.encode('utf-8')).hexdigest(),
        'target_sha256': hashlib.sha256(target_code.encode('utf-8')).hexdigest(),
        'contract_id': contract['contract_id'],
    }
    rule = {
        'rule_id': rule_id,
        'source_language': source_language,
        'target_language': target_language,
        'source_schema': schema,
        'target_templates': templates,
        'rule_table_version': RULE_TABLE_VERSION,
        'learner_schema_version': LEARNER_SCHEMA_VERSION,
        'status': 'experimental_exact_schema',
        'generalizes': False,
        'scope': 'exact ordered flat assignment/print IR schema; values and consistently renamed identifiers are slots; source semantics are not inferred',
        'examples': [example],
    }
    RULE_STORE.parent.mkdir(parents=True, exist_ok=True)
    with _STORE_LOCK:
        existing = find_generalized_rule(source_language, target_language, ir)
        if existing:
            rule = existing
            if example not in rule.get('examples', []):
                rule['examples'] = [*rule.get('examples', []), example][-20:]
        with RULE_STORE.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(rule, ensure_ascii=False, sort_keys=True) + '\n')
    return rule
