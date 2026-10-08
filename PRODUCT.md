# Product brief — SlashAudit

**Value proposition:** Before publishing a Claude Code skill collection, identify two concrete cases where its written instructions may promise a command that is not shipped or show a currency value that is changed by argument substitution.

**User and job:** A skill/plugin maintainer scans a local source tree, sees file-and-line diagnostics, checks the finding, and corrects the instruction before release.

**Evidence:** Public reports in Knowledge Work Plugins [#1283](https://github.com/anthropics/knowledge-work-plugins/issues/1283) and [#1286](https://github.com/anthropics/knowledge-work-plugins/issues/1286). Demand beyond these reports is unverified.

**Non-goals:** Full skill-spec conformance, security scanning, live Claude invocation, automatic fixes, running third-party code, or claiming a warning is definitely a defect.

**Acceptance criteria:** A clean bundled example exits 0; a bundled broken example pinpoints one unresolved slash and one monetary substitution hazard and exits 1; JSON output is machine-readable; missing/unreadable input exits 2; tests run offline with Python's standard library.

**Success measure to validate later:** Whether external skill authors can confirm a true actionable finding in their own repo without being buried in false positives. No adoption or accuracy rate has been measured yet.
