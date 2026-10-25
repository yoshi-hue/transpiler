"""Small, documented legacy-language front ends for the course prototype.
Supported subsets are intentionally limited and reject unsupported syntax instead of guessing.
"""
import ast
import re
from dataclasses import dataclass

LANGUAGES = {
    'COBOL': 'COBOL subset',
    'FORTRAN': 'FORTRAN 77/90-style subset',
    'Pascal': 'Pascal subset',
    'BASIC': 'BASIC (line-numbered) subset',
    'Python-like': 'Python-like subset',
}

SUBSETS = {
    'COBOL': ['WORKING-STORAGE numeric declarations with VALUE', 'MOVE', 'COMPUTE', 'DISPLAY', 'IF/ELSE/END-IF', 'STOP RUN'],
    'FORTRAN': ['INTEGER/REAL declarations', 'scalar list-directed READ', 'assignment', 'PRINT */formatted scalar WRITE', 'IF/ELSE/END IF', 'DO/END DO', 'integer division truncating toward zero', 'MOD with dividend-sign remainder'],
    'Pascal': ['var declarations', 'assignment :=', 'writeln/write', 'if/then/else', 'for/to/do', 'while/do'],
    'BASIC': ['line-numbered LET/assignment', 'PRINT', 'IF ... THEN ...', 'FOR/NEXT', 'END/STOP'],
}

@dataclass
class LegacyResult:
    language: str
    target: str
    javascript: str
    tokens: list
    ir: list
    symbols: dict
    rules_used: list
    coverage: dict
    source_program: list
    unsupported: list
    notes: list

class UnsupportedSyntax(Exception):
    pass

def _tok(text, kind='SYMBOL'):
    return {'type': kind, 'value': text}

def tokenize_legacy(code, language):
    # Deliberately lightweight: enough lexical evidence for the supported subset.
    pattern = r'"[^"\n]*"|\'[^\'\n]*\'|\b\d+(?:\.\d+)?\b|[A-Za-z_][A-Za-z0-9_-]*|:=|<=|>=|<>|==|[+\-*/=<>(),.:;]'
    return [_tok(m.group(0), 'STRING' if m.group(0)[0:1] in "\"'" else 'NUMBER' if m.group(0)[0:1].isdigit() else 'IDENT' if re.match(r'[A-Za-z_]', m.group(0)) else 'SYMBOL') for m in re.finditer(pattern, code)]

def expr(e):
    e = e.strip().rstrip('.')
    e = e.replace('<>', '!=')
    e = re.sub(r'(?<![<>!])=(?!=)', '==', e)
    e = re.sub(r'\bAND\b', 'and', e, flags=re.I)
    e = re.sub(r'\bOR\b', 'or', e, flags=re.I)
    e = re.sub(r'\bNOT\b', 'not', e, flags=re.I)
    e = re.sub(r'\bTRUE\b', 'True', e, flags=re.I)
    e = re.sub(r'\bFALSE\b', 'False', e, flags=re.I)
    return e

def js_expr(e):
    e = e.strip().rstrip(';.')
    e = re.sub(r'\bAND\b', '&&', e, flags=re.I)
    e = re.sub(r'\bOR\b', '||', e, flags=re.I)
    e = re.sub(r'\bNOT\b', '!', e, flags=re.I)
    e = e.replace('<>', '!=')
    e = re.sub(r'(?<![<>!=])=(?!=)', '==', e)
    e = re.sub(r'\bTRUE\b', 'true', e, flags=re.I)
    e = re.sub(r'\bFALSE\b', 'false', e, flags=re.I)
    return e

def _node_expr(node, key, target):
    value=node[key]
    if node.get('integer_division') or node.get('fortran_mod'):
        # Preserve malformed/unsupported Fortran constructs for diagnostics; the
        # case is explicitly rejected below and must not fail the whole pipeline.
        unsupported_call=re.search(r'\b(?!MOD\b)[A-Za-z_]\w*\s*\(',value,re.I)
        unsupported_array=re.search(r'\b[A-Za-z_]\w*\s*\([^)]*:',value)
        if not (unsupported_call or unsupported_array):
            value=_rewrite_fortran_intrinsics(expr(value), integer_division=node.get('integer_division',False))
    return js_expr(value) if target=='JavaScript' else py_expr(value)

