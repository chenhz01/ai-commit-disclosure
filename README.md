# ai-commit-disclosure

An offline auditor that reads `git log --format=fuller` output and answers one management question: of the commits that look AI-involved, how many actually said so? It flags AI-looking identities (authors, co-author trailers, model-name trailers), separates *disclosed* from *undeclared suspects*, and reports a disclosure rate — so disclosure policy can be measured instead of assumed.

**Confidence: High (85%)** that the marker set covers how AI involvement actually shows up in commit metadata today (disclosure trailers plus AI-looking identities); **Medium (55%)** that the identity heuristics keep false positives low on your contributor base — the pattern list is configurable precisely because "AI"/"bot" word matching will nick edge cases [estimated].

## Problem

AI-attribution *tooling* is booming — every assistant now stamps its commits — but attribution *auditing* is not: once the stamps are on, nothing tells a maintainer what fraction of AI-involved commits carry them, or which commits look AI-touched yet disclose nothing. Existing anchors solve the wrong half of the loop: heios/ai-commit-attribution (0★ as of 2026-10-11) is research on *how to word* attribution trailers, JasonSongHoho/jetbrains-ai-commit-attribution (0★) is an IDE plugin that *adds* a commit option in GoLand, and bcmyguest/assisted-by (2★) *enforces* one specific trailer via a Claude Code plugin — all three write attribution; none reads history back and reports the disclosure rate.

## How it works

Feed it a `git log --format=fuller` dump (or raw messages separated by `commit <sha>` lines). No git, no network — pure text analysis. Each commit is classified:

| Label | Meaning |
|---|---|
| `disclosed_ai` | a disclosure trailer exists (`AI-assisted:`, `Generated-by:`, `Assisted-by:`, `AI-generated:`) with a truthy value, or any AI-looking identity is paired with one |
| `undeclared_suspect` | an AI-looking identity appears — author name, or a `Co-authored-by:` identity matching the configurable pattern list (`ai`, `bot`, `copilot`, `llm`, `claude`, `gpt`, `gemini`, `deepseek`, `codex`, `cursor`, …) — with no disclosure trailer |
| `human` | nothing AI-looking detected |

The report emits totals, per-commit reasons, a `missing_disclosure` sha list, and `disclosure_rate = disclosed / (disclosed + suspects)`. `check` subcommand gates (exit 1 on any suspect); `report` subcommand just measures. `AI-assisted: no` is honored as a negative, not counted as involvement.

## Quickstart (~2 min)

```bash
# 1. Self-test: 43 checks, functional / error-path / extreme-edge (~2 s)
python self_test.py

# 2. Measure your own history
git log --format=fuller -200 > mylog.txt
python cli.py report mylog.txt                 # disclosure rate + missing list
python cli.py check mylog.txt                  # gate: exit 1 if suspects exist
python cli.py report mylog.txt --json          # machine-readable
```

## Why not X

| Alternative | Why not |
|---|---|
| heios/ai-commit-attribution (0★) | Research on attribution wording ("Co-authored-by" vs "Assisted-by") — it informs *policy text*, does not parse logs or produce a disclosure rate |
| JasonSongHoho/jetbrains-ai-commit-attribution (0★) | IDE-only (GoLand) commit-time helper; adds attribution but never audits what actually landed, and requires the IDE |
| bcmyguest/assisted-by (2★) | Enforces one trailer dialect at commit time via a Claude Code plugin; no rate reporting, no suspect detection for commits written outside its hook |
| DCO / commit-signing bots | Verify sign-off presence, are blind to AI disclosure entirely |
| grep one-liners over `git log` | Miss trailer structure, can't express "AI-looking identity without disclosure", no rate math |

## Minimal Fallback (PLAN B)

No Python? The policy is two greps: `grep -iE "co-authored-by.*(ai|bot|copilot|llm|gpt|claude)"` finds AI-looking co-authors; intersect with `grep -iv "AI-assisted"` per commit block to list suspects. The JSON report schema in this repo is the contract a re-implementation must emit.

## Design Trade-offs

Priority order: **low false-accusation > detection recall > convenience**. The identity matcher is word-boundary regex on names — it will miss a co-author named "Elena" that happens to be a bot and may false-flag a human literally named "Ai"; the list is configurable per run for exactly this reason. Disclosure trailers are trusted at face value ("yes" means disclosed) — this measures *transparency*, not *truthfulness*; someone can write `AI-assisted: no` over AI work and pass. Commits with short hashes (<7 hex) are not recognized as separators by design; feed real `--format=fuller` output.

## Limits & Second-order Effects

- It reads only commit metadata: AI code committed under a human identity with no AI co-author trailer is invisible — the tool measures disclosed involvement, not true involvement.
- Pattern-list tightening invites gaming ("rename the bot to 'Reviewer'"), the same arms race as email spam filters; the countermeasure is sampling diffs, which is out of scope.
- Publishing per-team disclosure rates may pressure contributors into performative `AI-assisted: no` stamps — measure but don't leaderboard.
- `AI-assisted: no` normalizing into a meaningless ritual is a real second-order risk; treat rate drops below historical baseline as the signal, not individual commits.

## FAQ

**Does it connect to git or any API?** Never. Input is text you paste or dump; that keeps it CI-portable and air-gap-safe.

**Why is `disclosure_rate` 1.0 when nothing looks AI-involved?** Vacuous truth: no suspects means nothing to disclose. It reads as "no undeclared AI involvement found", not "no AI used".

**When NOT to use this?** Don't use it as evidence in individual contributor disputes — name heuristics are probabilistic and the output is explicitly at audit granularity. Don't use it on solo repos (nothing to audit). And don't use it as a security control: disclosure hygiene is process compliance, not provenance verification (that needs signed commits).

**Can I enforce one specific trailer dialect (e.g. only `Assisted-by:`)?** Yes — narrow `DISCLOSURE_KEYS` in one line; the auditor will then report the other dialects as suspects, which is the policy you asked for.

## [Core Assumptions]

1. AI involvement leaves traces in commit metadata (identities, trailers) often enough for a rate metric to be meaningful; fully-laundered AI contributions are undetectable here.
2. A configurable word-boundary pattern list is an acceptable identity heuristic at audit granularity — false positives are an accepted, tunable cost.
3. Disclosure trailer values are truthful claims; the tool audits transparency, not veracity.
4. `git log --format=fuller` is the canonical input substrate; other formats need a shim, not a rewrite.

*Data as of 2026-10-11. Measured: 43/43 self-test checks PASS (functional 16, error paths 7, extreme edges 20), repro `python self_test.py` on Windows 10 / CPython 3.11. False-positive behavior of identity patterns on real contributor bases is [estimated].*

---

Part of the [zhengming-toolbox](https://github.com/chenhz01/zhengming-toolbox) — 55 purpose-built AI-engineering tools across neglected niches.

Related tools: [lockfile-audit-diff](https://github.com/chenhz01/lockfile-audit-diff) · [money-precision-check](https://github.com/chenhz01/money-precision-check) · [unit-confusion-check](https://github.com/chenhz01/unit-confusion-check)
