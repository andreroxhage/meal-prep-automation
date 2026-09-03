#!/usr/bin/env python3
"""Inventory a Claude Code setup so an audit starts from facts, not impressions.

Usage:
    python3 scan_setup.py [ROOT] [--user] [--json]

    ROOT     project directory to scan (default: current directory)
    --user   also scan ~/.claude (user scope)
    --json   emit machine-readable JSON instead of the text report

Reports what exists, how it is wired, and where the wiring has gaps. It makes
no judgements about quality — that is the reading pass in SKILL.md. Standard
library only, so it runs anywhere Python 3.9+ does.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Language that asserts a rule holds every time. Each of these is a claim to
# check against the enforcement layer: prompt (probabilistic) or hook/settings
# (deterministic). Swedish included — this user writes instructions in both.
ABSOLUTE = re.compile(
    r"\b(always|never|must|mandatory|required|critical|ensure|every time"
    r"|alltid|aldrig|måste|obligatorisk|krävs|varje gång|ska alltid)\b",
    re.IGNORECASE,
)

HOOK_EVENTS_BLOCKING = {"PreToolUse", "UserPromptSubmit", "Stop", "SubagentStop", "PreCompact"}
CLAUDE_MD_SOFT_LIMIT = 200  # lines; docs recommend staying under this


# --------------------------------------------------------------------------
# Frontmatter (no PyYAML — must run on a stock macOS Python)
# --------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, int]:
    """Return (frontmatter dict, number of body lines). Values stay strings/lists."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, len(lines)
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, len(lines)

    data: dict = {}
    current_key: str | None = None
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s*-\s+(.*)$", raw)
        if item and current_key:
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(item.group(1).strip().strip("\"'"))
            continue
        pair = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", raw)
        if pair:
            key, value = pair.group(1), pair.group(2).strip()
            current_key = key
            if value in ("", "|", ">"):
                data[key] = []
            elif value.startswith("[") and value.endswith("]"):
                data[key] = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
            else:
                data[key] = value.strip("\"'")
    return data, len(lines) - end - 1


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


# --------------------------------------------------------------------------

@dataclass
class Finding:
    level: str          # WARN | INFO
    area: str
    message: str


@dataclass
class Scan:
    root: str
    memory: list = field(default_factory=list)
    rules: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    agents: list = field(default_factory=list)
    hooks: dict = field(default_factory=dict)
    hook_files: list = field(default_factory=list)
    absolutes: list = field(default_factory=list)
    findings: list = field(default_factory=list)

    def warn(self, area: str, message: str) -> None:
        self.findings.append(asdict(Finding("WARN", area, message)))

    def info(self, area: str, message: str) -> None:
        self.findings.append(asdict(Finding("INFO", area, message)))


# --------------------------------------------------------------------------
# Scanners
# --------------------------------------------------------------------------

def scan_memory(root: Path, scan: Scan) -> None:
    """CLAUDE.md and friends: what loads into every single session."""
    candidates = [
        root / "CLAUDE.md",
        root / ".claude" / "CLAUDE.md",
        root / "CLAUDE.local.md",
        root / "AGENTS.md",
    ]
    for path in candidates:
        if not path.exists() and not path.is_symlink():
            continue
        entry = {
            "path": str(path.relative_to(root)),
            "lines": len(read(path).split("\n")) if path.exists() else 0,
            "symlink_to": os.readlink(path) if path.is_symlink() else None,
        }
        scan.memory.append(entry)

        if path.name == "CLAUDE.md" and entry["lines"] > CLAUDE_MD_SOFT_LIMIT:
            scan.warn(
                "memory",
                f"{entry['path']} is {entry['lines']} lines (soft limit "
                f"{CLAUDE_MD_SOFT_LIMIT}). Long files reduce adherence — move "
                "file-type conventions into path-scoped .claude/rules/.",
            )

    agents_md = root / "AGENTS.md"
    claude_md = root / "CLAUDE.md"
    if agents_md.exists() and claude_md.exists() and not agents_md.is_symlink():
        a, c = read(agents_md), read(claude_md)
        if a and c and a != c:
            overlap = len(set(a.split("\n")) & set(c.split("\n")))
            if overlap > 20:
                scan.warn(
                    "memory",
                    "AGENTS.md and CLAUDE.md are separate files sharing "
                    f"{overlap} identical lines — a copy that will drift. "
                    "Symlink AGENTS.md → CLAUDE.md, or import with @AGENTS.md.",
                )