def strip_comment(line):
    s=line.strip()
    if not s: return ''
    if s.startswith('*'): return ''
    return s

def _cobol_lines(code):
    lines=[]; current=[]; quote=None; i=0
    while i<len(code):
        ch=code[i]
        if quote:
            current.append(ch)
            if ch==quote:
                if i+1<len(code) and code[i+1]==quote:
                    current.append(code[i+1]); i+=1
                else:
                    quote=None
        elif ch in ("'", '"'):
            quote=ch; current.append(ch)
        elif code[i:i+11].upper()=='PROGRAM-ID.':
            match=re.match(r'PROGRAM-ID\.\s*[A-Za-z0-9-]+\.',code[i:],re.I)
            if match:
                current.extend(match.group())
                i+=len(match.group())-1
                lines.append(''.join(current).strip()); current=[]
        elif ch=='.' and (i+1==len(code) or code[i+1].isspace()):
            current.append(ch)
            if ''.join(current).strip(): lines.append(''.join(current).strip())
            current=[]
        elif ch in '\r\n':
            if ''.join(current).strip(): lines.append(''.join(current).strip())
            current=[]
        else:
            current.append(ch)
        i+=1
    if ''.join(current).strip(): lines.append(''.join(current).strip())
    return lines

def parse_cobol(code):
    lines=[strip_comment(x) for x in _cobol_lines(code)]
    lines=[x for x in lines if x]
    nodes=[]; symbols={}; unsupported=[]; i=0
    in_proc=False
    while i<len(lines):
        s=lines[i].rstrip('.')
        up=s.upper()
        if up.startswith(('IDENTIFICATION DIVISION','PROGRAM-ID','DATA DIVISION','WORKING-STORAGE SECTION','ENVIRONMENT DIVISION')):
            i+=1; continue
        if up.startswith('PROCEDURE DIVISION'):
            in_proc=True; i+=1; continue
        m=re.match(r'^\d+\s+(\w+)\s+PIC\s+(?:9+|9\(\d+\))\s+VALUE\s+(.+)$',s,re.I)
        if m:
            name=m.group(1); val=m.group(2); symbols[name]='variable'; nodes.append({'kind':'assign','name':name,'expr':val})
            i+=1; continue
        if re.match(r'^\d+\s+\w+\s+PIC\b',s,re.I):
            unsupported.append(s); i+=1; continue
        if not in_proc:
            unsupported.append(s); i+=1; continue
        m=re.match(r'MOVE\s+(.+?)\s+TO\s+(\w+)$',s,re.I)
        if m: nodes.append({'kind':'assign','name':m.group(2),'expr':m.group(1)}); symbols[m.group(2)]='variable'; i+=1; continue
        m=re.match(r'COMPUTE\s+(\w+)\s*=\s*(.+)$',s,re.I)
        if m: nodes.append({'kind':'assign','name':m.group(1),'expr':m.group(2)}); symbols[m.group(1)]='variable'; i+=1; continue
        m=re.match(r'DISPLAY\s+(.+)$',s,re.I)
        if m: nodes.append({'kind':'print','expr':m.group(1)}); i+=1; continue
        m=re.match(r'IF\s+(.+)$',s,re.I)
        if m:
            cond=m.group(1); then=[]; els=[]; i+=1; cur=then
            while i<len(lines):
                q=lines[i].rstrip('.'); qu=q.upper()
                if qu.startswith('ELSE'): cur=els; i+=1; continue
                if qu.startswith('END-IF'): i+=1; break
                q2=q.rstrip('.')
                mm=re.match(r'MOVE\s+(.+?)\s+TO\s+(\w+)$',q2,re.I)
                mc=re.match(r'COMPUTE\s+(\w+)\s*=\s*(.+)$',q2,re.I)
                md=re.match(r'DISPLAY\s+(.+)$',q2,re.I)
                if mm: cur.append({'kind':'assign','name':mm.group(2),'expr':mm.group(1)}); symbols[mm.group(2)]='variable'
                elif mc: cur.append({'kind':'assign','name':mc.group(1),'expr':mc.group(2)}); symbols[mc.group(1)]='variable'
                elif md: cur.append({'kind':'print','expr':md.group(1)})
                else: unsupported.append(q2)
                i+=1
            nodes.append({'kind':'if','cond':cond,'then':then,'else':els}); continue
        if up.startswith('STOP RUN'): i+=1; continue
        unsupported.append(s); i+=1
    return nodes,symbols,unsupported

