#!/usr/bin/env python3
"""Vet candidate GitHub repos before scavenging from them.

Pulls hard signals instead of eyeballing a README: license (SPDX), stars,
OpenSSF Scorecard "Maintained" score, archived flag, and days since last push.
Sources: deps.dev (no auth needed) and the GitHub REST API (uses GH_TOKEN /
GITHUB_TOKEN when set; skipped quietly if unreachable). Stdlib only.

Usage:
    python3 vet_repos.py owner/repo https://github.com/owner/other ...
    python3 vet_repos.py --json owner/repo ...
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

PERMISSIVE = {
    "MIT", "MIT-0", "BSD-2-Clause", "BSD-3-Clause", "0BSD", "Apache-2.0", "ISC",
    "Unlicense", "Zlib", "BSL-1.0", "CC0-1.0", "PSF-2.0", "Python-2.0", "WTFPL",
}
WEAK_COPYLEFT_PREFIXES = ("LGPL", "MPL", "EPL", "CDDL")
STRONG_COPYLEFT_PREFIXES = ("GPL", "AGPL", "EUPL", "OSL", "SSPL")

STALE_DAYS = 730
TIMEOUT = 15


def parse_repo(arg):
    """Accept owner/repo or any github.com URL; return 'owner/repo' or None."""
    arg = arg.strip()
    m = re.match(r"^(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s#?]+)", arg)
    if not m:
        m = re.match(r"^([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)$", arg)
    if not m:
        return None
    owner, name = m.group(1), m.group(2)
    if name.endswith(".git"):
        name = name[:-4]
    return f"{owner}/{name}"


def classify_license(spdx):
    """Map an SPDX id to permissive / weak-copyleft / copyleft / none / unknown."""
    if not spdx or spdx in ("NOASSERTION", "non-standard"):
        return "none" if not spdx else "unknown"
    ids = re.split(r"\s+(?:OR|AND)\s+", spdx.strip("() "))
    if any(i in PERMISSIVE for i in ids) and " AND " not in spdx:
        return "permissive"
    if any(i.startswith(STRONG_COPYLEFT_PREFIXES) for i in ids):
        return "copyleft"
    if any(i.startswith(WEAK_COPYLEFT_PREFIXES) for i in ids):
        return "weak-copyleft"
    if all(i in PERMISSIVE for i in ids):
        return "permissive"
    return "unknown"


def _get_json(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "repo-scavenger", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.load(resp)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


def fetch_depsdev(slug):
    key = urllib.parse.quote(f"github.com/{slug}", safe="")
    return _get_json(f"https://api.deps.dev/v3/projects/{key}")


def fetch_github(slug):
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = _get_json(f"https://api.github.com/repos/{slug}", headers)
    return data if data and "full_name" in data else None


def vet(slug):
    dd = fetch_depsdev(slug) or {}
    gh = fetch_github(slug) or {}

    checks = {c["name"]: c.get("score") for c in (dd.get("scorecard") or {}).get("checks", [])}
    maintained = checks.get("Maintained")
    if maintained is not None and maintained < 0:
        maintained = None

    license_id = ((gh.get("license") or {}).get("spdx_id")) or dd.get("license") or ""
    license_class = classify_license(license_id)

    days_since_push = None
    if gh.get("pushed_at"):
        pushed = datetime.fromisoformat(gh["pushed_at"].replace("Z", "+00:00"))
        days_since_push = (datetime.now(timezone.utc) - pushed).days

    flags = []
    if not dd and not gh:
        return {"repo": slug, "url": f"https://github.com/{slug}", "verdict": "avoid", "license": None,
                "license_class": None, "stars": None, "forks": None, "maintained": None, "scorecard": None,
                "days_since_push": None, "default_branch": None, "description": None,
                "flags": ["not found (typo, private, or offline?)"]}
    if gh.get("archived"):
        flags.append("archived")
    if gh.get("fork"):
        flags.append("is a fork; check upstream")
    if license_class == "none":
        flags.append("no license (all rights reserved)")
    elif license_class == "unknown":
        flags.append(f"unrecognized license '{license_id}'; read it")
    elif license_class in ("copyleft", "weak-copyleft"):
        flags.append(f"{license_class} ({license_id})")
    if days_since_push is not None and days_since_push > STALE_DAYS:
        flags.append(f"no push in {days_since_push // 365}y")
    if maintained == 0:
        flags.append("quiet for 90d (Scorecard Maintained=0; fine if it's small and finished)")

    if gh.get("archived"):
        verdict = "avoid"
    elif license_class != "permissive":
        verdict = "ask-user"
    else:
        verdict = "ok"

    return {
        "repo": slug,
        "url": f"https://github.com/{slug}",
        "verdict": verdict,
        "license": license_id or None,
        "license_class": license_class,
        "stars": gh.get("stargazers_count", dd.get("starsCount")),
        "forks": gh.get("forks_count", dd.get("forksCount")),
        "maintained": maintained,
        "scorecard": (dd.get("scorecard") or {}).get("overallScore"),
        "days_since_push": days_since_push,
        "default_branch": gh.get("default_branch"),
        "description": gh.get("description") or dd.get("description"),
        "flags": flags,
    }


VERDICT_RANK = {"ok": 0, "ask-user": 1, "avoid": 2}


def sort_key(r):
    return (VERDICT_RANK[r["verdict"]], -(r["maintained"] or 0), -(r["stars"] or 0))


def render_table(rows):
    def cell(v):
        return "-" if v is None else str(v)

    out = [
        "| repo | verdict | license | stars | maintained/10 | last push | flags |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        push = "-" if r["days_since_push"] is None else f"{r['days_since_push']}d ago"
        out.append(
            f"| [{r['repo']}]({r['url']}) | {r['verdict']} | {cell(r['license'])} | {cell(r['stars'])}"
            f" | {cell(r['maintained'])} | {push} | {'; '.join(r['flags']) or '-'} |"
        )
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("repos", nargs="+", help="owner/repo or GitHub URL")
    p.add_argument("--json", action="store_true", help="emit JSON instead of a markdown table")
    args = p.parse_args(argv)

    slugs, bad = [], []
    for a in args.repos:
        s = parse_repo(a)
        if s and s not in slugs:
            slugs.append(s)
        elif not s:
            bad.append(a)
    for b in bad:
        print(f"skipping unrecognized repo: {b}", file=sys.stderr)
    if not slugs:
        return 2

    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = sorted(pool.map(vet, slugs), key=sort_key)

    print(json.dumps(rows, indent=2) if args.json else render_table(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
