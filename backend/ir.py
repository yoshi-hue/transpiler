from dataclasses import asdict, is_dataclass
from .ast_nodes import *

class SharedIR:
    """A small language-neutral whole-program IR for the course prototype.

    The source AST is lowered into generic nodes with IDs, parent references and
    scope information. A production version would define a richer typed IR.
    """
    def __init__(self, program):
        self.nodes = []
        self._build(program, parent=None, scope='global')

    def _build(self, node, parent, scope):
        if node is None:
            return None
        if isinstance(node, list):
            return [self._build(x, parent, scope) for x in node]
        if isinstance(node, tuple):
            return [self._build(x, parent, scope) for x in node]
        if not is_dataclass(node):
            return node

        node_id = len(self.nodes)
        entry = {
            'id': node_id,
            'kind': node.__class__.__name__,
            'parent': parent,
            'scope': scope,
            'children': [],
            'fields': {},
        }
        self.nodes.append(entry)

        child_scope = scope
        if isinstance(node, FunctionDef):
            child_scope = f'{scope}.{node.name}'

        for field_name in node.__dataclass_fields__:
            value = getattr(node, field_name)
            child_ids = []
            if isinstance(value, (list, tuple)):
                for item in value:
                    if is_dataclass(item):
                        child_id = self._build(item, node_id, child_scope)
                        if isinstance(child_id, int): child_ids.append(child_id)
                    elif isinstance(item, tuple):
                        for nested in item:
                            if is_dataclass(nested):
                                child_id = self._build(nested, node_id, child_scope)
                                if isinstance(child_id, int): child_ids.append(child_id)
            elif is_dataclass(value):
                child_id = self._build(value, node_id, child_scope)
                if isinstance(child_id, int): child_ids.append(child_id)
            if child_ids:
                entry['children'].extend(child_ids)
                entry['fields'][field_name] = child_ids
            elif not isinstance(value, (list, tuple)):
                entry['fields'][field_name] = value
        return node_id

    def to_dict(self):
        edges = [
            {'parent': node['id'], 'child': child_id}
            for node in self.nodes
            for child_id in node['children']
        ]
        return {
            'representation': 'SharedIR',
            'language_neutral': True,
            'node_count': len(self.nodes),
            'edge_count': len(edges),
            'scopes': sorted({node['scope'] for node in self.nodes}),
            'nodes': self.nodes,
            'edges': edges,
        }
