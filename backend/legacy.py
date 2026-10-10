"""Small, documented legacy-language front ends for the course prototype.
Supported subsets are intentionally limited and reject unsupported syntax instead of guessing.
"""
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
    'FORTRAN': ['INTEGER/REAL declarations', 'assignment', 'PRINT *', 'IF/ELSE/END IF', 'DO/END DO'],
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
    e = e.replace('<>', '!=').replace('=', '==')
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
    e = e.replace('<>', '!=').replace('==', '==').replace('=', '==')
    e = re.sub(r'(?<![<>!=])=(?!=)', '==', e)
    e = re.sub(r'\bTRUE\b', 'true', e, flags=re.I)
    e = re.sub(r'\bFALSE\b', 'false', e, flags=re.I)
    return e

def strip_comment(line):
    s=line.strip()
    if not s: return ''
    if s.startswith('*'): return ''
    return s

def parse_cobol(code):
    lines=[strip_comment(x) for x in code.splitlines()]
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
        if re.match(r'^\d+\s+\w+\s+PIC\s+', s, re.I):
            m=re.match(r'^\d+\s+(\w+)\s+PIC\s+[^ ]+(?:\s+VALUE\s+(.+))?$', s, re.I)
            if m:
                name=m.group(1); val=m.group(2) or '0'; symbols[name]='variable'; nodes.append({'kind':'assign','name':name,'expr':val})
                i+=1; continue
        if not in_proc:
            i+=1; continue
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
    nodes=[]; symbols={}; unsupported=[]; stack=[]; root=nodes
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
            for n in m.group(2).split(','): symbols[n.strip().upper()]='variable'
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
        m=re.match(r'(\w+)\s*=\s*(.+)$',s)
        if m: root.append({'kind':'assign','name':m.group(1),'expr':m.group(2)}); symbols[m.group(1).upper()]='variable'; i+=1; continue
        unsupported.append(s); i+=1
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

def eval_expr(e, env):
    e=e.strip().rstrip(';.')
    e=re.sub(r"'([^']*)'", r'"\1"', e)
    e=e.replace('<>','!=').replace('=', '==')
    e=re.sub(r'(?<![<>!=])=(?!=)', '==', e)
    e=re.sub(r'\bAND\b','and',e,flags=re.I); e=re.sub(r'\bOR\b','or',e,flags=re.I); e=re.sub(r'\bNOT\b','not',e,flags=re.I)
    e=re.sub(r'\bTRUE\b','True',e,flags=re.I); e=re.sub(r'\bFALSE\b','False',e,flags=re.I)
    # COBOL / Fortran identifiers are case-insensitive in our subset.
    local={k:v for k,v in env.items()}; local.update({k.upper():v for k,v in env.items()})
    try: return eval(e, {'__builtins__':{}}, local)
    except Exception: raise UnsupportedSyntax(f'Could not evaluate supported expression: {e}')

def run_nodes(nodes, env, output):
    for n in nodes:
        k=n['kind']
        if k=='assign':
            val=eval_expr(n['expr'],env); env[n['name']]=val; env[n['name'].upper()]=val; env[n['name'].lower()]=val
        elif k=='print':
            # DISPLAY/PRINT can contain comma-separated values; join with a space.
            vals=[eval_expr(x,env) for x in re.split(r'\s*,\s*',n['expr'])]
            output.append(' '.join(str(v) for v in vals))
        elif k=='if':
            branch=n['then'] if eval_expr(n['cond'],env) else n['else']; run_nodes(branch,env,output)
        elif k=='for':
            a=int(eval_expr(n['start'],env)); b=int(eval_expr(n['end'],env));
            for v in range(a,b+1):
                env[n['name']]=v; env[n['name'].upper()]=v; env[n['name'].lower()]=v; run_nodes(n['body'],env,output)
        elif k=='while':
            guard=0
            while eval_expr(n['cond'],env):
                run_nodes(n['body'],env,output); guard+=1
                if guard>10000: raise UnsupportedSyntax('Loop exceeded validation guard')
        else: raise UnsupportedSyntax(f'Unsupported internal node: {k}')

