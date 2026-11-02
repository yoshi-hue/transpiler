"""Small, auditable mutation set for validator sensitivity experiments."""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Mutation:
    mutation_id: str
    description: str
    code: str


def mutate_javascript(code: str) -> list[Mutation]:
    mutations = []
    replacements = [
        ('reverse-comparison', 'Reverse the first strict comparison', lambda s: s.replace('<', '>', 1)),
        ('arithmetic-off-by-one', 'Change the first numeric literal by one', lambda s: re.sub(r'\b\d+\b', lambda m: str(int(m.group()) + 1), s, count=1)),
        ('omit-output', 'Remove the first console output statement', lambda s: re.sub(r'\s*console\.log\([^;]+\);?', '', s, count=1)),
        ('loop-bound-off-by-one', 'Increase the first loop bound by one', lambda s: re.sub(r'i\s*<\s*(\d+)', lambda m: f'i < {int(m.group(1)) + 1}', s, count=1)),
    ]
    for mutation_id, description, transform in replacements:
        changed = transform(code)
        if changed != code:
            mutations.append(Mutation(mutation_id, description, changed))
    return mutations


def evaluate_mutations(code, run):
    """Return detected, equivalent, and inconclusive mutations from an oracle runner."""
    baseline = run(code)
    rows = []
    for mutation in mutate_javascript(code):
        result = run(mutation.code)
        if not result.get('available') or not baseline.get('available'):
            outcome = 'inconclusive'
        elif result.get('ok') != baseline.get('ok') or result.get('output') != baseline.get('output'):
            outcome = 'behaviorally_different'
        else:
            outcome = 'equivalent_under_fixture'
        rows.append({'mutation_id': mutation.mutation_id, 'description': mutation.description,
                     'outcome': outcome, 'observed_output': result.get('output'),
                     'error': result.get('error', '')})
    different = [row for row in rows if row['outcome'] == 'behaviorally_different']
    return {
        'baseline': {'ok': baseline.get('ok'), 'output': baseline.get('output')},
        'mutations': rows,
        'behaviorally_different': len(different),
        'equivalent_or_inconclusive': len(rows) - len(different),
        'interpretation': 'Sensitivity to tested mutations only; not proof of universal error detection.',
    }
