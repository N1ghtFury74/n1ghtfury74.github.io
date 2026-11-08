"""
Build-time generation for the homepage and the blog index.

Three jobs:

1. A page is generated for every category in `categories_allowed` that has
   no posts yet, so the full taxonomy is browsable from day one. These sit
   at exactly the URL the blog plugin would use once the category gains a
   post (`blog/category/<slug>/`), using the plugin's own slugify function,
   so the link never changes and never breaks.

2. `<!-- nf:recent-posts -->` in docs/index.md is replaced with cards for
   the most recent posts.

3. `<!-- nf:categories -->` in docs/index.md and docs/blog/index.md is
   replaced with a chip per category, each showing its post count.

Injection happens at on_post_build, not on_page_markdown. The blog plugin
fills in `readtime` and the category `title` only while each post or view
page renders, and the homepage renders first — at markdown time read times
are missing and category titles are None.

Post and category URLs come from the plugin wherever a page exists, so no
slug or date-format logic is duplicated. If anything fails the markers are
left as HTML comments, which are invisible, rather than raising.
"""

from __future__ import annotations

import logging
import pathlib
import re

from mkdocs.plugins import event_priority

log = logging.getLogger("mkdocs.hooks.blog_index")

RECENT_LIMIT = 1
RECENT_MARKER = "<!-- nf:recent-posts -->"
CATEGORY_MARKER = "<!-- nf:categories -->"

FALLBACK = '<p class="nf-empty"><a href="blog/">Browse the blog &rarr;</a></p>'

# Pages the markers may appear in, with the path prefix each needs to reach
# the site root. docs/index.md sits at the root; docs/blog/index.md one down.
TARGETS = {
    "index.html": "",
    "blog/index.html": "../",
}


# -------------------------------------------------------------------------
# Category helpers
# -------------------------------------------------------------------------

def _blog_plugin(config):
    return config.plugins.get("material/blog")


def _slugify(config):
    """The blog plugin's own slugify, so generated stubs match its URLs."""
    plugin = _blog_plugin(config)
    try:
        cfg = plugin.config
        fn, sep = cfg.categories_slugify, cfg.categories_slugify_separator
        return lambda name: fn(name, sep)
    except Exception:
        from pymdownx.slugs import slugify

        fn = slugify(case="lower")
        return lambda name: fn(name, "-")


def _allowed(config):
    plugin = _blog_plugin(config)
    try:
        return list(plugin.config.categories_allowed or [])
    except Exception:
        return []


def _category_url(config, name):
    """URL the blog plugin uses (or would use) for a category."""
    plugin = _blog_plugin(config)
    slug = _slugify(config)(name)
    try:
        fmt = plugin.config.categories_url_format
        blog_dir = plugin.config.blog_dir
    except Exception:
        fmt, blog_dir = "category/{slug}", "blog"
    return f"{blog_dir}/{fmt.format(slug=slug)}/"


def _cat_name(cat) -> str:
    """Display name of a category view.

    `Category.title` is still None while the homepage renders — the blog
    plugin only fills it in when the category's own page is built, which
    happens later. `Category.name` carries the string from the start.
    """
    for attr in ("name", "title"):
        value = getattr(cat, attr, None)
        if isinstance(value, str) and value.strip():
            return value.strip()

    slug = (getattr(cat, "url", "") or "").rstrip("/").rsplit("/", 1)[-1]
    return slug.replace("-", " ").title() if slug else "Uncategorised"


# -------------------------------------------------------------------------
# Post helpers
# -------------------------------------------------------------------------

def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _excerpt(post) -> str:
    """First real paragraph of the post, before the <!-- more --> marker."""
    md = (post.markdown or "").split("<!-- more -->")[0]

    for block in md.split("\n\n"):
        block = block.strip()
        if not block or block.startswith("#"):
            continue
        block = re.sub(r"^\*+|\*+$", "", block.strip())
        block = re.sub(r"\s+", " ", block).strip()
        if block:
            return block
    return ""


def _created(post):
    raw = (post.config or {}).get("date")
    if isinstance(raw, dict):
        raw = raw.get("created")
    return raw


def _date(post) -> str:
    raw = _created(post)
    try:
        # %-d / %#d differ across platforms, so strip the zero by hand
        return f"{raw.strftime('%B')} {raw.day}, {raw.year}"
    except Exception:
        return ""


def _posts(config):
    plugin = _blog_plugin(config)
    posts = list(getattr(getattr(plugin, "blog", None), "posts", []) or [])
    try:
        posts.sort(key=_created, reverse=True)
    except Exception:
        pass
    return posts


# -------------------------------------------------------------------------
# Rendering
# -------------------------------------------------------------------------

def _render_posts(posts, prefix: str) -> str:
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
        # and nesting anchors is invalid HTML.
        cats = "".join(
            f'<span class="nf-post-card__cat">{_esc(_cat_name(c))}</span>'
            for c in (post.categories or [])
        )

        out.append(
            f'<a class="nf-post-card nf-reveal" href="{_esc(prefix + post.url)}">'
            f'<span class="nf-post-card__meta">{"".join(meta)}</span>'
            f'<span class="nf-post-card__title">{_esc(post.title)}</span>'
            f'<span class="nf-post-card__excerpt">{_esc(_excerpt(post))}</span>'
            f'<span class="nf-post-card__cats">{cats}</span>'
            f'<span class="nf-post-card__more">Read post</span>'
            f"</a>"
        )
    out.append("</div>")
    return "".join(out)


