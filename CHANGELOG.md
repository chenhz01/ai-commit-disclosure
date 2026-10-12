# Changelog

## [0.1.1] - 2026-10-11

### Changed (round-2 iteration after first-draft self-audit)

- **Correctness:** fixed a real detection gap the expanded suite exposed — generic AI identities like `AI Bot` / `Build Bot` (no assistant/copilot/model token) were silently classified `human`; pattern list widened with word-boundary `\bai\b` and `\bbot\b` while keeping `Botello`-style human names unmatched (new test pins both sides).
- **Correctness:** commit-block separator now documented as ≥7 hex chars; a 5-char test sha silently merged two commits into one, masking detection — test fixed to realistic short-hash shape and the constraint written into Design Trade-offs.
- **Robustness:** CLI error path restructured — path-not-found returned an int sentinel that was then consumed as a report dict (`TypeError`); run now returns 2 cleanly, and the five CLI tests suppress stdout so JSON noise no longer leaks into test output.
- **Test rigor (+34%):** suite grew 32 → 43 checks; fixture corrected to real `--format=fuller` shape (`AuthorDate:`), uppercase `YES` disclosure values and model-name co-authors now covered.

## [0.1.0] - 2026-10-11

### Added

- `disclose.py`: git-log text parser (commit split, author/date/subject/trailer extraction), three-way classification (disclosed_ai / undeclared_suspect / human), configurable AI-identity pattern list, disclosure-rate report with missing-disclosure sha list, file/dir/batch auditing, gate verdict.
- `cli.py`: `check` (gate, exit 1 on suspects) and `report` (measure only) subcommands, `--json`; exit codes 0/1/2.
- `self_test.py`: three families — functional, error paths, extreme edges (100KB bodies, 200-commit logs, unicode identities, CRLF, 50KB trailers, custom pattern lists).
- MIT LICENSE (zhengming contributors), README, initial ALIGNMENT audit.
