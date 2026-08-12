#!/usr/bin/env python3
"""
Turn bundle.html into artifact.html — a body-only fragment for hosting the
preview on claude.ai, which supplies its own <!doctype>, <head> and <body>.

Two things this has to get right:
  * the <title> must land inside the first 8 KB, and the bundle's own title
    sits behind ~44 KB of inlined CSS, so it is re-emitted at the top;
  * the host paints its own ground in the viewer's theme. This page commits
    to Hero's light brand world, so the ground is pinned rather than
    inherited, or a dark-mode viewer gets Hero's dark text on a dark ground.
"""

import io
import re

src = open("bundle.html", encoding="utf-8").read()

style = re.search(r"<style>.*?</style>", src, re.S).group(0)

body = src[src.index("<body>") + len("<body>") :]
body = re.sub(r"</body>\s*</html>\s*$", "", body).strip()

assert "id=root" in body or 'id="root"' in body, "mount point missing"
assert "<script" in body, "scripts missing"

out = io.StringIO()
out.write("<title>Hero Lead Path</title>\n")
out.write(style)
out.write(
    "\n<style>\n"
    "  html, body { background: #ffffff !important; color: #1d1d1f; }\n"
    "  #root { background: #ffffff; }\n"
    "</style>\n"
)
out.write(body)
out.write("\n")

text = out.getvalue()
open("artifact.html", "w", encoding="utf-8").write(text)

assert text.find("<title>") < 8192, "title pushed out of the first 8 KB"
print(f"wrote artifact.html ({len(text):,} bytes)")