def _render_categories(config, posts, prefix: str) -> str:
    """One chip per allowed category, including those with no posts."""
    counts: dict[str, int] = {}
    for post in posts:
        for cat in post.categories or []:
            name = _cat_name(cat)
            counts[name] = counts.get(name, 0) + 1

    names = _allowed(config)
    # Any category used by a post but somehow not in the allowed list still
    # gets a chip, so nothing silently disappears.
    for name in counts:
        if name not in names:
            names.append(name)

    if not names:
        return ""

    chips = []
    for name in names:
        count = counts.get(name, 0)
        empty = " nf-cat-chip--empty" if not count else ""
        url = _category_url(config, name)
        chips.append(
            f'<a class="nf-cat-chip nf-reveal{empty}" href="{_esc(prefix + url)}">'
            f'<span class="nf-cat-chip__name">{_esc(name)}</span>'
            f'<span class="nf-cat-chip__count">{count}</span>'
            f"</a>"
        )
    return f'<div class="nf-cat-chips">{"".join(chips)}</div>'


# -------------------------------------------------------------------------
# Hooks
# -------------------------------------------------------------------------

def on_files(files, config, **kwargs):
    """Generate a page for every category that has no posts yet.

    Categories with posts are left entirely to the blog plugin; this only
    fills the gaps, so the two never collide. Categories are read straight
    from the post source files because the plugin has not collected its
    posts yet at this point in the build.
    """
    try:
        from mkdocs.structure.files import File
    except Exception:  # pragma: no cover
        return files

    plugin = _blog_plugin(config)
    if plugin is None:
        return files

    try:
        blog_dir = plugin.config.blog_dir
    except Exception:
        blog_dir = "blog"

    docs_dir = pathlib.Path(config["docs_dir"])
    used: set[str] = set()

    for path in (docs_dir / blog_dir / "posts").glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
        if not match:
            continue
        block = re.search(
            r"^categories:\s*\n((?:\s*-\s*.+\n?)+)", match.group(1), re.M
        )
        if not block:
            continue
        for line in block.group(1).splitlines():
            item = line.strip()
            if item.startswith("- "):
                used.add(item[2:].strip().strip("'\""))

    slugify = _slugify(config)
    made = 0

    for name in _allowed(config):
        if name in used:
            continue

        src_uri = f"{blog_dir}/category/{slugify(name)}.md"
        if files.get_file_from_path(src_uri) is not None:
            continue

        content = (
            f"---\ntitle: {name}\nsearch:\n  exclude: true\n---\n\n"
            f"# {name}\n\n"
            f'<p class="nf-empty-category">Nothing filed under this category '
            f"yet. It is part of what this blog covers, so posts will land "
            f'here.</p>\n\n'
            f'<p class="nf-empty-category__back">'
            f'<a href="../../">Back to the blog</a></p>\n'
        )

        try:
            files.append(File.generated(config, src_uri, content=content))
            made += 1
        except Exception as error:  # pragma: no cover
            log.warning("blog_index hook: could not generate %s (%s)", src_uri, error)

    if made:
        log.info("blog_index hook: generated %d empty-category page(s)", made)
    return files


def on_post_build(config, **kwargs):
    """Inject the generated blocks once every page has rendered."""
    try:
        site_dir = pathlib.Path(config["site_dir"])
    except Exception:
        site_dir = pathlib.Path(getattr(config, "site_dir", "site"))

    try:
        posts = _posts(config)
    except Exception as error:  # pragma: no cover
        log.warning("blog_index hook: could not read posts (%s)", error)
        posts = []

    if not posts:
        log.warning("blog_index hook: no posts found; using fallback link")

    for rel, prefix in TARGETS.items():
        page = site_dir / rel
        if not page.is_file():
            continue

        html = page.read_text(encoding="utf-8")
        if RECENT_MARKER not in html and CATEGORY_MARKER not in html:
            continue

        html = html.replace(RECENT_MARKER, _render_posts(posts, prefix))
        html = html.replace(
            CATEGORY_MARKER, _render_categories(config, posts, prefix)
        )
        page.write_text(html, encoding="utf-8")
        log.info("blog_index hook: injected into %s", rel)


def _find_section(items, name):
    """Depth-first search for a nav section by title."""
    for item in items or []:
        if getattr(item, "is_section", False) and getattr(item, "title", None) == name:
            return item
        found = _find_section(getattr(item, "children", None), name)
        if found is not None:
            return found
    return None


@event_priority(-100)
def on_nav(nav, config, files, **kwargs):
    """Add the generated empty-category pages to the Categories sidebar.

    Priority -100 so this runs after the blog plugin's own on_nav, which
    is what creates the Categories section in the first place. Without
    it the sidebar lists only the categories that happen to have posts,
    which is exactly the subset a reader does not need help finding.
    """
    plugin = _blog_plugin(config)
    if plugin is None:
        return nav

    try:
        section_name = plugin.config.categories_name
        blog_dir = plugin.config.blog_dir
    except Exception:
        section_name, blog_dir = "Categories", "blog"

    section = _find_section(nav.items, section_name)
    if section is None:
        log.warning("blog_index hook: no %r nav section found", section_name)
        return nav

    allowed = _allowed(config)
    slugify = _slugify(config)
    by_slug = {slugify(name): name for name in allowed}

    present = {getattr(child, "url", None) for child in section.children}
    prefix = f"{blog_dir}/category/"

    for file in files:
        if not file.src_uri.startswith(prefix) or not file.src_uri.endswith(".md"):
            continue

        page = getattr(file, "page", None)
        if page is None or getattr(page, "url", None) in present:
            continue

        title = by_slug.get(file.src_uri[len(prefix):-3])
        if title is None:
            continue

        # Titles are normally resolved while a page renders; set it here
        # so the nav has something to show for pages it never rendered.
        page.title = title
        page.parent = section
        section.children.append(page)

    order = {name: i for i, name in enumerate(allowed)}
    section.children.sort(
        key=lambda c: order.get(getattr(c, "title", None) or _cat_name(c), 999)
    )
    return nav
