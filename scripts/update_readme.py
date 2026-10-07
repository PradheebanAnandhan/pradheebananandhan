"""Refresh the auto-updated sections of README.md from the GitHub API.

Run by .github/workflows/update-readme.yml on a schedule. Only text between
the <!-- name:start --> and <!-- name:end --> markers is replaced.
"""

import json
import os
import re
import urllib.request
from datetime import datetime
from pathlib import Path

USER = "PradheebanAnandhan"
README = Path(__file__).resolve().parent.parent / "README.md"


def github(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def escape(text):
    # Repo descriptions are user-written; keep them from breaking the markdown.
    return re.sub(r"([\\`*_\[\]<>|])", r"\\\1", text)


def recent_repos(limit=5):
    repos = github(f"/users/{USER}/repos?sort=pushed&per_page=30")
    lines = []
    for repo in repos:
        if repo["fork"] or repo["name"].lower() == USER.lower():
            continue
        pushed = datetime.strptime(repo["pushed_at"], "%Y-%m-%dT%H:%M:%SZ")
        line = f"[{escape(repo['name'])}]({repo['html_url']})"
        if repo.get("description"):
            line += f" · {escape(repo['description'])}"
        line += f" · <sub>{pushed:%d %b %Y}</sub>"
        lines.append(line)
        if len(lines) == limit:
            break
    return "\n\n".join(lines) or "_Nothing public yet._"


def replace_section(text, name, body):
    pattern = re.compile(
        rf"(<!-- {name}:start -->\n).*?(\n<!-- {name}:end -->)", re.DOTALL
    )
    if not pattern.search(text):
        raise SystemExit(f"README is missing the {name} markers")
    return pattern.sub(lambda m: m.group(1) + body + m.group(2), text)


def main():
    text = README.read_text()
    text = replace_section(text, "recent", recent_repos())
    README.write_text(text)


if __name__ == "__main__":
    main()
