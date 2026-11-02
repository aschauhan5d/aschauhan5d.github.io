# How to add a blog post

1. Create a new `.md` file in this `blogs/` folder (any name, e.g. `lora-results.md`).

2. Start it with frontmatter, then write normal Markdown:

````markdown
---
title: "Your Post Title"
date: "March 22, 2026"
excerpt: "A short summary shown on the homepage and in link previews."
---

Your post content goes here.

## A Heading

Paragraphs, **bold**, *italic*, [links](https://example.com), lists,
> quotes, tables and images all work.

```python
# Code blocks get syntax highlighting and a Copy button
print("hello world")
```
````

3. Commit and push. That's it.

A GitHub Action runs `build.py` on every push, which creates the post's own page
at `https://aschauhan5d.github.io/blog/<your-title-as-slug>/`, adds it to the
homepage (newest first) and updates `sitemap.xml`. Give it a minute or two after
pushing.

## Optional frontmatter

| Field   | What it does |
|---------|--------------|
| `slug: "my-post"` | Fixes the URL. Without it, the URL comes from the title, so renaming a post changes its link. |
| `draft: true`     | Keeps the post off the site until you remove this line. |

## Publications

Edit `publications.md` in the repo root the same way — uncomment an entry and fill it in.

## CV

Put a file called `cv.pdf` in the repo root and the "CV ↓" link appears automatically.

## Preview on your computer

```
python3 build.py
python3 -m http.server
```

Then open http://localhost:8000.
