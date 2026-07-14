"""
Resolves every `local N` symbol in a SCIP index back to the actual
variable name by reading the source text at the occurrence's range position.
"""
import sys
sys.path.insert(0, '.')
import scip_pb2

SCIP_FILE = 'index.scip'

index = scip_pb2.Index()
with open(SCIP_FILE, 'rb') as f:
    index.ParseFromString(f.read())

for doc in index.documents:
    # Load source lines for this file
    try:
        with open(doc.relative_path, encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f'[SKIP] {doc.relative_path} not found')
        continue

    # Find all Definition occurrences for local symbols
    local_defs = {}
    for occ in doc.occurrences:
        if occ.symbol.startswith('local ') and occ.symbol_roles == 1:
            r = occ.range
            line_text = lines[r[0]].rstrip()
            name = line_text[r[1]:r[2]]          # slice [col_start : col_end]
            local_defs[occ.symbol] = {
                'line':      r[0] + 1,            # 1-based for display
                'col_start': r[1],
                'col_end':   r[2],
                'name':      name,
                'context':   line_text.strip(),
            }

    if not local_defs:
        continue

    print(f'=== {doc.relative_path} ===')
    for sym, info in sorted(local_defs.items(), key=lambda x: int(x[0].split()[1])):
        print(f"  {sym:10s}  L{info['line']:3d}  {info['name']!r:25s}  →  {info['context']}")
    print()
