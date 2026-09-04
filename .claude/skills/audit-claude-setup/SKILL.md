---
name: audit-claude-setup
description: Audit a Claude Code / Agent SDK setup — CLAUDE.md, rules, skills, subagents, hooks and settings — against agentic architecture principles, and report ranked, evidence-backed improvements. Use when asked to review, evaluate, audit or improve a .claude setup, an agent configuration, or a multi-agent workflow; or when a setup keeps failing to follow its own stated rules.
argument-hint: "[path to project, default: current directory] [--user]"
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# Audit a Claude Code setup

Evaluate an agentic setup against the architecture principles in `rubric.md`, then
report ranked improvements with evidence. **Produce findings, not commits** — the
owner decides what to implement.

The one question this audit exists to answer: **which of this setup's stated rules
are actually enforced, and which are just hopes written in Markdown?**

## 1. Inventory (facts before opinions)

```bash
python3 "$CLAUDE_SKILL_DIR/scan_setup.py" [PATH]          # text report
python3 "$CLAUDE_SKILL_DIR/scan_setup.py" [PATH] --json   # full data, all absolute claims
python3 "$CLAUDE_SKILL_DIR/scan_setup.py" [PATH] --user   # also scan ~/.claude
```

If `$CLAUDE_SKILL_DIR` is unset, use the path this SKILL.md lives in.

The scanner reports what exists and how it is wired: always-loaded context and its
size, rules and whether they are path-scoped, skills and their frontmatter,
subagents and their tool scoping, registered hooks, orphan hook files, mirrored
config trees, broken path references, and every absolute claim in the instruction
files. It makes no quality judgements — that is step 3.

Never skip the scan and audit from memory. The scanner's line counts, hook
registrations and dead references are exactly the things impressions get wrong.

## 2. Read the rubric

Read `rubric.md` in this skill directory. It carries the six domains, the
enforcement spectrum, and the fix for each signal.

## 3. Read what the scan flagged

Open the files the scan raised, plus:

- Every file with absolute claims — the enforcement question is per-claim.
- Each subagent definition — tool scoping, description quality, procedural vs
  goal-oriented prompting.
- The coordinator/orchestrator, if there is one — decomposition breadth,
  parallel spawning, what it passes to subagents.
- Each hook script — does it actually enforce what its registration implies?

Read the files you cite. Do not infer a file's content from its name.

## 4. Evaluate

Work the rubric domain by domain. For every finding, establish:

- **What** is wrong, in one sentence
- **Evidence** — `file:line`, quoted
- **Principle** — the named rubric check
- **Fix** — concrete and sized

Two failure modes to avoid:

- **Cargo-culting the rubric.** Not every setup needs every mechanism. A
  single-agent repo does not need hub-and-spoke findings. Report what is wrong
  *here*, not what is absent from a maximal setup.
- **Trusting the scanner's absolute-claims list as a defect list.** It is a
  worklist. Many hits are prose. Judge each one; report only the ones where a
  single failure actually costs something.

## 5. Report

Open with what the setup gets right — the reader needs proportion, and a
findings-only report reads as noise.

Then a ranked table (impact first, effort second):

| # | Finding | Evidence | Principle | Fix | Impact | Effort |
|---|---|---|---|---|---|---|

Then the detail per finding, and a recommendation of which tier to do first.

Close by asking which items to implement. **Do not start implementing.** If the
owner picks items, implement them then — and if a fix is itself an enforcement
mechanism, validate it against the real files before claiming it works.

## Notes

- Auditing a setup that includes *this* skill is fine and expected; hold it to
  the same rubric.
- **No `context: fork`, deliberately.** The rubric says verbose analysis skills
  should fork. This one doesn't, because its deliverable is a detailed
  evidence-backed table that a fork's return summary would flatten, and because
  the owner usually picks fixes to implement straight after — which needs the
  files still in context. Add `context: fork` if you only ever want the verdict.
- The scanner is stdlib-only Python 3.9+, so it runs on a stock macOS Python.
- Findings about `~/.claude` (user scope) affect every project on the machine.
  Flag them separately from project-scope findings — they have a different
  blast radius and a different owner.
