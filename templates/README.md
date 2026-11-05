# Post templates

Starting points for new blog posts. **These files live outside `docs/`, so MkDocs never
sees them and they are never published.** They exist in the repo as reference only.

## Templates

| File | Use for |
|---|---|
| [`post-skeleton.md`](post-skeleton.md) | Any post — frontmatter reference plus a tour of every MkDocs Material feature available |
| [`mkdocs-feature-reference.md`](mkdocs-feature-reference.md) | The fuller feature catalogue: admonitions, tabs, mermaid, annotations, keys, critic markup |
| [`threat-hunting.md`](threat-hunting.md) | Hunt writeups — hypothesis, telemetry, queries, findings, playbook updates |
| [`detection-engineering.md`](detection-engineering.md) | Detection deep dives — technique, logic, Sigma/KQL/SPL, tuning, validation |
| [`dfir-investigation.md`](dfir-investigation.md) | Incident writeups — scope, timeline, evidence, root cause, containment |
| [`adversary-emulation.md`](adversary-emulation.md) | Emulation playbooks — target TTPs, execution, OPSEC notes, detection outcomes |

## Writing a new post

1. Copy a template into `docs/blog/posts/` and give it a descriptive slug:

   ```bash
   cp templates/threat-hunting.md docs/blog/posts/hunting-dcsync-abuse.md
   ```

2. Fill in the frontmatter. `date`, `authors` and `categories` are required:

   ```yaml
   ---
   date: 2026-11-05
   authors:
     - n1ghtfury
   categories:
     - Threat Hunting
     - Detection Engineering
   tags:
     - DCSync
     - Active Directory
   ---
   ```

3. Replace every placeholder — anything in `[square brackets]`, `TXXXX.XXX`, or a line
   beginning *"Replace this with…"*.

4. Keep `<!-- more -->` after the opening paragraph. Everything above it becomes the
   excerpt shown on the blog index card.

5. Remove `draft: true` when you're ready to publish. While it's present the post builds
   locally with `mkdocs serve` but is excluded from the deployed site.

## Allowed categories

Set in `categories_allowed` in [`mkdocs.yml`](../mkdocs.yml). A category outside this list
fails the build:

- Threat Hunting
- Detection Engineering
- Security Engineering
- DFIR
- Adversary Emulation
- Tools
- MISC

A post can carry several — the WRAITH post sits under Security Engineering, Threat Hunting
and Tools. Tags are free-form and need no registration.

## Images

Put a post's images in a folder beside it and reference them relatively:

```
docs/blog/posts/
├── building-wraith.md
└── wraith-diagrams/
    └── 01-the-whole-idea.svg
```

```markdown
![the whole idea](wraith-diagrams/01-the-whole-idea.svg)
```

Light-background diagrams are handled automatically — site CSS puts them on a light panel
so they stay readable in dark mode.

## Preview locally

```bash
pip install -r requirements.txt
mkdocs serve          # http://127.0.0.1:8000
mkdocs build --strict # what CI runs
```