def parse_fortran(code):
    lines=[strip_comment(x) for x in code.splitlines() if strip_comment(x)]
    nodes=[]; symbols={}; unsupported=[]; stack=[]; root=nodes; integer_names=set()
    i=0
    while i<len(lines):
        s=re.sub(r'^\s*\d+\s*','',lines[i]).strip(); up=s.upper()
        if up.startswith(('PROGRAM ','END PROGRAM','IMPLICIT NONE')): i+=1; continue
        if up.startswith('END IF'):
            root=stack.pop()[0]; i+=1; continue
        if up.startswith('END DO'):
            root=stack.pop()[0]; i+=1; continue
        if up=='END': i+=1; continue
        m=re.match(r'(INTEGER|REAL)(?:\s*::)?\s+(.+)$',s,re.I)
        if m:
            for n in m.group(2).split(','):
                name=n.strip().upper(); symbols[name]='variable'
                if m.group(1).upper()=='INTEGER': integer_names.add(name.lower())
            i+=1; continue
        m=re.match(r'READ\s*\(\s*\*\s*,\s*\*\s*\)\s*(.+)$',s,re.I)
        if not m:
            m=re.match(r'READ\s*\*\s*,\s*\*\s*(.+)$',s,re.I)
        if m:
            names=[name.strip() for name in m.group(1).split(',') if name.strip()]
            if names and all(re.fullmatch(r'[A-Za-z_]\w*', name) for name in names):
                root.append({'kind':'input','names':names})
                for name in names: symbols[name.lower()]='variable'
            else:
                unsupported.append(s)
            i+=1; continue
        m=re.match(r'IF\s*\((.+)\)\s*THEN$',s,re.I)
        if m:
            node={'kind':'if','cond':m.group(1),'then':[],'else':[]}; root.append(node); stack.append((root,node)); root=node['then']; i+=1; continue
        if up=='ELSE': root=stack[-1][1]['else']; i+=1; continue
        m=re.match(r'DO\s+(\w+)\s*=\s*([^,]+),\s*(.+)$',s,re.I)
        if m:
            node={'kind':'for','name':m.group(1),'start':m.group(2),'end':m.group(3),'body':[]}; root.append(node); stack.append((root,node)); root=node['body']; symbols[m.group(1).upper()]='variable'; i+=1; continue
        m=re.match(r'PRINT\s*\*,\s*(.+)$',s,re.I)
        if m: root.append({'kind':'print','expr':m.group(1)}); i+=1; continue
        m=re.match(r'WRITE\s*\(\s*\*\s*,\s*([\'\"]).*?\1\s*\)\s*(.+)$',s,re.I)
        if m: root.append({'kind':'print','expr':m.group(2)}); i+=1; continue
        m=re.match(r'(\w+)\s*=\s*(.+)$',s)
        if m: root.append({'kind':'assign','name':m.group(1),'expr':m.group(2)}); symbols[m.group(1).upper()]='variable'; i+=1; continue
        unsupported.append(s); i+=1
    def mark_integer_division(ns):
        for node in ns:
            expressions=[node[key] for key in ('expr','cond','start','end') if key in node]
            for expression in expressions:
                if re.search(r'\b(?!MOD\b)[A-Za-z_]\w*\s*\(',expression,re.I) or re.search(r'\b[A-Za-z_]\w*\s*\([^)]*:',expression):
                    unsupported.append('Unsupported Fortran function or array expression: '+expression)
            names=set()
            for expression in expressions:
                names.update(re.findall(r'\b[A-Za-z_]\w*\b',expression))
            expression_names={name.lower() for name in names if name.lower() not in {'mod'}}
            node['integer_division']=bool(expressions and any('/' in expression for expression in expressions)
                and expression_names and expression_names <= integer_names)
            node['fortran_mod']=bool(expressions and any(re.search(r'\bMOD\s*\(', expression, re.I) for expression in expressions))
            for key in ('then','else','body'):
                if key in node: mark_integer_division(node[key])
    mark_integer_division(nodes)
    return nodes,{k.lower():v for k,v in symbols.items()},unsupported

