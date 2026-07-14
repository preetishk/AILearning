import sys, os, re, json
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import scip_pb2

SCIP_FILE = os.path.join(_HERE, 'index.scip')
SRC_ROOT  = _HERE
OUT       = os.path.join(_HERE, 'index.scip.json')

index = scip_pb2.Index()
with open(SCIP_FILE, 'rb') as f:
    index.ParseFromString(f.read())

ROLE_NAMES = {
    0:'unspecified', 1:'definition', 2:'import',
    4:'write',       8:'read',      16:'generated',
    32:'test',      64:'forward_def'
}

def short_symbol(sym):
    m = re.match(r'^scip-python\s+\S+\s+\S+\s+\S+\s+(.*)', sym)
    return m.group(1).strip() if m else sym

def build_local_map(doc):
    try:
        with open(os.path.join(SRC_ROOT, doc.relative_path), encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return {}
    mapping = {}
    for occ in doc.occurrences:
        if occ.symbol.startswith('local ') and occ.symbol_roles == 1:
            r = occ.range
            name = lines[r[0]][r[1]:r[2]].strip()
            if name:
                mapping[occ.symbol] = name
    return mapping

def resolve(sym, local_map):
    if sym.startswith('local '):
        return local_map.get(sym, sym)
    return short_symbol(sym)

output = []
for doc in index.documents:
    lmap = build_local_map(doc)
    try:
        with open(os.path.join(SRC_ROOT, doc.relative_path), encoding='utf-8') as f:
            src_lines = f.readlines()
    except FileNotFoundError:
        src_lines = []
    file_entry = {'file': doc.relative_path, 'definitions': [], 'call_sites': []}
    for occ in doc.occurrences:
        r    = occ.range
        role = ROLE_NAMES.get(occ.symbol_roles, str(occ.symbol_roles))
        name = resolve(occ.symbol, lmap)
        src  = src_lines[r[0]].strip() if r[0] < len(src_lines) else ''
        entry = {'line': r[0]+1, 'symbol': name, 'role': role, 'source': src}
        if occ.symbol_roles == 1:
            file_entry['definitions'].append(entry)
        elif occ.symbol_roles in (8, 4) and not occ.symbol.startswith('local '):
            file_entry['call_sites'].append(entry)
    output.append(file_entry)

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2)

print(f'Written {OUT}')
print()
print('Sample (ast_names.py definitions):')
print(json.dumps(output[0]['definitions'][:6], indent=2))
print()
print('Sample (ast_names.py call sites):')
print(json.dumps(output[0]['call_sites'][:4], indent=2))
