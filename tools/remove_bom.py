"""Remove UTF-8 BOM from files under .github/workflows if present."""

import pathlib

p = pathlib.Path(".github/workflows")
modified = []
for f in sorted(p.glob("**/*.y*ml")):
    b = f.read_bytes()
    if b.startswith(b"\xef\xbb\xbf"):
        new = b[3:]
        f.write_bytes(new)
        modified.append(str(f))
print("removed BOM from", len(modified), "files")
for m in modified:
    print(m)
