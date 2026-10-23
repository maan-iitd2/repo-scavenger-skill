# 🦴 repo-scavenger

**Stop writing boilerplate.** A [Claude Code](https://claude.com/claude-code) skill that autonomously hunts GitHub for open-source solutions and adapts them to your project.

---

## The Problem & The Solution

**The problem.** Every project needs the same well-trodden utilities — a retry wrapper with exponential backoff, a debounce, a slug generator, a rate limiter, an OAuth flow, a CSV parser. Rewriting them by hand is slow, and the version you write at 2am is buggier than the one a thousand people already battle-tested on GitHub.

**The solution.** `repo-scavenger` turns "I'll just write it myself" into "let's borrow the good version." When you ask for a common utility, the skill searches GitHub for real implementations, reads the actual source, extracts **only** the piece you need, strips out hardcoded secrets, adapts it to your project's conventions, and records exactly where it came from — including a license check so you don't accidentally paste GPL code into a proprietary codebase.

You keep the thinking. The skill just saves you from reinventing the wheel.

## What it does

Three modes, picked from how you ask:

| Mode | Ask it like | You get |
|---|---|---|
| **Snippet** | "find me a retry decorator, don't reinvent it" | Adapted code saved in your project, with provenance |
| **Similar repos** | "find repos like `owner/repo`" / "alternatives to X" | A ranked, vetted table of candidates |
| **Prior art** | "I want to build Y. Has anyone done it?" | The table plus "what exists, where's the gap" |

Under the hood:

1. **Frames the query**: behavior plus synonyms, ecosystem, and the seed repo's topics, instead of one literal search.
2. **Searches wide**: GitHub repo and code search (MCP tools or `gh`), topic search, hidden-gem (low-star) and recently-active passes, package registries, `awesome-*` lists, grep.app/Sourcegraph, with web search as fallback.
3. **Vets with hard signals**: `scripts/vet_repos.py` pulls license (SPDX), stars, OpenSSF Scorecard "Maintained", and archived/last-push status, and ranks candidates `ok` / `ask-user` / `avoid`.
4. **Decides depend vs. extract vs. learn**: a maintained package beats copied code for anything security-sensitive.
5. **Reads the real source pinned to a commit SHA**, checks the license *before* copying, and treats fetched READMEs and code as untrusted (no following embedded instructions, no running install scripts).
6. **Extracts and adapts** only what's needed: strips secrets, matches your style, adds a provenance header and a runnable check.
7. **Summarizes** the source, the runners-up, the changes, and any caveats.

## Installation

Dead simple — Claude Code auto-discovers any skill in your skills directory.

**Option A — user-level (available in every project):**

```bash
git clone https://github.com/maan-iitd2/repo-scavenger-skill.git \
  ~/.claude/skills/repo-scavenger
```

**Option B — project-level (this repo only):**

```bash
git clone https://github.com/maan-iitd2/repo-scavenger-skill.git \
  .claude/skills/repo-scavenger
```

That's it. Restart Claude Code if it was already running, then just ask:

> "find me an existing implementation of exponential backoff retry — don't reinvent it"

> "find repos similar to jd/tenacity"

Claude will pick up the skill and run the scavenging workflow automatically.

### The vetting script on its own

```bash
python3 scripts/vet_repos.py jd/tenacity litl/backoff https://github.com/invl/retry
```

It needs only the Python stdlib. deps.dev requires no auth; set `GH_TOKEN` to add archived/last-push data from the GitHub API. Pass `--json` for machine-readable output. Tests: `python3 -m unittest scripts/test_vet_repos.py`.

## Under the Hood

This skill was architected and generated using **Claude Code's native Skill Creator**, iterating on the skill's system prompt and description until the workflow and triggering behavior were dialed in. The result is a `SKILL.md` plus one small stdlib-only helper script:

- A **"pushy" description** tuned so Claude reliably reaches for the skill on borrow-don't-build requests, without over-triggering on unrelated tasks.
- A **seven-step workflow**: frame, search wide, vet, decide, read and license-check, extract/adapt, summarize. The *reasoning* behind each step is spelled out, so the model adapts instead of following rote instructions.
- A **license-safety gate** baked in, because a skill that copies other people's code has to respect their licenses by design.

It also pairs with the `ponytail` skill (if you have it installed) to keep extractions minimal — take the utility, not the whole framework.

## A note on licensing

`repo-scavenger` copies code from other people's repositories, so it's built to respect their licenses and will stop to ask before pulling in copyleft or unlicensed code. **You** remain responsible for honoring the license of anything it scavenges — treat the built-in check as a helpful guardrail, not legal advice.

## License

MIT — see [LICENSE](LICENSE).