def scan_rules(root: Path, scan: Scan) -> None:
    """.claude/rules/: always-on vs path-scoped context cost."""
    rules_dir = root / ".claude" / "rules"
    if not rules_dir.is_dir():
        scan.info("rules", "No .claude/rules/ directory — every convention loads from CLAUDE.md.")
        return

    always_on_lines = 0
    for path in sorted(rules_dir.rglob("*.md")):
        fm, body_lines = parse_frontmatter(read(path))
        paths = fm.get("paths")
        if isinstance(paths, str):
            paths = [paths]
        entry = {
            "path": str(path.relative_to(root)),
            "lines": body_lines,
            "paths": paths or [],
            "scoped": bool(paths),
        }
        scan.rules.append(entry)
        if not paths:
            always_on_lines += body_lines

    if always_on_lines > 100:
        scan.warn(
            "rules",
            f"{always_on_lines} lines of rules have no `paths:` frontmatter, so they "
            "load in every session regardless of what is being edited. Scope them.",
        )


def scan_skills(root: Path, scan: Scan) -> None:
    skills_dir = root / ".claude" / "skills"
    if not skills_dir.is_dir():
        return

    for stray in sorted(skills_dir.glob("*.md")):
        scan.warn(
            "skills",
            f"{stray.relative_to(root)} is a flat file directly inside .claude/skills/ — "
            "it creates no command. A skill is a directory containing SKILL.md; a flat "
            "file only works under .claude/commands/.",
        )

    for entry_path in sorted(skills_dir.glob("*/SKILL.md")):
        fm, body_lines = parse_frontmatter(read(entry_path))
        entry = {
            "path": str(entry_path.relative_to(root)),
            "name": fm.get("name", entry_path.parent.name),
            "has_description": bool(fm.get("description")),
            "description_len": len(fm.get("description", "")) if isinstance(fm.get("description"), str) else 0,
            "context_fork": fm.get("context") == "fork",
            "allowed_tools": fm.get("allowed-tools") or [],
            "argument_hint": fm.get("argument-hint"),
            "lines": body_lines,
        }
        scan.skills.append(entry)

        if not entry["has_description"]:
            scan.warn(
                "skills",
                f"{entry['path']} has no `description` — Claude has nothing to match "
                "intent against, so it only ever fires on explicit /invocation.",
            )
        if entry["lines"] > 300:
            scan.info(
                "skills",
                f"{entry['path']} is {entry['lines']} lines. Consider splitting "
                "reference material into supporting files beside SKILL.md.",
            )


def scan_agents(root: Path, scan: Scan) -> None:
    agents_dir = root / ".claude" / "agents"
    if not agents_dir.is_dir():
        return

    for path in sorted(agents_dir.glob("*.md")):
        fm, body_lines = parse_frontmatter(read(path))
        tools = fm.get("tools")
        if isinstance(tools, str):
            tools = [t.strip() for t in tools.split(",") if t.strip()]
        tools = tools or []
        entry = {
            "path": str(path.relative_to(root)),
            "name": fm.get("name", path.stem),
            "model": fm.get("model"),
            "tools": tools,
            "unrestricted_tools": not tools,
            "can_spawn": any(t.startswith(("Agent", "Task")) for t in tools),
            "has_description": bool(fm.get("description")),
            "lines": body_lines,
            "own_hooks": "hooks" in fm,
        }
        scan.agents.append(entry)

        if entry["unrestricted_tools"]:
            scan.warn(
                "agents",
                f"{entry['path']} declares no `tools:` — it inherits the full tool set. "
                "Scope each subagent to the tools its role needs.",
            )
        if not entry["has_description"]:
            scan.warn(
                "agents",
                f"{entry['path']} has no `description` — the coordinator cannot tell "
                "when to delegate to it.",
            )


