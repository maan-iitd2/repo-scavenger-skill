---
name: repo-scavenger
description: Finds and adapts existing open-source code instead of writing boilerplate from scratch. Searches GitHub for repositories that already solve a specific requirement, extracts just the relevant utility functions or classes, strips secrets, adapts them to this project, and saves the result. Use this whenever the user wants to implement a well-trodden feature (rate limiter, retry wrapper, CSV parser, OAuth flow, debounce, slug generator, etc.) and says things like "find me an existing implementation," "don't reinvent this," "scavenge some code for X," "is there an open-source version of this," or otherwise signals they'd rather borrow than build. Prefer this over hand-writing utility code that surely already exists somewhere.
---

# Repo Scavenger

The goal: stop writing boilerplate that thousands of people have already written and debugged. Find a good existing implementation, take only the piece you need, make it fit here, and record where it came from.

This pairs naturally with the `ponytail` skill — invoke it (`Skill: ponytail`) before adapting the code. Its whole ethos ("extract the minimum, don't pull in a whole framework, prefer stdlib") is exactly what keeps a scavenge from turning into a dependency-dragging mess. That's why it's here — not to save tokens, but to keep the extracted code lean.

## Workflow

### 1. Search
Use web search to find GitHub repositories that already solve the user's specific requirement. Search for the *behavior*, not just the name — e.g. "exponential backoff retry decorator python github", "debounce function javascript github". Favor repos with real usage (stars, recent commits, tests) — that's a proxy for "this code actually works."

Prefer 2-3 candidate sources over the first hit, so you can pick the cleanest implementation rather than the first-ranked one.

### 2. Read the source
Locate and read the specific Python or JavaScript file(s) containing the relevant code. Fetch the raw file rather than guessing from a README. You need to see the actual implementation, its imports, and what it depends on.

### 3. Check the license — do this before extracting, not after
Find the repo's license (LICENSE file, or the `license` field in `package.json` / `pyproject.toml`). This matters because copying code carries legal obligations that don't disappear because it's on GitHub:

- **MIT / BSD / Apache-2.0 / ISC** → fine to reuse; keep the attribution.
- **GPL / AGPL / LGPL (copyleft)** → flag it clearly to the user *before* copying. Pulling GPL code into a proprietary project can force the whole project open. Don't silently paste it in.
- **No license at all** → tell the user. "No license" legally means all rights reserved, not "free to take." Suggest they ask, reimplement the idea themselves, or pick a licensed alternative.

If the license is copyleft or missing, stop and surface it. Don't make that call for the user.

### 4. Extract and adapt
Pull out **only** the necessary utility function(s) or class(es). Do not vendor the entire framework or a pile of unrelated helpers — that defeats the purpose. If the snippet drags in a heavy dependency for something trivial, prefer rewriting that part against the standard library (this is where `ponytail` earns its place).

While adapting:
- **Remove any hardcoded secrets** — API keys, tokens, passwords, private URLs. Replace them with a parameter or an environment-variable read, and note it in the summary.
- Match this project's conventions: naming style, import layout, type hints / JSDoc, error handling. The code should read like it was written here, not pasted in.
- Keep a one-line source comment at the top of the adapted code pointing back to the origin (repo URL + license), so provenance survives.

### 5. Save
Write the adapted code to a new file in the local workspace. Pick a sensible path and filename that fits the project's existing structure; if it's ambiguous, ask where it should go.

### 6. Summarize
Print a short summary using this structure:

```
## Scavenged: <what it does>

**Source:** <repo URL> (<license>)
**Saved to:** <local file path>

**Changes made:**
- <e.g. removed hardcoded OPENAI_API_KEY, now reads from env>
- <e.g. dropped the `requests` dependency, used urllib from stdlib>
- <e.g. renamed to match project snake_case>

**Heads-up (if any):** <license caveat, remaining TODO, untested edge case>
```

## Notes

- If nothing good exists, say so and fall back to writing it directly — don't force a bad match just to have "scavenged" something.
- Non-trivial logic you extract should keep (or gain) one runnable check — a small `__main__`/`demo()` assert or a `test_*` — so an adapted snippet isn't trusted blind.
- Never paste code you haven't actually read in full. Provenance and correctness both depend on having seen the source.
