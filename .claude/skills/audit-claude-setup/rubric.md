# Audit rubric

Derived from the *Claude Architect Certification* notes (Anthropic Architect's
Playbook + the six CCAF domains) and the Claude Code docs. Each check names the
signal to look for and the fix, so a finding is always actionable.

Score each domain **Strong / Adequate / Weak** with file:line evidence. A domain
with no evidence either way is *Unknown* — say so rather than guessing.

---

## 0. The enforcement spectrum (apply this first, it dominates)

The central diagnostic. For every rule the setup states as absolute, ask: **what
happens on the run where the model just doesn't?**

| Requirement | Mechanism | Guarantee |
|---|---|---|
| Must hold 100% of the time | Hook / `settings.json` | Deterministic |
| Preferred, occasional deviation is fine | Prompt / CLAUDE.md / rule | Probabilistic |

Prompt-based guidance works ~90–95% of the time. That failure rate is fine for a
formatting preference and unacceptable where a single failure costs money, breaks
compliance, or corrupts data. Adding *more* instructions moves 8% to 3%, never to 0.

**Check:** the scanner lists every "always / never / must / alltid / aldrig /
måste / obligatorisk" line. For each, find the enforcing hook. No hook behind an
absolute claim = it is a preference wearing a rule's clothing. Either enforce it
or soften the wording so the setup stops lying about itself.

That list is a worklist, not a defect list — plenty of hits are prose. Judge each.

**Do not report as findings:** rules that genuinely are preferences (tone, naming
taste), or claims where the cost of one failure is trivial.

---

## 1. Agentic architecture & orchestration

| Check | Signal | Fix |
|---|---|---|
| **Parallel spawning** | Independent subagent tasks invoked one per turn | Emit multiple Agent/Task calls in a single response |
| **Goal-oriented delegation** | Coordinator prompt dictates step-by-step procedure | State the goal and quality criteria; let the subagent adapt |
| **Decomposition breadth** | Output misses whole categories (not depth — *scope*) | Fix the coordinator's decomposition; adding subagents won't help |
| **Context passing** | Subagent prompt omits prior findings, or passes content without source metadata | Pass complete findings + metadata (source, URL, date) explicitly — subagents inherit nothing |
| **Hub-and-spoke** | Subagents talking to each other | Route everything through the coordinator: observability, uniform error handling |
| **Spawn capability** | Coordinator lacks `Agent`/`Task` in `tools` | Binary gate — without it, it cannot delegate at all |
| **Completion gating** | Subagent can return non-conforming work | `SubagentStop` hook blocking with a reason; cap the retries so it can't loop |
| **Least privilege** | Subagent declares no `tools:` | Scope each to what its role needs |

**Trace failures to their origin.** Incomplete output is usually the coordinator's
decomposition or its context passing, not the subagent that produced the text.

---

## 2. Tool design & MCP

| Check | Signal | Fix |
|---|---|---|
| **Granularity** | One tool doing many unrelated things | Split into single-purpose tools |
| **Result trimming** | Verbose tool output flowing straight into context | Trim to relevant fields in a `PostToolUse` hook or the tool itself — once it's in history, it's in every later turn |
| **Structured errors** | Failures surfacing as free text | Return `isError` / `isRetryable`; resolve locally first |
| **Search vs read** | Bulk sequential file reads | `Grep` for targeted text, `Glob` for finding files, `Read` only when the whole file is needed |

---

## 3. Claude Code configuration

| Check | Signal | Fix |
|---|---|---|
| **CLAUDE.md size** | >200 lines | Move file-type conventions to path-scoped rules; imports don't shrink context, they only reorganise it |
| **Right mechanism** | File-type conventions in root CLAUDE.md; task workflows in CLAUDE.md; always-on standards in a skill | Universal → CLAUDE.md · file-type across dirs → `.claude/rules/` with `paths:` · on-demand workflow → skill |
| **Rule scoping** | Rules with no `paths:` frontmatter | Add globs so they load only with matching files |
| **Skill shape** | Flat `.md` directly in `.claude/skills/` | A skill is a *directory* with `SKILL.md`; flat files only work under `.claude/commands/` |
| **Skill description** | Missing/vague `description` | Without it the skill only fires on explicit `/invocation` |
| **Verbose skills** | Analysis/brainstorm output polluting the main thread | `context: fork` |
| **Scope placement** | Team rules in `~/.claude/` | Project scope (`.claude/`) ships via git; user scope is personal and unshared |
| **Config drift** | Mirrored trees (`.agents/`, `.codex/`), stale path references | Symlink or generate from one source; a copy always drifts |
| **Conflicts** | Two files stating different rules for the same thing | Contradictions resolve arbitrarily — delete one |
| **Enforcement vs guidance** | Hard requirements living in CLAUDE.md | `settings.json` and hooks are enforced by the client; CLAUDE.md is not |

---

## 4. Prompt engineering & structured output

| Check | Signal | Fix |
|---|---|---|
| **Few-shot over verbosity** | Long format instructions, output still inconsistent | 2–4 targeted examples **with reasoning** — the reasoning is what generalises |
| **Failing-case coverage** | Examples only show the happy path | Show the cases that actually fail, plus counter-examples of what *not* to flag |
| **Validation-retry** | Retry with no error detail | Feed back the original input, the failed output, **and the specific error** |
| **Retry boundary** | Retrying for information absent from the source | Retries fix format/structure/placement; they cannot invent missing data — escalate instead |
| **Self-checking output** | No way to detect a bad result | Ask for both a computed and a stated value; disagreement flags itself |

---

## 5. Context management & reliability

| Check | Signal | Fix |
|---|---|---|
| **Always-on budget** | Large unscoped rules + long CLAUDE.md | Path-scope; measure the per-session cost |
| **Critical facts vs summary** | Amounts, dates, IDs living only in summarisable history | Persistent facts block, included every turn, never summarised |
| **Lost in the middle** | Key findings buried mid-input | Key-findings summary first, explicit section headers after |
| **Upstream verbosity** | Subagents returning reasoning chains | Return structured findings + metadata, not prose |
| **Compaction survival** | Instruction vanishes after `/compact` | Root CLAUDE.md is re-injected; nested/path-scoped reload on match; conversation-only instructions are lost |

---

## 6. Escalation to human

| Check | Signal | Fix |
|---|---|---|
| **Explicit request** | Agent investigating instead of handing off | A request for a human escalates immediately, no triage |
| **Valid triggers** | Escalating on complexity or sentiment | Escalate on explicit request, policy ambiguity, or inability to make progress — not on difficulty |
| **Handoff quality** | Raw transcript passed along | Structured summary: who, root cause, what was tried, recommended action — the human cannot see the transcript |
| **Phase gates** | "Ask before continuing" as prompt only | A prompt gate is probabilistic; if the gate must hold, back it with a hook |

---

## Reporting

Rank findings by **impact first, effort second**. Each finding gets:

- **What** — one sentence
- **Evidence** — `file:line`, quoted
- **Principle** — which check above, named
- **Fix** — concrete, sized (a line edit, a new hook, a restructure)

State clearly what is already good — an audit that only lists faults gives no
sense of proportion. And separate *verified* from *suspected*: if you did not
open the file, say so.

Stop at the ranked list. The owner decides what to implement.