def parse_pascal(code):
    s=re.sub(r'\{.*?\}|//.*','',code,flags=re.S)
    lines=[x.strip() for x in s.splitlines() if x.strip()]
    text=' '.join(lines)
    text=re.sub(r'\s+',' ',text)
    text=re.sub(r'\bbegin\b\s*', '', text, flags=re.I)
    text=re.sub(r'\bend\.?\s*$', '', text, flags=re.I)
    stmts=[x.strip() for x in re.split(r';',text) if x.strip()]
    nodes=[]; symbols={}; unsupported=[]
    for st in stmts:
        up=st.upper()
        if up.startswith(('PROGRAM ','BEGIN','END')): continue
        m=re.match(r'VAR\s+(.+)',st,re.I)
        if m:
            mm=re.match(r'(.+?)\s*:\s*(\w+)$',m.group(1).strip(),re.I)
            if mm:
                for name in mm.group(1).split(','): symbols[name.strip()]='variable'
            else: unsupported.append(st)
            continue
        m=re.match(r'(\w+)\s*:=\s*(.+)',st,re.I)
        if m: nodes.append({'kind':'assign','name':m.group(1),'expr':m.group(2)}); symbols[m.group(1)]='variable'; continue
        m=re.match(r'(?:WRITELN|WRITE)\s*\((.*)\)',st,re.I)
        if m: nodes.append({'kind':'print','expr':m.group(1)}); continue
        m=re.match(r'IF\s+(.+?)\s+THEN\s+(.+?)\s+ELSE\s+(.+)',st,re.I)
        if m: nodes.append({'kind':'if','cond':m.group(1),'then':[{'kind':'raw','text':m.group(2)}],'else':[{'kind':'raw','text':m.group(3)}]}); continue
        m=re.match(r'FOR\s+(\w+)\s*:=\s*(.+?)\s+TO\s+(.+?)\s+DO\s+(.+)',st,re.I)
        if m: nodes.append({'kind':'for','name':m.group(1),'start':m.group(2),'end':m.group(3),'body':[{'kind':'raw','text':m.group(4)}]}); symbols[m.group(1)]='variable'; continue
        m=re.match(r'WHILE\s+(.+?)\s+DO\s+(.+)',st,re.I)
        if m: nodes.append({'kind':'while','cond':m.group(1),'body':[{'kind':'raw','text':m.group(2)}]}); continue
        unsupported.append(st)
    # Resolve raw single statements recursively.
    def resolve(ns):
        out=[]
        for n in ns:
            if n['kind']=='raw':
                q=parse_pascal(n['text']+';'); out.extend(q[0]); unsupported.extend(q[2])
            else:
                for k in ('then','else','body'):
                    if k in n: n[k]=resolve(n[k])
                out.append(n)
        return out
    return resolve(nodes),symbols,unsupported

