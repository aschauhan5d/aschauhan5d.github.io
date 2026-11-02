#!/usr/bin/env python3
"""
build.py — regenerates the site from your Markdown files.

  • every blogs/*.md post (except README.md) → its own page at blog/<slug>/
  • the blog list and publications list on index.html
  • the CV link (shown only if cv.pdf exists in the repo root)
  • sitemap.xml

You normally don't need to run this yourself: a GitHub Action runs it
automatically whenever you push. To preview locally:

    python3 build.py
    python3 -m http.server     # then open http://localhost:8000

Standard library only — nothing to install.
"""
import html
import json
import math
import re
import shutil
from datetime import date, datetime
from pathlib import Path

SITE = "https://aschauhan5d.github.io"
AUTHOR = "Abhishek Singh Chauhan"
ROOT = Path(__file__).resolve().parent
BLOGS = ROOT / "blogs"
OUT = ROOT / "blog"
INDEX = ROOT / "index.html"
PUBS = ROOT / "publications.md"
DATE_FORMATS = ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%d %B %Y")

esc = html.escape


# ── helpers ──────────────────────────────────────────────────────────────
def parse_date(s):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            pass
    return None


def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    return re.sub(r"[\s_-]+", "-", s) or "post"


def parse_frontmatter(text):
    m = re.match(r"^---\s*\n([\s\S]*?)\n---\s*\n?", text)
    if not m:
        return None, text
    meta = {}
    for line in m.group(1).splitlines():
        lm = re.match(r'^(\w+):\s*"?(.*?)"?\s*$', line)
        if lm:
            meta[lm.group(1)] = lm.group(2)
    return meta, text[m.end():].lstrip()


def replace_block(doc, name, content):
    pattern = re.compile(rf"(<!-- {name}:START -->)[\s\S]*?(<!-- {name}:END -->)")
    if not pattern.search(doc):
        raise SystemExit(f"✗ index.html is missing the <!-- {name}:START/END --> markers")
    return pattern.sub(lambda m: f"{m.group(1)}{content}{m.group(2)}", doc)


# ── load posts ───────────────────────────────────────────────────────────
posts = []
for path in sorted(BLOGS.glob("*.md")):
    if path.name.lower() == "readme.md":
        continue
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    if meta is None:
        print(f"  ⚠ {path.name}: no frontmatter (--- title/date/excerpt ---), skipped")
        continue
    if meta.get("draft", "").lower() in ("true", "yes"):
        print(f"  · {path.name}: draft, skipped")
        continue
    d = parse_date(meta.get("date", ""))
    if not d:
        print(f"  ⚠ {path.name}: couldn't read date {meta.get('date')!r} — use e.g. \"March 22, 2026\"")
    words = len(re.findall(r"\w+", re.sub(r"```[\s\S]*?```", "", body)))
    posts.append({
        "file": path.name,
        "title": meta.get("title", path.stem),
        "excerpt": meta.get("excerpt", ""),
        "date": d,
        "date_label": d.strftime("%B %-d, %Y") if d else meta.get("date", ""),
        "slug": slugify(meta.get("slug") or meta.get("title") or path.stem),
        "minutes": max(1, math.ceil(words / 220)),
        "body": body.strip(),
    })
    print(f"  ✓ {meta.get('title', path.stem)}  ({path.name})")

posts.sort(key=lambda p: p["date"] or date.min, reverse=True)


# ── post pages ───────────────────────────────────────────────────────────
POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — {author}</title>
  <meta name="description" content="{excerpt}" />
  <meta name="author" content="{author}" />
  <link rel="canonical" href="{url}" />
  <meta name="theme-color" content="#fafaf7" media="(prefers-color-scheme: light)" />
  <meta name="theme-color" content="#141614" media="(prefers-color-scheme: dark)" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="{author}" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{excerpt}" />
  <meta property="og:url" content="{url}" />
  <meta property="article:published_time" content="{iso}" />
  <meta name="twitter:card" content="summary" />
  <link rel="icon" href="../../assets/favicon.svg" type="image/svg+xml" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;1,300&family=IBM+Plex+Mono:wght@400&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../../assets/style.css" />
  <script type="application/ld+json">{jsonld}</script>
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <nav class="nav" aria-label="Site">
    <a class="nav-name" href="../../">{author}</a>
    <div class="nav-links">
      <a href="../../#about">About</a>
      <a href="../../#research">Research</a>
      <a href="../../#publications">Publications</a>
      <a href="../../#blog" class="on">Blog</a>
    </div>
  </nav>
  <main class="wrap" id="main">
    <a class="post-back" href="../../#blog">← All posts</a>
    <article>
      <header class="post-header">
        <h1>{title}</h1>
        <p class="item-meta"><time datetime="{iso}">{date_label}</time> · {minutes} min read</p>
      </header>
      <div class="post-body" id="post-body">
        <noscript><pre style="white-space:pre-wrap">{body_escaped}</pre></noscript>
      </div>
    </article>
    <hr />
    <nav class="item" aria-label="More posts" style="border:none;padding-top:0">{neighbours}</nav>
    <footer class="footer">
      <span>© {year} {author}</span>
      <a href="../../">aschauhan5d.github.io</a>
    </footer>
  </main>

  <script id="post-md" type="application/json">{body_json}</script>
  <script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
  <script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"></script>
  <script>
    const md = JSON.parse(document.getElementById('post-md').textContent);
    const el = document.getElementById('post-body');
    el.innerHTML = marked.parse(md);
    el.querySelectorAll('a[href^="http"]').forEach(a => {{ a.target = '_blank'; a.rel = 'noopener'; }});
    el.querySelectorAll('pre code').forEach(code => {{
      if (window.hljs) hljs.highlightElement(code);
      const btn = document.createElement('button');
      btn.className = 'copy-btn'; btn.type = 'button'; btn.textContent = 'Copy';
      btn.onclick = () => navigator.clipboard.writeText(code.innerText).then(() => {{
        btn.textContent = 'Copied'; setTimeout(() => btn.textContent = 'Copy', 1500);
      }});
      code.parentElement.appendChild(btn);
    }});
  </script>
