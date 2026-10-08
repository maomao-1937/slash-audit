# SlashAudit

A tiny, read-only check for promises inside Claude Code `SKILL.md` files. It looks for two easy-to-miss problems before a skill is shared:

1. An inline slash invocation such as `/close-books` that has no matching local skill or command.
2. A currency example such as `$5.00` that Claude Code may interpret as a positional argument placeholder.

This is **not** a general Agent Skills spec validator, security scanner, or proof that a command works at runtime. It complements broader tools by checking a narrow user-facing failure mode. It never executes skill content, changes files, calls an API, or needs a key.

## Who it is for

Plugin and skill authors who document slash commands or include literal money amounts in Claude Code skills. The first pass is useful before publishing a plugin or as a CI check on a skill collection.

## Run in 30 seconds

Requires Python 3.9+; no third-party dependencies. The included tests were run with Python 3.9.6.

```bash
python3 slash_audit.py scan examples/broken
```

Expected result: two warnings (`UNRESOLVED_SLASH` and `CLAUDE_LITERAL_DOLLAR`) and exit code `1`. Compare with a clean example:

```bash
python3 slash_audit.py scan examples/healthy
```

The clean example reports zero warnings and exits `0`. Scan your own local tree:

```bash
python3 slash_audit.py scan /path/to/plugin-or-skill-repo
python3 slash_audit.py scan /path/to/plugin-or-skill-repo --format json
python3 slash_audit.py scan /path/to/plugin-or-skill-repo --ignore-command /my-runtime-command
```

`--ignore-command` is repeatable for commands supplied by the runtime but absent from the scanned tree. The default exits `1` for warnings, `0` when clean, and `2` for unreadable input or no `SKILL.md`. Use `--fail-on none` for an advisory-only run.

## What the checks mean

`UNRESOLVED_SLASH` checks slash-like invocations inside inline code or at the beginning of fenced example lines against sibling `skills/*/SKILL.md` and `commands/**/*.md`. It understands the current plugin namespace (for example `/finance:reconcile`), common Claude built-ins, and skips external plugin names it cannot verify locally. A warning is a **candidate mismatch**, not proof of a broken command: aliases, generated commands, custom runtimes and nonstandard layouts can be valid.

`CLAUDE_LITERAL_DOLLAR` detects amounts like `$5.00` or `$10,000` in skill content. [Claude Code's skill documentation](https://code.claude.com/docs/en/skills#available-string-substitutions) says `$N` is positional substitution and a literal dollar before a digit needs one preceding backslash. The scanner treats exactly one backslash as escaped; two backslashes do not suppress the warning. This rule applies to Claude Code semantics, not every Agent Skills host.

The scanner intentionally does not parse arbitrary YAML, infer semantic intent, execute commands, inspect remote dependencies, or promise zero false positives. It reads only local `SKILL.md` files up to 2 MiB each. Review warnings before changing your skill.

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile slash_audit.py
```

The tests cover missing and valid commands, plugin namespaces, built-ins, paths/URLs, escaped and double-escaped money, JSON output, exit codes, and empty input.

## Why this exists

[A Knowledge Work Plugins issue](https://github.com/anthropics/knowledge-work-plugins/issues/1283) reports skills referring to slash commands the plugin does not ship. [Another issue](https://github.com/anthropics/knowledge-work-plugins/issues/1286) reports literal amounts colliding with positional substitutions. Those are concrete problem reports, not proof this tool has been adopted or tested by those maintainers. See [research notes](docs/research.md) for the alternatives considered and existing validators.

In a read-only scan of a temporary clone on 2026-10-08, SlashAudit found the reported `/je`, `/sox`, `/flux`, and monetary examples in the `finance/` skills. Those are candidate text findings, not an independent Claude Code runtime reproduction.

## License

MIT; see [LICENSE](LICENSE). No source or prompt text from the referenced projects is included.