def scan_hooks(root: Path, scan: Scan) -> None:
    """settings.json hook registrations vs hook files actually on disk."""
    registered_commands: set[str] = set()

    for settings_name in ("settings.json", "settings.local.json"):
        settings_path = root / ".claude" / settings_name
        if not settings_path.is_file():
            continue
        try:
            settings = json.loads(read(settings_path))
        except json.JSONDecodeError as exc:
            scan.warn("hooks", f".claude/{settings_name} is not valid JSON: {exc}")
            continue

        for event, groups in (settings.get("hooks") or {}).items():
            for group in groups:
                for hook in group.get("hooks", []):
                    command = hook.get("command", "")
                    registered_commands.add(Path(command).name)
                    scan.hooks.setdefault(event, []).append({
                        "source": settings_name,
                        "matcher": group.get("matcher", "(all)"),
                        "command": command,
                    })
                    resolved = Path(
                        command.replace("${CLAUDE_PROJECT_DIR}", str(root))
                               .replace("$CLAUDE_PROJECT_DIR", str(root))
                    )
                    if command and not resolved.exists():
                        scan.warn("hooks", f"{event} hook points at a missing file: {command}")
                    elif resolved.exists() and not os.access(resolved, os.X_OK):
                        scan.warn("hooks", f"{event} hook is not executable: {command}")

    hooks_dir = root / ".claude" / "hooks"
    if hooks_dir.is_dir():
        for path in sorted(hooks_dir.iterdir()):
            if path.is_file() and path.suffix in (".sh", ".py", ".js", ".ts", ""):
                scan.hook_files.append(str(path.relative_to(root)))
                if path.name not in registered_commands and not path.name.startswith("test"):
                    scan.info(
                        "hooks",
                        f"{path.relative_to(root)} exists but no settings.json hook "
                        "references it (helper, or an orphan?).",
                    )

    for path in scan.agents:
        if path["own_hooks"]:
            scan.info("hooks", f"{path['path']} defines its own scoped hooks in frontmatter.")


def scan_absolutes(root: Path, scan: Scan) -> None:
    """Every 'always/never' claim is a promise the setup must actually keep."""
    targets: list[Path] = []
    for pattern in ("CLAUDE.md", ".claude/rules/**/*.md", ".claude/agents/*.md",
                    ".claude/skills/*/SKILL.md"):
        targets.extend(p for p in root.glob(pattern) if p.is_file() and not p.is_symlink())

    for path in sorted(set(targets)):
        lines = read(path).split("\n")
        # Skip frontmatter: a description naming a rule is metadata, not a claim.
        start = 0
        if lines and lines[0].strip() == "---":
            for i in range(1, len(lines)):
                if lines[i].strip() == "---":
                    start = i + 1
                    break

        for line_no, line in enumerate(lines[start:], start=start + 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("```", "|", ">")):
                continue
            if ABSOLUTE.search(stripped):
                scan.absolutes.append({
                    "path": str(path.relative_to(root)),
                    "line": line_no,
                    "text": stripped[:160],
                })