</body>
</html>
"""

if OUT.exists():
    shutil.rmtree(OUT)

for i, p in enumerate(posts):
    url = f"{SITE}/blog/{p['slug']}/"
    iso = p["date"].isoformat() if p["date"] else ""
    newer = posts[i - 1] if i > 0 else None
    older = posts[i + 1] if i + 1 < len(posts) else None
    nb = []
    if older:
        nb.append(f'<div class="item-meta">Previous</div><a class="item-title" href="../{older["slug"]}/">{esc(older["title"])}</a>')
    if newer:
        nb.append(f'<div class="item-meta" style="margin-top:.8rem">Next</div><a class="item-title" href="../{newer["slug"]}/">{esc(newer["title"])}</a>')
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": p["title"], "description": p["excerpt"], "datePublished": iso,
        "url": url, "author": {"@type": "Person", "name": AUTHOR, "url": SITE + "/"},
    }, ensure_ascii=False).replace("</", "<\\/")
    page = POST_TEMPLATE.format(
        title=esc(p["title"]), excerpt=esc(p["excerpt"]), author=AUTHOR, url=url, iso=iso,
        date_label=esc(p["date_label"]), minutes=p["minutes"], year=date.today().year,
        jsonld=jsonld, neighbours="".join(nb), body_escaped=esc(p["body"]),
        body_json=json.dumps(p["body"], ensure_ascii=False).replace("</", "<\\/"),
    )
    dest = OUT / p["slug"] / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page, encoding="utf-8")


# ── publications ─────────────────────────────────────────────────────────
pubs = []
if PUBS.exists():
    cur = None
    for line in PUBS.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r'^\s*(-\s*)?(\w+):\s*"?(.*?)"?\s*$', line)
        if not m:
            continue
        if m.group(1) is not None:  # "- key:" starts a new entry
            cur = {}
            pubs.append(cur)
        if cur is not None:
            cur[m.group(2)] = m.group(3)
    pubs = [p for p in pubs if p.get("title")]
    pubs.sort(key=lambda p: str(p.get("year", "")), reverse=True)


def pub_html(p):
    acts = "".join(
        f'<a href="{esc(p[k])}" target="_blank" rel="noopener">{label} ↗</a>'
        for k, label in (("pdf", "PDF"), ("doi", "DOI"), ("code", "Code"), ("arxiv", "arXiv"))
        if p.get(k) and p[k] != "#"
    )
    return f"""
        <div class="item">
          <div class="item-meta">{esc(p.get("year", ""))}</div>
          <div class="item-title">{esc(p["title"])}</div>
          <div class="item-sub">{esc(p.get("authors", ""))}</div>
          <div class="item-venue">{esc(p.get("venue", ""))}</div>
          <div class="actions">{acts}</div>
        </div>"""


pubs_html = "".join(pub_html(p) for p in pubs) or \
    '\n        <p class="empty">Papers in progress — check back soon.</p>'

posts_html = "".join(f"""
        <article class="item">
          <div class="item-meta"><time datetime="{p['date'].isoformat() if p['date'] else ''}">{esc(p['date_label'])}</time> · {p['minutes']} min read</div>
          <a class="item-title" href="blog/{p['slug']}/">{esc(p['title'])}</a>
          <p class="item-sub">{esc(p['excerpt'])}</p>
        </article>""" for p in posts) or '\n        <p class="empty">No posts yet.</p>'

cv_html = '<a href="cv.pdf">CV ↓</a>' if (ROOT / "cv.pdf").exists() else ""

doc = INDEX.read_text(encoding="utf-8")
doc = replace_block(doc, "POSTS", posts_html + "\n        ")
doc = replace_block(doc, "PUBLICATIONS", pubs_html + "\n        ")
doc = replace_block(doc, "CV", cv_html)
INDEX.write_text(doc, encoding="utf-8")


# ── sitemap ──────────────────────────────────────────────────────────────
latest = max((p["date"] for p in posts if p["date"]), default=date.today())
urls = [(f"{SITE}/", latest)] + [(f"{SITE}/blog/{p['slug']}/", p["date"]) for p in posts]
(ROOT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{u}</loc>{f'<lastmod>{d.isoformat()}</lastmod>' if d else ''}</url>\n" for u, d in urls)
    + "</urlset>\n",
    encoding="utf-8",
)

print(f"\n✓ Built {len(posts)} post page(s), {len(pubs)} publication(s), sitemap.xml"
      f"{'' if cv_html else '  (no cv.pdf found — CV link hidden)'}")