def parse_basic(code):
    lines=[]
    for raw in code.splitlines():
        s=raw.strip()
        if not s: continue
        m=re.match(r'^(\d+)\s+(.*)$',s); lines.append((int(m.group(1)),m.group(2).strip()) if m else (len(lines)+1,s))
    nodes=[]; symbols={}; unsupported=[]; i=0
    while i<len(lines):
        s=lines[i][1]; up=s.upper()
        s=re.sub(r'^REM\s+.*$','',s,flags=re.I)
        if not s: i+=1; continue
        m=re.match(r'(?:LET\s+)?(\w+)\s*=\s*(.+)$',s,re.I)
        if m: nodes.append({'kind':'assign','name':m.group(1),'expr':m.group(2)}); symbols[m.group(1)]='variable'; i+=1; continue
        m=re.match(r'PRINT\s+(.+)$',s,re.I)
        if m: nodes.append({'kind':'print','expr':m.group(1)}); i+=1; continue
        m=re.match(r'IF\s+(.+?)\s+THEN\s+(.+)$',s,re.I)
        if m:
            inner=parse_basic('1 '+m.group(2))[0]
            nodes.append({'kind':'if','cond':m.group(1),'then':inner,'else':[]}); i+=1; continue
        m=re.match(r'FOR\s+(\w+)\s*=\s*(.+?)\s+TO\s+(.+)$',s,re.I)
        if m:
            name,start,end=m.group(1),m.group(2),m.group(3); body=[]; i+=1
            while i<len(lines) and not re.match(r'NEXT(?:\s+\w+)?$',lines[i][1],re.I):
                body.extend(parse_basic('1 '+lines[i][1])[0]); i+=1
            if i>=len(lines): unsupported.append('FOR without NEXT'); break
            nodes.append({'kind':'for','name':name,'start':start,'end':end,'body':body}); symbols[name]='variable'; i+=1; continue
        if up in ('END','STOP','STOP RUN'): i+=1; continue
        unsupported.append(s); i+=1
    return nodes,symbols,unsupported

def parse(language, code):
    if language=='COBOL': return parse_cobol(code)
    if language=='FORTRAN': return parse_fortran(code)
    if language=='Pascal': return parse_pascal(code)
    if language=='BASIC': return parse_basic(code)
    raise UnsupportedSyntax(f'Unsupported source language: {language}')

def _fortran_integer_division(left, right):
    a=int(left); b=int(right)
    if b == 0: raise ZeroDivisionError('integer division by zero')
    quotient=abs(a)//abs(b)
    return -quotient if (a < 0) != (b < 0) else quotient

def _fortran_mod(left, right):
    """Fortran MOD returns a remainder with the dividend's sign."""
    a=int(left); b=int(right)
    return a - _fortran_integer_division(a, b) * b

class _FortranExpressionRewrite(ast.NodeTransformer):
    def __init__(self, integer_division):
        self.integer_division = integer_division

    def visit_Call(self, node):
        self.generic_visit(node)
        if (isinstance(node.func, ast.Name) and node.func.id.lower() == 'mod'
                and len(node.args) == 2 and not node.keywords):
            return ast.copy_location(ast.Call(
                func=ast.Name(id='__fortran_mod', ctx=ast.Load()),
                args=node.args, keywords=[]), node)
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if self.integer_division and isinstance(node.op, ast.Div):
            return ast.copy_location(ast.Call(
                func=ast.Name(id='__fortran_idiv', ctx=ast.Load()),
                args=[node.left, node.right], keywords=[]), node)
        return node

def _rewrite_fortran_intrinsics(expression, integer_division=False):
    tree=ast.parse(expression,mode='eval')
    tree=_FortranExpressionRewrite(integer_division).visit(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree.body)

def eval_expr(e, env, integer_division=False, fortran_mod=False):
    e=e.strip().rstrip(';.')
    e=re.sub(r"'([^']*)'", r'"\1"', e)
    e=e.replace('<>','!=')
    e=re.sub(r'(?<![<>!=])=(?!=)', '==', e)
    e=re.sub(r'\bAND\b','and',e,flags=re.I); e=re.sub(r'\bOR\b','or',e,flags=re.I); e=re.sub(r'\bNOT\b','not',e,flags=re.I)
    e=re.sub(r'\bTRUE\b','True',e,flags=re.I); e=re.sub(r'\bFALSE\b','False',e,flags=re.I)
    if integer_division or fortran_mod:
        e=_rewrite_fortran_intrinsics(e, integer_division=integer_division)
    # COBOL / Fortran identifiers are case-insensitive in our subset.
    local={k:v for k,v in env.items()}; local.update({k.upper():v for k,v in env.items()})
    local['__fortran_idiv']=_fortran_integer_division
    local['__fortran_mod']=_fortran_mod
    try: return eval(e, {'__builtins__':{}}, local)
    except Exception: raise UnsupportedSyntax(f'Could not evaluate supported expression: {e}')

