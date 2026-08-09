#!/usr/bin/env python3
"""Regenerate Hugo content files from the old Django blog's SQLite export
(old-blog/data.dat). Reads the raw `content` field (not `content_highlighted`,
which is pre-rendered Pygments HTML) and writes one Hugo content file per
article under content/ or content/posts/.

Usage: python3 migrate.py
"""
import html
import re
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parent
DB = REPO / "old-blog" / "data.dat"
CONTENT_DIR = REPO / "content"

CODE_RE = re.compile(r'<code(?:\s+class="([a-zA-Z0-9_+-]+)")?\s*>\n?(.*?)</code>', re.DOTALL)


def toml_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def rewrite_links(text):
    text = text.replace("http://ilian.i-n-i.org/wp-content/uploads/", "/wp-content/uploads/")
    text = re.sub(r'href="http://ilian\.i-n-i\.org"', 'href="/"', text)
    text = re.sub(r'href="http://ilian\.i-n-i\.org/', 'href="/', text)
    text = text.replace("http://www.ilian.io/", "/")
    text = text.replace("http://1.gravatar.com/", "https://www.gravatar.com/")
    text = text.replace("http%3A%2F%2F1.gravatar.com%2F", "https%3A%2F%2Fwww.gravatar.com%2F")
    return text


def convert_code_blocks(text):
    def repl(m):
        lang = m.group(1) or "python"
        code = html.unescape(m.group(2)).strip("\n")
        code = html.escape(code, quote=True)
        return f'</p><pre><code class="language-{lang}">{code}</code></pre><p>'

    text = CODE_RE.sub(repl, text)
    # drop paragraphs left empty by the </p><pre>...</pre><p> substitution above
    text = re.sub(r"<p>\s*</p>", "", text)
    return text


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    articles = conn.execute(
        "SELECT id, title, slug, date_published, content, is_page "
        "FROM static_blog_article WHERE status = 1 ORDER BY id"
    ).fetchall()

    for a in articles:
        tags = [
            r[0]
            for r in conn.execute(
                "SELECT t.name FROM static_blog_article_tags at "
                "JOIN static_blog_tag t ON t.id = at.tag_id "
                "WHERE at.article_id = ? ORDER BY t.name",
                (a["id"],),
            ).fetchall()
        ]

        body = rewrite_links(a["content"])
        body = convert_code_blocks(body)

        date = a["date_published"].replace(" ", "T") + "Z"
        tags_toml = ", ".join(f'"{toml_escape(t)}"' for t in tags)

        lines = [
            "+++",
            f'title = "{toml_escape(a["title"])}"',
            f'date = "{date}"',
            f'slug = "{a["slug"]}"',
            f"tags = [{tags_toml}]",
            "draft = false",
        ]
        if a["is_page"]:
            lines.append(f'url = "/{a["slug"]}/"')
        lines.append("+++")

        out = "\n".join(lines) + "\n" + body.strip() + "\n"

        if a["is_page"]:
            dest = CONTENT_DIR / f'{a["slug"]}.html'
        else:
            dest = CONTENT_DIR / "posts" / f'{a["slug"]}.html'

        dest.write_text(out)
        print(f"wrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
