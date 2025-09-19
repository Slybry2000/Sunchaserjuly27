"""Normalize line endings and remove stray CR characters from workflow files.
Writes changes in-place and prints files modified.
"""

import pathlib

p = pathlib.Path(".github/workflows")
files = sorted(p.glob("**/*.y*ml"))
modified = []
for f in files:
    s = f.read_text(encoding="utf-8")
    s2 = s.replace("\r\n", "\n").replace("\r", "\n")
    if s2 != s:
        f.write_text(s2, encoding="utf-8")
        modified.append(str(f))
print("normalized", len(modified), "files")
for m in modified:
    print(m)
