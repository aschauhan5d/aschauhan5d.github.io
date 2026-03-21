#!/usr/bin/env python3
"""
build.py — Run this after adding/editing blog posts or publications.
It embeds all blog posts from blogs/*.md into index.html.

Usage:
    python3 build.py
"""
import json, re, os

BLOGS_DIR  = 'blogs'
INDEX_JSON = 'blogs/index.json'
HTML_FILE  = 'index.html'

# ── LOAD POSTS ──
with open(INDEX_JSON) as f:
    files = json.load(f)

posts = []
for fname in files:
    path = os.path.join(BLOGS_DIR, fname)
    if not os.path.exists(path):
        print(f"  ⚠ Warning: {fname} listed in index.json but file not found")
        continue
    with open(path) as f:
        text = f.read()
    m = re.match(r'^---\n([\s\S]*?)\n---', text)
    if not m:
        print(f"  ⚠ Warning: {fname} has no frontmatter, skipping")
        continue
    obj = {'file': fname, 'body': text[m.end():].lstrip()}
    for line in m.group(1).split('\n'):
        lm = re.match(r'^(\w+):\s*"?([^"]+?)"?\s*$', line)
        if lm:
            obj[lm.group(1)] = lm.group(2)
    posts.append(obj)
    print(f"  ✓ Loaded: {obj.get('title','(no title)')} ({fname})")

# ── EMBED INTO HTML ──
with open(HTML_FILE) as f:
    html = f.read()

new_data = json.dumps([{
    'file':    p['file'],
    'title':   p.get('title',''),
    'date':    p.get('date',''),
    'excerpt': p.get('excerpt',''),
    'body':    p.get('body','').strip()
} for p in posts], ensure_ascii=False)

# Replace the BLOG_POSTS constant
html = re.sub(
    r'const BLOG_POSTS = \[[\s\S]*?\];',
    f'const BLOG_POSTS = {new_data};',
    html
)

with open(HTML_FILE, 'w') as f:
    f.write(html)

print(f"\n✓ Build complete — {len(posts)} post(s) embedded into {HTML_FILE}")
print("\nTo add a new post:")
print("  1. Create blogs/blogN.md with frontmatter (title, date, excerpt)")
print("  2. Add 'blogN.md' to blogs/index.json")
print("  3. Run: python3 build.py")
print("  4. Commit and push to GitHub")
