# Selection record — 2026-10-08 (Asia/Shanghai)

This is a small, evidence-led product experiment, not a claim of unmet market demand. The GitHub discovery snapshot was taken at 2026-10-08 02:04 UTC; its star deltas compare with a snapshot at 01:17 UTC, **not** with a full prior day. One radar topic query returned HTTP 403, so star movement was not used to choose the idea. RSS coverage was empty. Sources below were read on 2026-10-08.

## Sources and what each contributed

- [Anthropic Knowledge Work Plugins issue #1283](https://github.com/anthropics/knowledge-work-plugins/issues/1283): a concrete report of documented slash commands missing from the plugin, plus overlapping skill descriptions. Informs the narrow command-inventory check. Repository license metadata: Apache-2.0.
- [Anthropic Knowledge Work Plugins issue #1286](https://github.com/anthropics/knowledge-work-plugins/issues/1286): concrete `$N` substitution collision in monetary examples. Informs the literal-dollar check. [Official Claude Code documentation](https://code.claude.com/docs/en/skills#available-string-substitutions) defines the substitution and escape behavior.
- [Agency Agents startup MVP workflow](https://github.com/msitarzewski/agency-agents/blob/main/examples/workflow-startup-mvp.md): emphasizes evidence-based quality gates and realistic scoping; used as a decision/checking lens, not as runtime code or agent prompts. Repository license metadata: MIT.
- [agent-ecosystem/skill-validator](https://github.com/agent-ecosystem/skill-validator), discovered in today's search: already checks structure, links, content density and more. It is a comparator, showing why another broad spec linter would be redundant. Repository license metadata: MIT.
- [blackwell-systems/agentskills-cli](https://github.com/blackwell-systems/agentskills-cli): another comparator focused on spec conformance and progressive disclosure. License metadata was unavailable via the GitHub API, so no code was reused.

No code or long prompt text from any source was copied. Source links document inspiration and constraints, not endorsements.

## Five candidate ideas (heuristic 1–5 scores)

Scores are judgments, not measured user demand. Columns: user value / evidence / differentiation / one-day feasibility / demo clarity.

| Idea | Target user → scene → current alternative → minimum loop | Score | Decision |
| --- | --- | --- | --- | --- |
| SlashAudit | Skill author → pre-release check → manual review or broad linter → scan, locate, correct two runtime promise hazards | 4/5/4/5/5 = 23 | Chosen: two documented failure reports, narrow scope, offline demo. |
| Handoff Ledger | Multi-agent workflow designer → verify a handoff includes inputs, outputs and acceptance evidence → manual checklist → validate handoff manifest | 3/2/3/4/4 = 16 | Agency workflow suggests a pattern, but no independent failure report found. |
| MCP Citation Envelope | MCP tool author → return sources without host-specific callback → custom host integration → normalize result metadata | 5/3/4/2/3 = 17 | Adjacent to [Open WebUI #32041](https://github.com/open-webui/open-webui/issues/32041), but needs host integration and more time. |
| README Runbook Probe | OSS maintainer → verify copy-paste setup commands → manually run README → safe scripted command review | 4/3/2/2/3 = 14 | Execution/sandbox design is too risky for a one-day MVP; existing docs test tools exist. |
| Skill Overlap Explorer | Plugin author → distinguish near-identical trigger descriptions → manual comparison → show likely overlaps | 3/3/2/4/4 = 16 | The #1283 report mentions overlap, but [skill-check](https://github.com/thedaviddias/skill-check) and other validators already cover similar quality checks. |

The remaining user-demand hypothesis: authors will run a focused pre-publish check for these specific mistakes even if they already use a general skill validator. That must be tested with real users later.

## Read-only field check

After implementing the MVP, a temporary shallow clone of Knowledge Work Plugins was scanned on 2026-10-08. The `finance/` folder contained 8 `SKILL.md` files. SlashAudit emitted 13 **candidate warnings**: it found `/je` at `journal-entry/SKILL.md:18`, `/sox` at `sox-testing/SKILL.md:18`, `/flux` at `financial-statements/SKILL.md:175`, and the four monetary examples named in issue #1286. Six further monetary examples were flagged in `variance-analysis/SKILL.md`. This confirms the tool locates the documented text patterns in a real source tree; it does **not** establish that every warning has a runtime impact, that maintainers accept the diagnosis, or that the tool has external users.