def scan_duplication(root: Path, scan: Scan) -> None:
    """Mirrored config trees drift silently; so do references to moved paths."""
    mirrors = [d for d in (root / ".agents", root / ".codex", root / ".cursor") if d.is_dir()]
    for mirror in mirrors:
        scan.warn(
            "drift",
            f"{mirror.name}/ mirrors .claude/ — a second copy that will drift out of "
            "sync. Symlink it, or generate it from one source.",
        )

    referenced = set()
    for path in root.rglob("*.md"):
        if ".git" in path.parts or path.is_symlink():
            continue
        for match in re.finditer(r"`(\.claude/[\w./*-]+)`", read(path)):
            referenced.add((str(path.relative_to(root)), match.group(1)))

    for source, target in sorted(referenced):
        clean = target.rstrip("/")
        if "*" in clean:
            continue
        if not (root / clean).exists():
            scan.warn("drift", f"{source} references `{clean}`, which does not exist.")


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def render(scan: Scan) -> str:
    out: list[str] = [f"# Claude setup inventory — {scan.root}", ""]

    out.append("## Always-loaded context")
    if scan.memory:
        for m in scan.memory:
            link = f" → {m['symlink_to']}" if m["symlink_to"] else ""
            out.append(f"  {m['path']}{link} ({m['lines']} lines)")
    else:
        out.append("  (none)")
    scoped = [r for r in scan.rules if r["scoped"]]
    unscoped = [r for r in scan.rules if not r["scoped"]]
    out.append(f"  rules: {len(scoped)} path-scoped, {len(unscoped)} always-on")
    for r in scan.rules:
        marker = ", ".join(r["paths"]) if r["scoped"] else "ALWAYS ON"
        out.append(f"    {r['path']} ({r['lines']} lines) — {marker}")

    out.append("")
    out.append("## Skills (on-demand)")
    for s in scan.skills or []:
        flags = []
        if s["context_fork"]:
            flags.append("context: fork")
        if s["allowed_tools"]:
            flags.append(f"allowed-tools: {len(s['allowed_tools'])}")
        if not s["has_description"]:
            flags.append("NO DESCRIPTION")
        out.append(f"  /{s['name']} ({s['lines']} lines){' — ' + ', '.join(flags) if flags else ''}")
    if not scan.skills:
        out.append("  (none)")

    out.append("")
    out.append("## Subagents")
    for a in scan.agents or []:
        tools = ", ".join(a["tools"]) if a["tools"] else "ALL (unrestricted)"
        spawn = " [can spawn subagents]" if a["can_spawn"] else ""
        out.append(f"  {a['name']} — model: {a['model'] or 'inherit'}{spawn}")
        out.append(f"    tools: {tools}")
    if not scan.agents:
        out.append("  (none)")

    out.append("")
    out.append("## Hooks (deterministic enforcement)")
    if scan.hooks:
        for event, entries in scan.hooks.items():
            blocking = " (can block)" if event in HOOK_EVENTS_BLOCKING else " (feedback only)"
            out.append(f"  {event}{blocking}")
            for e in entries:
                out.append(f"    matcher {e['matcher']} → {e['command']}")
    else:
        out.append("  NONE — nothing in this setup is enforced deterministically.")

    out.append("")
    out.append(f"## Absolute claims ({len(scan.absolutes)})")
    out.append("  Each line asserts something holds every time. Check each against the")
    out.append("  hooks above: a claim with no hook behind it is a preference, not a rule.")
    by_file: dict[str, list] = {}
    for a in scan.absolutes:
        by_file.setdefault(a["path"], []).append(a)
    for path, items in sorted(by_file.items()):
        out.append(f"  {path} ({len(items)})")
        for item in items[:4]:
            out.append(f"    :{item['line']} {item['text']}")
        if len(items) > 4:
            out.append(f"    … {len(items) - 4} more (use --json for the full list)")

    out.append("")
    warns = [f for f in scan.findings if f["level"] == "WARN"]
    infos = [f for f in scan.findings if f["level"] == "INFO"]
    out.append(f"## Mechanical findings ({len(warns)} WARN, {len(infos)} INFO)")
    for f in warns + infos:
        out.append(f"  {f['level']:5} [{f['area']}] {f['message']}")
    if not scan.findings:
        out.append("  (none)")

    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".", type=Path)
    ap.add_argument("--user", action="store_true", help="also scan ~/.claude")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    roots = [args.root.resolve()]
    if args.user:
        roots.append(Path.home())

    scans = []
    for root in roots:
        if not root.is_dir():
            print(f"{root}: not a directory", file=sys.stderr)
            return 2
        scan = Scan(root=str(root))
        scan_memory(root, scan)
        scan_rules(root, scan)
        scan_skills(root, scan)
        scan_agents(root, scan)
        scan_hooks(root, scan)
        scan_absolutes(root, scan)
        scan_duplication(root, scan)
        scans.append(scan)

    if args.as_json:
        print(json.dumps([asdict(s) for s in scans], indent=2, ensure_ascii=False))
    else:
        print("\n\n".join(render(s) for s in scans))
    return 0


if __name__ == "__main__":
    sys.exit(main())
