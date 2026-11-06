"""
Generate the homepage's "Latest Posts" and "Browse by Category" blocks at
build time, so neither has to be maintained by hand.

Two placeholders in docs/index.md are replaced:

    <!-- nf:recent-posts -->   -> cards for the N most recent posts
    <!-- nf:categories -->     -> one chip per category that actually has
                                  posts, with a count, linking to its page

Post data comes from the Material blog plugin itself (post.url, post.title,
post.categories[].url), so the URLs always match whatever the plugin
generates — no duplicated slug or date-format logic here.

If anything goes wrong the placeholder is replaced with a plain link to the
blog instead of raising, because a broken homepage is a worse failure than a
missing section. Nothing else on the page is touched.
"""

from __future__ import annotations

import logging
import pathlib
import re

log = logging.getLogger("mkdocs.hooks.blog_index")

RECENT_LIMIT = 6
RECENT_MARKER = "<!-- nf:recent-posts -->"
CATEGORY_MARKER = "<!-- nf:categories -->"

FALLBACK = '<p class="nf-empty"><a href="blog/">Browse the blog &rarr;</a></p>'


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _cat_name(cat) -> str:
    """Display name of a category view.

    `Category.title` is still None while the homepage renders — the blog
    plugin only fills it in when the category's own page is built, which
    happens later. `Category.name` carries the string from the start, so
    prefer it and keep the others as fallbacks.
    """
    for attr in ("name", "title"):
        value = getattr(cat, attr, None)
        if isinstance(value, str) and value.strip():
            return value.strip()

    slug = (getattr(cat, "url", "") or "").rstrip("/").rsplit("/", 1)[-1]
    return slug.replace("-", " ").title() if slug else "Uncategorised"


def _excerpt(post) -> str:
    """First real paragraph of the post, before the <!-- more --> marker."""
    md = post.markdown or ""
    md = md.split("<!-- more -->")[0]

    for block in md.split("\n\n"):
        block = block.strip()
        if not block or block.startswith("#"):
            continue
        # Drop surrounding emphasis and collapse newlines
        block = re.sub(r"^\*+|\*+$", "", block.strip())
        block = re.sub(r"\s+", " ", block).strip()
        if block:
            return block
    return ""


def _date(post):
    raw = (post.config or {}).get("date")
    if isinstance(raw, dict):
        raw = raw.get("created")
    try:
        # Cross-platform: %-d / %#d differ, so strip the zero by hand
        return f"{raw.strftime('%B')} {raw.day}, {raw.year}"
    except Exception:
        return ""


def _sort_key(post):
    raw = (post.config or {}).get("date")
    if isinstance(raw, dict):
        raw = raw.get("created")
    return raw


def _posts(config):
    plugin = config.plugins.get("material/blog")
    posts = list(getattr(getattr(plugin, "blog", None), "posts", []) or [])
    # The plugin already sorts newest-first, but do not rely on it.
    try:
        posts.sort(key=_sort_key, reverse=True)
    except Exception:
        pass
    return posts


def _render_posts(posts) -> str:
    if not posts:
        return FALLBACK

    out = ['<div class="nf-post-grid">']
    for post in posts[:RECENT_LIMIT]:
        meta = []
        date = _date(post)
        if date:
            meta.append(f'<span class="nf-post-card__date">{_esc(date)}</span>')
        readtime = (post.config or {}).get("readtime")
        if readtime:
            meta.append(
                f'<span class="nf-post-card__read">{int(readtime)} min read</span>'
            )

        # Categories are spans, not links: the whole card is already an <a>,
        # and nesting anchors is invalid HTML. Category links live in the
        # "Browse by Category" block below.
        cats = "".join(
            f'<span class="nf-post-card__cat">{_esc(_cat_name(c))}</span>'
            for c in (post.categories or [])
        )

        excerpt = _excerpt(post)

        out.append(
            f'<a class="nf-post-card nf-reveal" href="{_esc(post.url)}">'
            f'<span class="nf-post-card__meta">{"".join(meta)}</span>'
            f'<span class="nf-post-card__title">{_esc(post.title)}</span>'
            f'<span class="nf-post-card__excerpt">{_esc(excerpt)}</span>'
            f'<span class="nf-post-card__cats">{cats}</span>'
            f'<span class="nf-post-card__more">Read post</span>'
            f"</a>"
        )
    out.append("</div>")
    return "".join(out)


def _render_categories(posts) -> str:
    # Count posts per category, keeping the plugin's own URL for each.
    seen: dict[str, dict] = {}
    for post in posts:
        for cat in post.categories or []:
            name = _cat_name(cat)
            entry = seen.setdefault(
                name, {"url": cat.url, "title": name, "count": 0}
            )
            entry["count"] += 1

    if not seen:
        return ""

    ordered = sorted(seen.values(), key=lambda e: (-e["count"], e["title"].lower()))

    chips = "".join(
        f'<a class="nf-cat-chip nf-reveal" href="{_esc(e["url"])}">'
        f'<span class="nf-cat-chip__name">{_esc(e["title"])}</span>'
        f'<span class="nf-cat-chip__count">{e["count"]}</span>'
        f"</a>"
        for e in ordered
    )
    return f'<div class="nf-cat-chips">{chips}</div>'


def on_post_build(config, **kwargs):
    """Inject the blocks once every page has rendered.

    This runs at post-build rather than on_page_markdown deliberately.
    The blog plugin fills in `readtime` and the category `title` only
    while each post or view page renders, and the homepage renders
    before them, so at markdown time read times are absent and category
    titles are None. By post-build every value is final.

    The markers are HTML comments, so if this hook never runs they stay
    invisible on the page rather than showing as stray text.
    """
    try:
        site_dir = pathlib.Path(config["site_dir"])
    except Exception:
        site_dir = pathlib.Path(getattr(config, "site_dir", "site"))

    index = site_dir / "index.html"
    if not index.is_file():
        log.warning("blog_index hook: %s not found; skipping", index)
        return

    html = index.read_text(encoding="utf-8")
    if RECENT_MARKER not in html and CATEGORY_MARKER not in html:
        return

    try:
        posts = _posts(config)
    except Exception as error:  # pragma: no cover - defensive
        log.warning("blog_index hook: could not read posts (%s)", error)
        posts = []

    if not posts:
        log.warning("blog_index hook: no posts found; using fallback link")

    html = html.replace(RECENT_MARKER, _render_posts(posts))
    html = html.replace(CATEGORY_MARKER, _render_categories(posts))
    index.write_text(html, encoding="utf-8")
    log.info("blog_index hook: injected %d post(s) into the homepage", len(posts))
