# 🦴 repo-scavenger

**Stop writing boilerplate.** A [Claude Code](https://claude.com/claude-code) skill that autonomously hunts GitHub for open-source solutions and adapts them to your project.

---

## The Problem & The Solution

**The problem.** Every project needs the same well-trodden utilities — a retry wrapper with exponential backoff, a debounce, a slug generator, a rate limiter, an OAuth flow, a CSV parser. Rewriting them by hand is slow, and the version you write at 2am is buggier than the one a thousand people already battle-tested on GitHub.

**The solution.** `repo-scavenger` turns "I'll just write it myself" into "let's borrow the good version." When you ask for a common utility, the skill searches GitHub for real implementations, reads the actual source, extracts **only** the piece you need, strips out hardcoded secrets, adapts it to your project's conventions, and records exactly where it came from — including a license check so you don't accidentally paste GPL code into a proprietary codebase.

You keep the thinking. The skill just saves you from reinventing the wheel.

## What it does

1. **Searches** GitHub for repos that already solve your specific requirement.
2. **Reads** the actual source file(s) — never guesses from a README.
3. **Checks the license first** — flags copyleft (GPL/AGPL) or missing licenses *before* copying, instead of silently vendoring a legal problem.
4. **Extracts & adapts** just the relevant function/class: removes secrets, matches your code style, leaves a provenance comment.
5. **Saves** it to a sensible path in your workspace.
6. **Summarizes** the source, the changes made, and any caveats.

## Installation

Dead simple — Claude Code auto-discovers any skill in your skills directory.

**Option A — user-level (available in every project):**

```bash
git clone https://github.com/maan-iitd2/claude-code-repo-scavenger.git \
  ~/.claude/skills/repo-scavenger
```

**Option B — project-level (this repo only):**

```bash
git clone https://github.com/maan-iitd2/claude-code-repo-scavenger.git \
  .claude/skills/repo-scavenger
```

That's it. Restart Claude Code if it was already running, then just ask:

> "find me an existing implementation of exponential backoff retry — don't reinvent it"

Claude will pick up the skill and run the scavenging workflow automatically.

## Under the Hood

This skill was architected and generated using **Claude Code's native Skill Creator**, iterating on the skill's system prompt and description until the workflow and triggering behavior were dialed in. The result is a single self-contained `SKILL.md`:

- A **"pushy" description** tuned so Claude reliably reaches for the skill on borrow-don't-build requests, without over-triggering on unrelated tasks.
- A **six-step workflow** in the skill body — search, read, license-check, extract/adapt, save, summarize — with the *reasoning* behind each step spelled out, so the model adapts intelligently rather than following rote instructions.
- A **license-safety gate** baked in, because a skill that copies other people's code has to respect their licenses by design.

It also pairs with the `ponytail` skill (if you have it installed) to keep extractions minimal — take the utility, not the whole framework.

## A note on licensing

`repo-scavenger` copies code from other people's repositories, so it's built to respect their licenses and will stop to ask before pulling in copyleft or unlicensed code. **You** remain responsible for honoring the license of anything it scavenges — treat the built-in check as a helpful guardrail, not legal advice.

## License

MIT — see [LICENSE](LICENSE).
