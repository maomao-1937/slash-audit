#!/usr/bin/env python3
"""Read-only checks for user-facing promises in Claude Code skill files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


MAX_BYTES = 2 * 1024 * 1024
INLINE_CODE = re.compile(r"`([^`\n]+)`")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
SLASH_AT_START = re.compile(
    r"^\s*(?P<name>/[A-Za-z][A-Za-z0-9_-]*(?::[A-Za-z][A-Za-z0-9_-]*)?)(?![\w./-])"
)
SLASH_NAME = re.compile(
    r"(?<![\w/])/(?P<name>[A-Za-z][A-Za-z0-9_-]*(?::[A-Za-z][A-Za-z0-9_-]*)?)(?![\w./-])"
)
MONEY_PLACEHOLDER = re.compile(r"\$(?:\d{1,3}(?:,\d{3})+|\d+\.\d{2})\b")
FRONTMATTER_FIELD = re.compile(r"^([A-Za-z][\w-]*):\s*(.*)$")
BUILTINS = {
    "add-dir", "agents", "bug", "clear", "compact", "config", "context",
    "cost", "doctor", "export", "help", "init", "login", "logout",
    "mcp", "model", "permissions", "plugin", "rename", "review",
    "rewind", "skills", "status", "terminal-setup", "usage",
}


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    column: int
    rule: str
    severity: str
    evidence: str
    message: str
    suggestion: str


def frontmatter(text: str) -> dict[str, str]:
    """Read simple scalar fields only; complex YAML is deliberately not parsed."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return result
        match = FRONTMATTER_FIELD.match(line)
        if match:
            value = match.group(2).strip().strip("\"'")
            if value and value not in {">", "|", ">-", "|-"}:
                result[match.group(1)] = value
    return {}


def plugin_root(skill_file: Path) -> Path:
    skills_dir = skill_file.parent.parent
    return skills_dir.parent if skills_dir.name == "skills" else skill_file.parent


def known_commands(root: Path) -> set[str]:
    names: set[str] = set()
    standalone = root / "SKILL.md"
    if standalone.is_file():
        names.add(root.name)
        metadata = frontmatter(read_skill(standalone))
        if metadata.get("name"):
            names.add(metadata["name"].split(":")[-1])
    skills = root / "skills"
    if skills.is_dir():
        for skill_file in skills.glob("*/SKILL.md"):
            names.add(skill_file.parent.name)
            metadata = frontmatter(read_skill(skill_file))
            if metadata.get("name"):
                names.add(metadata["name"].split(":")[-1])
    commands = root / "commands"
    if commands.is_dir():
        for command_file in commands.rglob("*.md"):
            names.add(":".join(command_file.relative_to(commands).with_suffix("").parts))
            names.add(command_file.stem)
    return names


def read_skill(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"not a regular SKILL.md file: {path}")
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"SKILL.md exceeds {MAX_BYTES} bytes: {path}")
    return path.read_text(encoding="utf-8")


def skill_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.name == "SKILL.md" else []
    if not target.is_dir():
        raise ValueError(f"path does not exist: {target}")
    return sorted(path for path in target.rglob("SKILL.md") if ".git" not in path.parts)


def position(text: str, offset: int) -> tuple[int, int, str]:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end < 0:
        end = len(text)
    return text.count("\n", 0, offset) + 1, offset - start + 1, text[start:end].strip()


def escaped_once(text: str, dollar_at: int) -> bool:
    backslashes = 0
    index = dollar_at - 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes == 1


def unresolved(name: str, root: Path, known: set[str], ignored: set[str]) -> bool:
    token = name.lstrip("/")
    if token in ignored:
        return False
    if ":" in token:
        prefix, local = token.split(":", 1)
        if prefix != root.name:
            return False  # External plugin: cannot verify locally.
    else:
        local = token
    return local not in known and local not in BUILTINS


def scan(target: Path, ignored: set[str] | None = None) -> tuple[int, list[Finding]]:
    files = skill_files(target)
    if not files:
        raise ValueError(f"no SKILL.md found under {target}")
    ignored = {name.lstrip("/") for name in (ignored or set())}
    findings: list[Finding] = []
    command_cache: dict[Path, set[str]] = {}

    for skill_file in files:
        text = read_skill(skill_file)
        root = plugin_root(skill_file)
        if root not in command_cache:
            command_cache[root] = known_commands(root)
        known = command_cache[root]
        display = str(skill_file.relative_to(target)) if target.is_dir() else skill_file.name

        for match in MONEY_PLACEHOLDER.finditer(text):
            if escaped_once(text, match.start()):
                continue
            line, column, evidence = position(text, match.start())
            findings.append(Finding(
                display, line, column, "CLAUDE_LITERAL_DOLLAR", "warning", evidence,
                f"{match.group()} may be parsed as a positional skill argument",
                "If this is a literal amount in Claude Code, prefix $ with one backslash.",
            ))

        for code in INLINE_CODE.finditer(text):
            for command in SLASH_NAME.finditer(code.group(1)):
                name = command.group("name")
                if not unresolved(name, root, known, ignored):
                    continue
                offset = code.start(1) + command.start()
                line, column, evidence = position(text, offset)
                findings.append(Finding(
                    display, line, column, "UNRESOLVED_SLASH", "warning", evidence,
                    f"/{name} has no matching skill or command in {root.name}",
                    "Confirm the runtime command, add it, or document an existing skill name.",
                ))

        # A command may be shown as a standalone line in a fenced example.
        active_fence: tuple[str, int] | None = None
        offset = 0
        for line_text in text.splitlines(keepends=True):
            fence = FENCE.match(line_text)
            if fence:
                marker = fence.group(1)
                if active_fence is None:
                    active_fence = (marker[0], len(marker))
                elif marker[0] == active_fence[0] and len(marker) >= active_fence[1]:
                    active_fence = None
            elif active_fence:
                command = SLASH_AT_START.match(line_text)
                if command and unresolved(command.group("name"), root, known, ignored):
                    command_offset = offset + command.start("name")
                    line, column, evidence = position(text, command_offset)
                    name = command.group("name")
                    findings.append(Finding(
                        display, line, column, "UNRESOLVED_SLASH", "warning", evidence,
                        f"{name} has no matching skill or command in {root.name}",
                        "Confirm the runtime command, add it, or document an existing skill name.",
                    ))
            offset += len(line_text)

    findings.sort(key=lambda item: (item.file, item.line, item.column, item.rule))
    return len(files), findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Find unresolved slash invocations and literal-dollar hazards in SKILL.md files."
    )
    parser.add_argument("command", choices=["scan"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--fail-on", choices=["warning", "none"], default="warning")
    parser.add_argument("--ignore-command", action="append", default=[], metavar="NAME")
    args = parser.parse_args(argv)
    try:
        count, findings = scan(args.path, set(args.ignore_command))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"SlashAudit: {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps({
            "skill_files": count,
            "finding_count": len(findings),
            "findings": [asdict(finding) for finding in findings],
        }, ensure_ascii=False, indent=2))
    else:
        for finding in findings:
            print(f"{finding.file}:{finding.line}:{finding.column}: "
                  f"{finding.severity} {finding.rule}: {finding.message}")
            print(f"  {finding.evidence}")
            print(f"  → {finding.suggestion}")
        print(f"Scanned {count} SKILL.md file(s); {len(findings)} warning(s).")
    return 1 if findings and args.fail_on == "warning" else 0


if __name__ == "__main__":
    raise SystemExit(main())
