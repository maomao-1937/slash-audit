from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from slash_audit import main, scan


class SlashAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def skill(self, name: str, body: str) -> Path:
        path = self.root / "finance" / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def test_finds_unresolved_command_and_literal_amount(self) -> None:
        self.skill("ledger", "---\nname: ledger\ndescription: Keep a ledger\n---\n"
                   "Run `/missing <month>` and show Balance: $0.00.\n")
        count, findings = scan(self.root)
        self.assertEqual(count, 1)
        self.assertEqual({item.rule for item in findings},
                         {"UNRESOLVED_SLASH", "CLAUDE_LITERAL_DOLLAR"})
        self.assertEqual({item.line for item in findings}, {5})

    def test_recognizes_skill_names_namespace_and_escaped_money(self) -> None:
        self.skill("ledger", "---\nname: ledger\ndescription: Keep a ledger\n---\n"
                   "Run `/ledger`, `/finance:ledger`, `/help`; show \\$10,000.\n")
        _, findings = scan(self.root)
        self.assertEqual(findings, [])

    def test_double_backslash_does_not_hide_substitution(self) -> None:
        self.skill("ledger", "---\nname: ledger\n---\nValue: \\\\$1.00\n")
        _, findings = scan(self.root)
        self.assertEqual([finding.rule for finding in findings],
                         ["CLAUDE_LITERAL_DOLLAR"])

    def test_paths_urls_and_external_plugins_are_not_local_commands(self) -> None:
        self.skill("ledger", "---\nname: ledger\n---\n"
                   "See `https://example.invalid/help`, `/app/data`, and `/other:check`.\n")
        _, findings = scan(self.root)
        self.assertEqual(findings, [])

    def test_real_command_file_and_ignore_option(self) -> None:
        self.skill("ledger", "---\nname: ledger\n---\nRun `/close` and `/custom`.\n")
        command = self.root / "finance" / "commands" / "close.md"
        command.parent.mkdir(parents=True)
        command.write_text("Close books.\n", encoding="utf-8")
        _, findings = scan(self.root, {"custom"})
        self.assertEqual(findings, [])

    def test_fenced_command_example_is_checked(self) -> None:
        self.skill("ledger", "---\nname: ledger\n---\nRun:\n```text\n/ghost <month>\n```\n")
        _, findings = scan(self.root)
        self.assertEqual([(finding.rule, finding.line) for finding in findings],
                         [("UNRESOLVED_SLASH", 6)])

    def test_standalone_skill_can_reference_its_own_name(self) -> None:
        path = self.root / "my-skill" / "SKILL.md"
        path.parent.mkdir()
        path.write_text("---\nname: fancy\n---\nRun `/fancy`.\n", encoding="utf-8")
        _, findings = scan(path)
        self.assertEqual(findings, [])

    def test_json_cli_and_exit_status(self) -> None:
        self.skill("ledger", "---\nname: ledger\n---\nRun `/missing`.\n")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["scan", str(self.root), "--format", "json"])
        self.assertEqual(status, 1)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["skill_files"], 1)
        self.assertEqual(payload["findings"][0]["rule"], "UNRESOLVED_SLASH")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["scan", str(self.root), "--fail-on", "none"]), 0)

    def test_empty_target_fails_closed(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["scan", str(self.root)]), 2)


if __name__ == "__main__":
    unittest.main()
