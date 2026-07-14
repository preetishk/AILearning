"""
Demonstrates how tree-sitter resolves identifier names from [row, col] coordinates.
The parse output only shows positions -- this script shows how to get actual text.

Key insight: every Node has a .text property that returns its source text directly.
Graphify tools work the same way: they keep the parsed tree in memory and read
node.text (or slice source_bytes[node.start_byte:node.end_byte]) to get names.
"""
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

source_path = "src/rayExample.py"
with open(source_path, "rb") as f:
    source_bytes = f.read()

tree = parser.parse(source_bytes)

# ── How [row, col] maps to text ──────────────────────────────────────────────
# The CLI parse output shows:  (identifier [0, 7] - [0, 11])
# That means: row=0, col 7 to col 11 in the source
# Method 1: node.text  (direct -- tree-sitter 0.22+)
# Method 2: source_bytes[node.start_byte : node.end_byte].decode()
lines = source_bytes.decode("utf-8").splitlines()
print("How [row, col] resolves to text:")
print(f"  Source line 0 : {lines[0]!r}")
print(f"  [0, 7]-[0, 11]: {lines[0][7:11]!r}  (== 'time')")
print()

# ── Walk the AST -- node.text gives the name directly ───────────────────────
print("All identifiers with their actual text (node.text):")
print("-" * 50)

def walk(node, depth=0):
    if node.type == "identifier":
        start = node.start_point   # (row, col)
        end   = node.end_point
        text  = node.text.decode("utf-8")   # <-- this is how graphify tools get the name
        print(f"  {'  ' * depth}[{start[0]}, {start[1]}]-[{end[0]}, {end[1]}]  {text!r}")
    for child in node.children:
        walk(child, depth + 1)

walk(tree.root_node)
print()

# ── Extract function names by walking the tree ───────────────────────────────
print("Function definitions found:")
print("-" * 50)

def find_functions(node):
    if node.type == "function_definition":
        name_node = node.child_by_field_name("name")
        if name_node:
            line = name_node.start_point[0] + 1
            name = name_node.text.decode("utf-8")
            print(f"  line {line:3d}: def {name}(...)")
    for child in node.children:
        find_functions(child)

find_functions(tree.root_node)
