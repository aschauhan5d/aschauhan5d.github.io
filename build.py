#!/usr/bin/env python3
"""
build.py — regenerates the site from your source files.

  blogs/*.md        → blog/<slug>/index.html, the Writing list and News items
  publications.md   → Publications section (with automatic BibTeX)
  news.md           → News section
  photo.jpg         → profile photo (also .jpeg / .png / .webp, in the root or assets/)
  cv.pdf            → "CV" button
  sitemap.xml       → regenerated

A GitHub Action runs this automatically on every push. To preview locally:

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
# Name variants that are shown in bold in author lists
MY_NAMES = ["Abhishek Singh Chauhan", "A. S. Chauhan", "A.S. Chauhan", "Abhishek S. Chauhan", "Abhishek Chauhan"]

ROOT = Path(__file__).resolve().parent
BLOGS = ROOT / "blogs"
OUT = ROOT / "blog"
INDEX = ROOT / "index.html"

esc = html.escape
TODAY = date.today()


# ── helpers ──────────────────────────────────────────────────────────────
def parse_date(s):
    """Returns (date, precision) where precision is 'day', 'month' or 'year'."""
    s = (s or "").strip()
    for fmt, prec in (("%B %d, %Y", "day"), ("%b %d, %Y", "day"), ("%Y-%m-%d", "day"),
                      ("%d %B %Y", "day"), ("%B %Y", "month"), ("%b %Y", "month"),
                      ("%Y-%m", "month"), ("%Y", "year")):
        try:
            return datetime.strptime(s, fmt).date(), prec
        except ValueError:
            pass
    return None, None


def short_date(d, prec):
    if not d:
        return ""
    return str(d.year) if prec == "year" else d.strftime("%b %Y")


def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    return re.sub(r"[\s_-]+", "-", s) or "post"


def inline_md(text):
    """Escape text, then allow [links](url), **bold** and *italic*."""
    t = esc(text)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: f'<a href="{m.group(2)}"{" target=\"_blank\" rel=\"noopener\"" if m.group(2).startswith("http") else ""}>{m.group(1)}</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return t


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


def parse_entries(path):
    """Reads a simple YAML-like list ("- key: value" blocks, '#' lines ignored,
    'key: |' for multi-line values)."""
    if not path.exists():
        return []
    entries, cur, block_key, block_indent, block_lines = [], None, None, 0, []

    def close_block():
        nonlocal block_key, block_lines
        if block_key and cur is not None:
            cur[block_key] = "\n".join(block_lines).rstrip()
        block_key, block_lines = None, []

    for raw in path.read_text(encoding="utf-8").splitlines():
        if block_key:
            indent = len(raw) - len(raw.lstrip())
            if raw.strip() == "" or indent >= block_indent:
                block_lines.append(raw[block_indent:] if raw.strip() else "")
                continue
            close_block()
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = re.match(r'^(\s*)(-\s*)?(\w+):\s*(.*?)\s*$', raw)
        if not m:
            continue
        if m.group(2) is not None:
            cur = {}
            entries.append(cur)
        if cur is None:
            continue
        key, val = m.group(3), m.group(4)
        if val == "|":
            block_key, block_lines = key, []
            block_indent = len(m.group(1)) + (len(m.group(2)) if m.group(2) else 0) + 2
            continue
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        cur[key] = val
    close_block()
    return entries


def replace_block(doc, name, content):
    pattern = re.compile(rf"(<!-- {name}:START -->)[\s\S]*?(<!-- {name}:END -->)")
    if not pattern.search(doc):
        raise SystemExit(f"✗ index.html is missing the <!-- {name}:START/END --> markers")
    return pattern.sub(lambda m: f"{m.group(1)}{content}{m.group(2)}", doc)


def find_file(*names):
    for n in names:
        for folder in (ROOT, ROOT / "assets"):
            p = folder / n
            if p.exists():
                return p.relative_to(ROOT).as_posix()
    return None


# ── posts ────────────────────────────────────────────────────────────────
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
    d, _ = parse_date(meta.get("date", ""))
    if not d:
        print(f"  ⚠ {path.name}: couldn't read date {meta.get('date')!r} — use e.g. \"March 22, 2026\"")
    words = len(re.findall(r"\w+", re.sub(r"```[\s\S]*?```", "", body)))
    posts.append({
        "title": meta.get("title", path.stem),
        "excerpt": meta.get("excerpt", ""),
        "date": d,
        "date_label": d.strftime("%B %-d, %Y") if d else meta.get("date", ""),
        "slug": slugify(meta.get("slug") or meta.get("title") or path.stem),
        "minutes": max(1, math.ceil(words / 220)),
        "body": body.strip(),
    })
    print(f"  ✓ post: {meta.get('title', path.stem)}")
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
  <meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)" />
  <meta name="theme-color" content="#121416" media="(prefers-color-scheme: dark)" />
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
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;450;500;600&family=JetBrains+Mono:wght@400&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../../assets/style.css" />
  <script type="application/ld+json">{jsonld}</script>
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <nav class="nav" aria-label="Site">
    <div class="nav-inner">
      <a class="nav-name" href="../../">{author}</a>
      <div class="nav-links">
        <a href="../../#about">About</a>
        <a href="../../#news">News</a>
        <a href="../../#publications">Publications</a>
        <a href="../../#research">Research</a>
        <a href="../../#writing" class="on">Writing</a>
      </div>
    </div>
  </nav>
  <main class="wrap post-wrap" id="main">
    <a class="back" href="../../#writing">← All writing</a>
    <article>
      <header class="post-header">
        <h1>{title}</h1>
        <p class="post-meta">{author} · <time datetime="{iso}">{date_label}</time> · {minutes} min read</p>
      </header>
      <div class="post-body" id="post-body">
        <noscript><pre style="white-space:pre-wrap">{body_escaped}</pre></noscript>
      </div>
    </article>
    <nav class="post-nav" aria-label="More posts">{neighbours}</nav>
    <footer class="footer">
      <span>© {year} {author}</span>
      <a href="../../">aschauhan5d.github.io</a>
    </footer>
  </main>

  <script id="post-md" type="application/json">{body_json}</script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
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
    nb = ""
    if older:
        nb += f'<a href="../{older["slug"]}/"><small>← Previous</small>{esc(older["title"])}</a>'
    if newer:
        nb += f'<a class="next" href="../{newer["slug"]}/"><small>Next →</small>{esc(newer["title"])}</a>'
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": p["title"], "description": p["excerpt"], "datePublished": iso,
        "url": url, "author": {"@type": "Person", "name": AUTHOR, "url": SITE + "/"},
    }, ensure_ascii=False).replace("</", "<\\/")
    page = POST_TEMPLATE.format(
        title=esc(p["title"]), excerpt=esc(p["excerpt"]), author=AUTHOR, url=url, iso=iso,
        date_label=esc(p["date_label"]), minutes=p["minutes"], year=TODAY.year,
        jsonld=jsonld, neighbours=nb, body_escaped=esc(p["body"]),
        body_json=json.dumps(p["body"], ensure_ascii=False).replace("</", "<\\/"),
    )
    dest = OUT / p["slug"] / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page, encoding="utf-8")


# ── publications ─────────────────────────────────────────────────────────
pubs = [p for p in parse_entries(ROOT / "publications.md") if p.get("title")]
pubs.sort(key=lambda p: str(p.get("year", "")), reverse=True)


def bold_me(authors):
    t = esc(authors)
    for n in sorted(MY_NAMES, key=len, reverse=True):
        t = re.sub(rf"(?<![\w>]){re.escape(esc(n))}(?![\w<])", f'<span class="me">{esc(n)}</span>', t)
        if 'class="me"' in t:
            break
    return t


def make_bibtex(p):
    kind = {"journal": "article", "preprint": "misc"}.get(p.get("type", "").lower(), "inproceedings")
    authors = [a.strip() for a in p.get("authors", AUTHOR).split(",") if a.strip()]
    first_last = re.sub(r"\W", "", authors[0].split()[-1].lower()) if authors else "author"
    first_word = next((w for w in re.findall(r"[a-z0-9]+", p["title"].lower())
                       if w not in {"a", "an", "the", "on", "of", "for", "in", "to", "with", "and"}), "paper")
    key = f"{first_last}{p.get('year', '')}{first_word}"
    venue_field = {"article": "journal", "misc": "howpublished"}.get(kind, "booktitle")
    fields = [("title", "{" + p["title"] + "}"), ("author", " and ".join(authors))]
    if p.get("venue"):
        fields.append((venue_field, p["venue"]))
    if p.get("year"):
        fields.append(("year", str(p["year"])))
    if p.get("doi"):
        fields.append(("doi", re.sub(r"^https?://(dx\.)?doi\.org/", "", p["doi"])))
    if p.get("arxiv") and kind == "misc":
        fields.append(("eprint", p["arxiv"].rstrip("/").split("/")[-1]))
    body = ",\n".join(f"  {k:<9}= {{{v}}}" for k, v in fields)
    return f"@{kind}{{{key},\n{body}\n}}"


def pub_html(p):
    link = p.get("pdf") or p.get("arxiv") or p.get("doi") or p.get("project")
    title = (f'<a class="pub-title" href="{esc(link)}" target="_blank" rel="noopener">{esc(p["title"])}</a>'
             if link else f'<span class="pub-title">{esc(p["title"])}</span>')
    award = f'<span class="badge">{esc(p["award"])}</span>' if p.get("award") else ""
    venue = f'<em>{esc(p.get("venue", ""))}</em>' if p.get("venue") else ""
    if p.get("year"):
        venue = f"{venue}, {esc(str(p['year']))}" if venue else esc(str(p["year"]))
    links = "".join(
        f'<a href="{esc(p[k])}" target="_blank" rel="noopener">{label}</a>'
        for k, label in (("pdf", "PDF"), ("arxiv", "arXiv"), ("code", "Code"),
                         ("project", "Project page"), ("doi", "DOI"))
        if p.get(k) and p[k] != "#"
    )
    bib = esc(p.get("bibtex") or make_bibtex(p))
    links += f'<details><summary>BibTeX</summary><pre class="bibtex">{bib}</pre></details>'
    thumb = (f'<img class="pub-thumb" src="{esc(p["image"])}" alt="" loading="lazy" />'
             if p.get("image") else "")
    classes = "pub" + ("" if thumb else " no-thumb") + (" highlight" if p.get("highlight", "").lower() == "true" else "")
    return f"""
      <article class="{classes}">
        {thumb}
        <div>
          {title}{award}
          <div class="pub-authors">{bold_me(p.get("authors", ""))}</div>
          <div class="pub-venue">{venue}</div>
          {f'<p class="pub-tldr">{inline_md(p["tldr"])}</p>' if p.get("tldr") else ""}
          <div class="pub-links">{links}</div>
        </div>
      </article>"""


if pubs:
    pubs_html = ('\n      <p class="pub-note"><span class="me" style="font-weight:600">Bold</span> marks my name.</p>'
                 + "".join(pub_html(p) for p in pubs))
else:
    pubs_html = """
      <div class="empty-card">Manuscripts on parameter-efficient fine-tuning of Vision Transformers for
        3D medical image segmentation are in preparation. Papers will appear here as they are published —
        see also my <a href="https://orcid.org/0009-0005-3507-6499" target="_blank" rel="noopener">ORCID</a> record.</div>"""


# ── news (news.md + blog posts) ──────────────────────────────────────────
news = []
for n in parse_entries(ROOT / "news.md"):
    if not n.get("text"):
        continue
    d, prec = parse_date(n.get("date", ""))
    news.append((d or date.min, short_date(d, prec) or esc(n.get("date", "")), inline_md(n["text"])))
for p in posts:
    if p["date"]:
        news.append((p["date"], short_date(p["date"], "day"),
                     f'New blog post: <a href="blog/{p["slug"]}/">{esc(p["title"])}</a>'))
news.sort(key=lambda x: x[0], reverse=True)
news = news[:10]  # keep the list short; oldest items drop off
news_html = "".join(f'\n        <li><time>{label}</time><span>{text}</span></li>' for _, label, text in news) \
    or '\n        <li><time></time><span>No news yet.</span></li>'


# ── writing list ─────────────────────────────────────────────────────────
posts_html = "".join(f"""
        <li>
          <a class="post-link" href="blog/{p['slug']}/">{esc(p['title'])}</a>
          <div class="post-meta"><time datetime="{p['date'].isoformat() if p['date'] else ''}">{esc(p['date_label'])}</time> · {p['minutes']} min read</div>
          <p class="post-excerpt">{esc(p['excerpt'])}</p>
        </li>""" for p in posts) or "\n        <li>No posts yet.</li>"


# ── photo, CV, updated ───────────────────────────────────────────────────
photo = find_file("photo.jpg", "photo.jpeg", "photo.png", "photo.webp", "profile.jpg", "profile.png")
if photo:
    photo_html = f'<img class="photo" src="{photo}" alt="Photo of {AUTHOR}" width="200" height="200" />'
    og_html = f'<meta property="og:image" content="{SITE}/{photo}" />'
else:
    photo_html = '<div class="photo photo-initials" aria-hidden="true">AC</div>'
    og_html = ""

cv = find_file("cv.pdf", "CV.pdf")
cv_html = (f'<a href="{cv}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
           'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 '
           '2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/></svg>CV</a>') if cv else ""

doc = INDEX.read_text(encoding="utf-8")
doc = replace_block(doc, "PHOTO", photo_html)
doc = replace_block(doc, "OG_IMAGE", og_html)
doc = replace_block(doc, "CV", cv_html)
doc = replace_block(doc, "NEWS", news_html + "\n        ")
doc = replace_block(doc, "PUBLICATIONS", pubs_html + "\n      ")
doc = replace_block(doc, "POSTS", posts_html + "\n        ")
doc = replace_block(doc, "UPDATED", f"Last updated {TODAY.strftime('%B %Y')}")
INDEX.write_text(doc, encoding="utf-8")


# ── sitemap ──────────────────────────────────────────────────────────────
urls = [(f"{SITE}/", TODAY)] + [(f"{SITE}/blog/{p['slug']}/", p["date"]) for p in posts]
(ROOT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{u}</loc>{f'<lastmod>{d.isoformat()}</lastmod>' if d else ''}</url>\n" for u, d in urls)
    + "</urlset>\n",
    encoding="utf-8",
)

print(f"\n✓ Built {len(posts)} post(s), {len(pubs)} publication(s), {len(news)} news item(s)"
      f" · photo: {photo or 'none (add photo.jpg)'} · CV: {cv or 'none (add cv.pdf)'}")