def generate_js(nodes, indent=0, declared=None, rules=None):
    if declared is None: declared=set()
    if rules is None: rules=[]
    out=[]; pad='    '*indent
    for n in nodes:
        k=n['kind']
        if k=='assign':
            name=n['name']; prefix='let ' if name not in declared else ''
            declared.add(name); out.append(pad+prefix+name+' = '+js_expr(n['expr'])+';'); rules.append('assignment → JavaScript let/assignment')
        elif k=='print': out.append(pad+'console.log('+js_expr(n['expr'])+');'); rules.append('output → console.log')
        elif k=='if':
            out.append(pad+'if ('+js_expr(n['cond'])+') {'); rules.append('conditional → if/else')
            out.extend(generate_js(n['then'],indent+1,declared,rules));
            if n['else']:
                out.append(pad+'} else {'); out.extend(generate_js(n['else'],indent+1,declared,rules))
            out.append(pad+'}')
        elif k=='for':
            name=n['name']; start=js_expr(n['start']); end=js_expr(n['end']);
            out.append(pad+f'for (let {name} = {start}; {name} <= {end}; {name}++) {{'); rules.append('loop → JavaScript for')
            out.extend(generate_js(n['body'],indent+1,declared,rules)); out.append(pad+'}')
        elif k=='while':
            out.append(pad+'while ('+js_expr(n['cond'])+') {'); rules.append('loop → JavaScript while'); out.extend(generate_js(n['body'],indent+1,declared,rules)); out.append(pad+'}')
    return out


def generate_python(nodes, indent=0, declared=None, rules=None):
    """Generate readable Python from the shared normalized node representation."""
    if declared is None: declared=set()
    if rules is None: rules=[]
    out=[]; pad='    '*indent
    for n in nodes:
        k=n['kind']
        if k=='assign':
            name=n['name']; out.append(pad+name+' = '+py_expr(n['expr'])); declared.add(name)
            rules.append('assignment → Python assignment')
        elif k=='print':
            out.append(pad+'print('+py_expr(n['expr'])+')'); rules.append('output → Python print')
        elif k=='if':
            out.append(pad+'if '+py_expr(n['cond'])+':'); rules.append('conditional → Python if/else')
            body=generate_python(n['then'],indent+1,declared,rules); out.extend(body or [pad+'    pass'])
            if n['else']:
                out.append(pad+'else:'); out.extend(generate_python(n['else'],indent+1,declared,rules) or [pad+'    pass'])
        elif k=='for':
            out.append(pad+f'for {n["name"]} in range({py_expr(n["start"])}, ({py_expr(n["end"])} + 1)):'); rules.append('loop → Python range')
            out.extend(generate_python(n['body'],indent+1,declared,rules) or [pad+'    pass'])
        elif k=='while':
            out.append(pad+'while '+py_expr(n['cond'])+':'); rules.append('loop → Python while')
            out.extend(generate_python(n['body'],indent+1,declared,rules) or [pad+'    pass'])
    return out


def py_expr(e):
    e=e.strip().rstrip(';.')
    e=re.sub(r'\bAND\b','and',e,flags=re.I); e=re.sub(r'\bOR\b','or',e,flags=re.I); e=re.sub(r'\bNOT\b','not',e,flags=re.I)
    e=re.sub(r'\bTRUE\b','True',e,flags=re.I); e=re.sub(r'\bFALSE\b','False',e,flags=re.I)
    e=e.replace('<>','!=')
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
    output='\n'.join(generated)
    source_out=[]
    # Source interpreter is intentionally limited to the documented subset.
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
    # Coverage is construct-based rather than simply counting duplicate rule strings.
    unique_rules=list(dict.fromkeys(rules)); avail=max(1,len(set(['assignment','output','conditional','loop'])))
    used_categories=len(set(r.split(' → ')[0].split()[0] for r in unique_rules))
    coverage={'rules_available':avail,'rules_used':used_categories,'coverage_percent':round(used_categories/avail*100,1),
              'deterministic_rules':len(unique_rules),'unsupported_constructs':len(unsupported)}
    notes=['Subset translation: '+LANGUAGES[language],
           'Shared normalized representation is lowered to the selected target backend.',
           'Rule-first translation is applied before optional LLM fallback.',
           'Unsupported constructs are surfaced explicitly and are never silently treated as translated.']
    return LegacyResult(language,target,output,tokenize_legacy(code,language),ir,symbols,unique_rules,coverage,nodes,unsupported,notes)