def record_expression_rules(expression, rules, target):
    if re.search(r'[+*/%]|\s-\s', expression):
        rules.append(f'arithmetic → {target} operators')
    if re.search(r'<=|>=|<>|!=|==|(?<![<>=])=(?!=)|[<>]', expression):
        rules.append(f'comparison → {target} operators')
    if re.search(r'\b(?:AND|OR|NOT)\b', expression, re.I):
        rules.append(f'logical → {target} operators')

def _input_number(token):
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return token

def _split_top_level_commas(text):
    """Split a list-directed expression only at commas outside nested calls/strings."""
    parts=[]; start=0; depth=0; quote=None; i=0
    while i < len(text):
        ch=text[i]
        if quote:
            if ch==quote:
                if i+1 < len(text) and text[i+1]==quote:
                    i+=1
                else:
                    quote=None
        elif ch in ('"', "'"):
            quote=ch
        elif ch=='(':
            depth+=1
        elif ch==')':
            depth=max(0,depth-1)
        elif ch==',' and depth==0:
            parts.append(text[start:i].strip()); start=i+1
        i+=1
    parts.append(text[start:].strip())
    return [part for part in parts if part]

def run_nodes(nodes, env, output, input_values=None):
    if input_values is None:
        input_values=[]
    for n in nodes:
        k=n['kind']
        if k=='input':
            for name in n['names']:
                if not input_values:
                    raise UnsupportedSyntax('Input fixture is required to validate this program.')
                value=_input_number(input_values.pop(0))
                env[name]=value; env[name.upper()]=value; env[name.lower()]=value
        elif k=='assign':
            val=eval_expr(n['expr'],env,n.get('integer_division',False),n.get('fortran_mod',False)); env[n['name']]=val; env[n['name'].upper()]=val; env[n['name'].lower()]=val
        elif k=='print':
            # DISPLAY/PRINT can contain comma-separated values; join with a space.
            vals=[eval_expr(x,env,n.get('integer_division',False),n.get('fortran_mod',False)) for x in _split_top_level_commas(n['expr'])]
            output.append(' '.join(str(v) for v in vals))
        elif k=='if':
            branch=n['then'] if eval_expr(n['cond'],env,n.get('integer_division',False),n.get('fortran_mod',False)) else n['else']; run_nodes(branch,env,output,input_values)
        elif k=='for':
            a=int(eval_expr(n['start'],env,n.get('integer_division',False),n.get('fortran_mod',False))); b=int(eval_expr(n['end'],env,n.get('integer_division',False),n.get('fortran_mod',False)));
            for v in range(a,b+1):
                env[n['name']]=v; env[n['name'].upper()]=v; env[n['name'].lower()]=v; run_nodes(n['body'],env,output,input_values)
        elif k=='while':
            guard=0
            while eval_expr(n['cond'],env,n.get('integer_division',False),n.get('fortran_mod',False)):
                run_nodes(n['body'],env,output,input_values); guard+=1
                if guard>10000: raise UnsupportedSyntax('Loop exceeded validation guard')
        else: raise UnsupportedSyntax(f'Unsupported internal node: {k}')

