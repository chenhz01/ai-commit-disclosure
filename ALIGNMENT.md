# Alignment Audit (Rules 85-100 / 16 items) — ai-commit-disclosure

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Safety/Ethics section | N/A | Read-only commit-text auditor; no offensive content; misuse (naming individuals) discouraged in FAQ/Limits. |
| 2 | Privacy/keys | PASS | No keys/tokens/real names; all identities are example.test placeholders; no network, no git invocation. |
| 3 | Copyright boundary | PASS | Anchor repos referenced factually (name, stars as of 2026-10-11, one-layer difference); no anchor text copied; MIT LICENSE shipped. |
| 4 | Fact-check numbers | PASS | 43/43 checks measured, repro command given; false-positive adequacy marked [estimated]. |
| 5 | Confidence grading | PASS | README: High (85%) marker coverage, Medium (55%) heuristic FP behavior, each with basis sentence. |
| 6 | Minimal Fallback | PASS | "Minimal Fallback (PLAN B)": two-grep policy; JSON report schema is the contract. |
| 7 | Quickstart timing | PASS | Quickstart labelled ~2 min, staged (self-test → own history → gate/JSON). |
| 8 | Conflict arbitration | PASS | "Design Trade-offs": low false-accusation > detection recall > convenience, with named costs. |
| 9 | Changelog ≥2 iterations | PASS | v0.1.0 → v0.1.1: generic-AI-identity detection bugfix, separator constraint documented, CLI error-path TypeError fix, 32→43 tests. |
| 10 | Exemption (session rule) | N/A | Session-level governance item; static repo not applicable. |
| 11 | Knowledge cutoff | PASS | Anchor star counts and tool landscape dated "as of 2026-10-11" in Problem. |
| 12 | Explicit assumptions | PASS | `[Core Assumptions]` lists 4 premises (metadata traces, heuristic acceptability, truthfulness of trailers, fuller-format substrate). |
| 13 | Three-part self-test | PASS | functional (16) + error paths (7) + extreme edges (20) = 43/43 PASS. |
| 14 | Socratic FAQ | PASS | "When NOT to use this?" — contributor disputes, solo repos, security-control mis-expectation. |
| 15 | Pareto iteration | PASS | Round 2: test count +34% (32→43), one real detection bug + one CLI crash fixed; CHANGELOG-traceable. |
| 16 | ≤60-word opening | PASS | First paragraph is 58 words ending with a judgment sentence ("measured instead of assumed"). |

Additional: **Second-order effects** — "Limits & Second-order Effects" covers laundered AI contributions, rename-gaming, performative stamps, and ritualization of `AI-assisted: no`.