def generate_js(nodes, indent=0, declared=None, rules=None):
    if declared is None: declared=set()
    if rules is None: rules=[]
    out=[]; pad='    '*indent
    for n in nodes:
        k=n['kind']
        if k=='assign':
            record_expression_rules(n['expr'], rules, 'JavaScript')
            name=n['name']; prefix='let ' if name not in declared else ''
            declared.add(name); out.append(pad+prefix+name+' = '+_node_expr(n,'expr','JavaScript')+';'); rules.append('assignment → JavaScript let/assignment')
        elif k=='input':
            for name in n['names']:
                prefix='let ' if name not in declared else ''
                declared.add(name)
                out.append(pad+prefix+name+' = Number(__inputTokens[__inputIndex++]);')
            rules.append('list-directed input -> JavaScript stdin')
        elif k=='print':
            record_expression_rules(n['expr'], rules, 'JavaScript')
            out.append(pad+'console.log('+_node_expr(n,'expr','JavaScript')+');'); rules.append('output → console.log')
        elif k=='if':
            record_expression_rules(n['cond'], rules, 'JavaScript')
            out.append(pad+'if ('+_node_expr(n,'cond','JavaScript')+') {'); rules.append('conditional → if/else')
            out.extend(generate_js(n['then'],indent+1,declared,rules));
            if n['else']:
                out.append(pad+'} else {'); out.extend(generate_js(n['else'],indent+1,declared,rules))
            out.append(pad+'}')
        elif k=='for':
            record_expression_rules(n['start'], rules, 'JavaScript')
            record_expression_rules(n['end'], rules, 'JavaScript')
            name=n['name']; start=_node_expr(n,'start','JavaScript'); end=_node_expr(n,'end','JavaScript');
            out.append(pad+f'for (let {name} = {start}; {name} <= {end}; {name}++) {{'); rules.append('loop → JavaScript for')
            out.extend(generate_js(n['body'],indent+1,declared,rules)); out.append(pad+'}')
        elif k=='while':
            record_expression_rules(n['cond'], rules, 'JavaScript')
            out.append(pad+'while ('+_node_expr(n,'cond','JavaScript')+') {'); rules.append('loop → JavaScript while'); out.extend(generate_js(n['body'],indent+1,declared,rules)); out.append(pad+'}')
    return out


def generate_python(nodes, indent=0, declared=None, rules=None):
    """Generate readable Python from the shared normalized node representation."""
    if declared is None: declared=set()
    if rules is None: rules=[]
    out=[]; pad='    '*indent
    for n in nodes:
        k=n['kind']
        if k=='assign':
            record_expression_rules(n['expr'], rules, 'Python')
            name=n['name']; out.append(pad+name+' = '+_node_expr(n,'expr','Python')); declared.add(name)
            rules.append('assignment → Python assignment')
        elif k=='input':
            for name in n['names']:
                out.append(pad+name+' = __read_number()')
            rules.append('list-directed input -> Python stdin')
        elif k=='print':
            record_expression_rules(n['expr'], rules, 'Python')
            out.append(pad+'print('+_node_expr(n,'expr','Python')+')'); rules.append('output → Python print')
        elif k=='if':
            record_expression_rules(n['cond'], rules, 'Python')
            out.append(pad+'if '+_node_expr(n,'cond','Python')+':'); rules.append('conditional → Python if/else')
            body=generate_python(n['then'],indent+1,declared,rules); out.extend(body or [pad+'    pass'])
            if n['else']:
                out.append(pad+'else:'); out.extend(generate_python(n['else'],indent+1,declared,rules) or [pad+'    pass'])
        elif k=='for':
            record_expression_rules(n['start'], rules, 'Python')
            record_expression_rules(n['end'], rules, 'Python')
            out.append(pad+f'for {n["name"]} in range({_node_expr(n,"start","Python")}, ({_node_expr(n,"end","Python")} + 1)):'); rules.append('loop → Python range')
            out.extend(generate_python(n['body'],indent+1,declared,rules) or [pad+'    pass'])
        elif k=='while':
            record_expression_rules(n['cond'], rules, 'Python')
            out.append(pad+'while '+_node_expr(n,'cond','Python')+':'); rules.append('loop → Python while')
            out.extend(generate_python(n['body'],indent+1,declared,rules) or [pad+'    pass'])
    return out


def py_expr(e):
    e=e.strip().rstrip(';.')
    e=re.sub(r'\bAND\b','and',e,flags=re.I); e=re.sub(r'\bOR\b','or',e,flags=re.I); e=re.sub(r'\bNOT\b','not',e,flags=re.I)
    e=re.sub(r'\bTRUE\b','True',e,flags=re.I); e=re.sub(r'\bFALSE\b','False',e,flags=re.I)
    e=e.replace('<>','!=')
    e=re.sub(r'(?<![<>!=])=(?!=)', '==', e)
    return e

def legacy_transpile(language, code, target='JavaScript'):
    if target not in ('JavaScript', 'Python'):
        raise UnsupportedSyntax('Legacy-language prototype currently targets JavaScript or Python.')
    nodes,symbols,unsupported=parse(language,code)
    rules=[]
    if target=='JavaScript':
        generated=generate_js(nodes,rules=rules)
    else:
        generated=generate_python(nodes,rules=rules)
    input_nodes=[]; has_integer_division=False; has_fortran_mod=False
    def find_inputs(ns):
        nonlocal has_integer_division, has_fortran_mod
        for node in ns:
            if node['kind']=='input': input_nodes.extend(node['names'])
            has_integer_division = has_integer_division or node.get('integer_division',False)
            has_fortran_mod = has_fortran_mod or node.get('fortran_mod',False)
            for key in ('then','else','body'):
                if key in node: find_inputs(node[key])
    find_inputs(nodes)
    output='\n'.join(generated)
    if target=='JavaScript':
        prelude=[]
        if input_nodes:
            prelude.extend(["const __inputTokens = require('fs').readFileSync(0, 'utf8').trim().split(/\\s+/).filter(Boolean);", 'let __inputIndex = 0;'])
        if has_integer_division:
            prelude.append('const __fortran_idiv = (a, b) => Math.trunc(a / b);')
        if has_fortran_mod:
            prelude.append('const __fortran_mod = (a, b) => a - Math.trunc(a / b) * b;')
        if prelude: output='\n'.join(prelude)+'\n'+output
    elif input_nodes or has_integer_division or has_fortran_mod:
        prelude=[]
        if input_nodes:
            prelude.extend(["import sys", "__inputTokens = iter(sys.stdin.read().split())", "def __read_number():", "    token = next(__inputTokens)", "    try:", "        return int(token)", "    except ValueError:", "        return float(token)"])
        if has_integer_division:
            prelude.extend(["def __fortran_idiv(a, b):", "    a, b = int(a), int(b)", "    q = abs(a) // abs(b)", "    return -q if (a < 0) != (b < 0) else q"])
        if has_fortran_mod:
            prelude.extend(["def __fortran_mod(a, b):", "    a, b = int(a), int(b)", "    q = abs(a) // abs(b)", "    q = -q if (a < 0) != (b < 0) else q", "    return a - q * b"])
        output='\n'.join(prelude)+'\n\n'+output
    source_out=[]
    # Source interpreter is intentionally limited to the documented subset.
    if not input_nodes:
        run_nodes(nodes,{},source_out)
    ir=[]; idx=0
    def walk(ns,parent=None,scope='global'):
        nonlocal idx
        for n in ns:
            idx+=1
            attrs={k:v for k,v in n.items() if k not in ('then','else','body')}
            ir.append({'id':idx,'kind':n['kind'],'parent':parent,'scope':scope,'attributes':attrs})
            for key in ('then','else','body'):
                if key in n: walk(n[key],idx,scope)
    walk(nodes)
    unique_rules=list(dict.fromkeys(rules))
    translated_units=len(ir)
    unsupported_units=len(unsupported)
    source_units=translated_units+unsupported_units
    coverage={
        'coverage_basis':'parsed IR statement nodes plus parser-reported unsupported constructs',
        'source_units':source_units,
        'translated_units':translated_units,
        'unsupported_units':unsupported_units,
        'rules_used':len(unique_rules),
        'deterministic_rules':len(unique_rules),
        'coverage_percent':round((translated_units/source_units)*100,1) if source_units else 100.0,
        'coverage_breakdown':unique_rules,
    }
    notes=['Subset translation: '+LANGUAGES[language],
           'Shared normalized representation is lowered to the selected target backend.',
           'Rule-first translation is applied before optional LLM fallback.',
           'Unsupported constructs are surfaced explicitly and are never silently treated as translated.']
    return LegacyResult(language,target,output,tokenize_legacy(code,language),ir,symbols,unique_rules,coverage,nodes,unsupported,notes)
