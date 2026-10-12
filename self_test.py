"""Self-test for ai-commit-disclosure: functional / error-path / extreme-edge."""
from __future__ import annotations

import os
import sys
import tempfile

import disclose

_results = []


def record(family, name, ok, detail=""):
    _results.append((family, name, "PASS" if ok else "FAIL", detail))


def cmsg(sha="a1b2c3d", author="Ada Dev <ada@example.test>", subject="do thing",
         body="Body.", trailers=("Signed-off-by: Ada Dev <ada@example.test>",)):
    lines = ["commit %s" % sha, "Author: %s" % author, "AuthorDate:   Mon Oct 5 10:00:00 2026 +0000",
             "", "    %s" % subject, "", body]
    lines += list(trailers)
    return "\n".join(lines) + "\n"


def log(*msgs):
    return "\n".join(msgs)


# ---------------------------------------------------------------- functional

def t_functional(tmp):
    r = disclose.audit(log(cmsg()))
    record("functional", "plain human commit -> human", r["human"] == 1 and r["ai_involved"] == 0)

    r = disclose.audit(log(cmsg(trailers=("AI-assisted: yes",))))
    record("functional", "AI-assisted: yes -> disclosed_ai", r["disclosed_ai"] == 1)

    r = disclose.audit(log(cmsg(trailers=("Co-authored-by: AI Assistant <noreply@example.test>",))))
    record("functional", "AI-looking co-author -> undeclared_suspect",
           r["undeclared_suspect"] == 1 and r["missing_disclosure"] == ["a1b2c3d"])

    r = disclose.audit(log(cmsg(trailers=("AI-assisted: yes",
                                          "Co-authored-by: AI Assistant <noreply@example.test>"))))
    record("functional", "AI co-author + disclosure -> disclosed_ai", r["disclosed_ai"] == 1)

    r = disclose.audit(log(cmsg(trailers=("Generated-by: Claude <noreply@example.test>",))))
    record("functional", "Generated-by marker -> disclosed_ai", r["disclosed_ai"] == 1)

    r = disclose.audit(log(cmsg(trailers=("Assisted-by: claude",))))
    record("functional", "Assisted-by marker -> disclosed_ai", r["disclosed_ai"] == 1)

    r = disclose.audit(log(cmsg(trailers=("AI-assisted: no",))))
    record("functional", "AI-assisted: no is not AI involvement", r["human"] == 1)

    r = disclose.audit(log(cmsg(author="Copilot Agent <bot@example.test>")))
    record("functional", "AI-looking author name -> suspect",
           r["undeclared_suspect"] == 1 and any("author" in x for x in r["commits"][0]["reasons"]))

    r = disclose.audit(log(cmsg(trailers=("Co-authored-by: Bob <bob@example.test>",))))
    record("functional", "human co-author is not AI", r["human"] == 1)

    a = disclose.audit(log(cmsg(trailers=("AI-assisted: yes",)), cmsg()))
    record("functional", "disclosure rate 1/1 AI-involved = 1.0",
           a["ai_involved"] == 1 and a["disclosure_rate"] == 1.0)

    a = disclose.audit(log(cmsg(trailers=("Co-authored-by: AI Bot <a@x.test>",)),
                           cmsg(sha="b222222", trailers=("AI-assisted: yes",)),
                           cmsg(sha="c333333")))
    record("functional", "rate math + missing list on 3-commit log",
           a["total"] == 3 and a["ai_involved"] == 2 and a["disclosure_rate"] == 0.5
           and a["missing_disclosure"] == ["a1b2c3d"])

    rec = disclose.audit(log(cmsg(), cmsg(sha="bbbbbbb", author="Copilot <c@x.test>")))
    record("functional", "gate verdict FAIL on suspect, PASS otherwise",
           disclose.gate_verdict(rec) == "FAIL"
           and disclose.gate_verdict(disclose.audit(log(cmsg()))) == "PASS")

    c = disclose.parse_commit(cmsg())
    record("functional", "subject/sha/date/trailers extracted",
           c["sha"] == "a1b2c3d" and c["subject"] == "do thing" and c["date"].startswith("Mon")
           and any(t["key"] == "signed-off-by" for t in c["trailers"]))


# ---------------------------------------------------------------- error paths

def t_error_paths(tmp):
    r = disclose.audit("")
    record("error", "empty input -> zero commits, rate 1.0",
           r["total"] == 0 and r["disclosure_rate"] == 1.0)

    r = disclose.audit("random words\nno structure at all\n")
    record("error", "headerless text treated as one unclassifiable commit",
           r["total"] == 1 and r["human"] == 1)

    r = disclose.audit(log(cmsg(trailers=("Signed-off-by no colon here",))))
    record("error", "malformed trailer ignored, no crash", r["total"] == 1)

    r = disclose.audit(log(cmsg(sha="")))
    record("error", "commit without sha -> placeholder in missing list",
           isinstance(r, dict))

    r = disclose.audit("\n\n\ncommit deadbee\n\n\n\nAuthor: X <x@x.test>\n\n    subj\n\nbody\n")
    record("error", "excess blank lines tolerated", r["total"] == 1 and r["commits"][0]["sha"] == "deadbee")

    r = disclose.audit(log(cmsg(trailers=("AI-assisted:",))))
    record("error", "empty trailer value handled", isinstance(r, dict) and r["total"] == 1)

    p = os.path.join(tmp, "garbage.log")
    with open(p, "w", encoding="utf-8", errors="replace") as f:
        f.write("\x00\x01\x02 commit cafe123 \x7f\nAuthor: Ai Bot <a@x.test>\n")
    r = disclose.audit_file(p)
    record("error", "control-char garbage still parses, AI author flagged",
           r["undeclared_suspect"] == 1)


# ---------------------------------------------------------------- extreme edges

def t_extreme_edges(tmp):
    r = disclose.audit(log(cmsg(body="x" * 100000)))
    record("edge", "100KB body handled", r["total"] == 1 and r["human"] == 1)

    big = log(*[cmsg(sha="%07d" % i, trailers=("AI-assisted: yes" if i % 2 else "AI-assisted: no",))
                for i in range(200)])
    r = disclose.audit(big)
    record("edge", "200 commits, alternating disclosure",
           r["total"] == 200 and r["disclosed_ai"] == 100 and r["human"] == 100)

    r = disclose.audit(log(cmsg(author="\u00c4da D\u00e9v <ada@x.test>",
                                trailers=("Co-authored-by: \u00c5ssistant Bot <bot@x.test>",))))
    record("edge", "unicode names parsed, AI bot still flagged",
           r["undeclared_suspect"] == 1)

    crlf = log(cmsg()).replace("\n", "\r\n")
    r = disclose.audit(crlf)
    record("edge", "CRLF log handled", r["total"] == 1 and r["human"] == 1)

    r = disclose.audit(log(cmsg(trailers=("Signed-off-by: Ada <ada@x.test>", "X-Trailer: " + "y" * 50000))))
    record("edge", "50KB single trailer tolerated", r["total"] == 1)

    rec = disclose.looks_ai_identity("Botello Rodriguez <botello@x.test>")
    record("edge", "name merely containing 'bot' substring not matched by word-boundary patterns",
           rec is False)

    r = disclose.audit(log(cmsg(trailers=("co-authored-by: AI Assistant <a@x.test>",))))
    record("edge", "lowercase trailer key recognized", r["undeclared_suspect"] == 1)

    r = disclose.audit(log(cmsg(trailers=("AI-ASSISTED: yes",))))
    record("edge", "uppercase disclosure key recognized", r["disclosed_ai"] == 1)

    custom = [r"\bzorp\b"]
    r = disclose.audit(log(cmsg(trailers=("Co-authored-by: Zorp Unit <z@x.test>",))), ai_patterns=custom)
    record("edge", "custom AI-pattern list honored", r["undeclared_suspect"] == 1)

    p = os.path.join(tmp, "many.log")
    with open(p, "w", encoding="utf-8") as f:
        f.write(log(*[cmsg(sha="%07d" % i) for i in range(50)]))
    r = disclose.audit_file(p)
    record("edge", "audit_file reads 50-commit dump", r["total"] == 50)

    d = os.path.join(tmp, "dumpdir")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "one.log"), "w", encoding="utf-8") as f:
        f.write(log(cmsg(trailers=("AI-assisted: yes",))))
    with open(os.path.join(d, "two.txt"), "w", encoding="utf-8") as f:
        f.write(log(cmsg(sha="9999999", trailers=("Co-authored-by: AI Bot <b@x.test>",))))
    r = disclose.audit_dir(d)
    record("edge", "audit_dir merges .log+.txt files", r["total"] == 2
           and r["disclosed_ai"] == 1 and r["undeclared_suspect"] == 1)

    r = disclose.audit(log(cmsg(trailers=("Generated-by: DeepSeek-R1", "Generated-by: GPT-5"))))
    record("edge", "multiple disclosure trailers count once",
           r["disclosed_ai"] == 1 and len(r["commits"][0]["reasons"]) == 2)

    # ---- round-2 additions: generic AI identities, CLI, date extraction ----

    r = disclose.audit(log(cmsg(trailers=("Co-authored-by: AI Bot <b@x.test>",))))
    record("edge", "generic 'AI Bot' co-author detected (round-2 bugfix)", r["undeclared_suspect"] == 1)

    r = disclose.audit(log(cmsg(trailers=("Co-authored-by: Build Bot <b@x.test>",))))
    record("edge", "standalone word 'bot' matches, 'Botello' does not",
           r["undeclared_suspect"] == 1
           and disclose.looks_ai_identity("Botello <b@x.test>") is False)

    r = disclose.audit(log(cmsg(author="DeepSeek Agent <d@x.test>",
                                trailers=("AI-assisted: yes",))))
    record("functional", "AI author with disclosure still disclosed_ai", r["disclosed_ai"] == 1)

    import cli as cli_mod
    import io
    from contextlib import redirect_stdout
    good = os.path.join(tmp, "g.log")
    bad = os.path.join(tmp, "b.log")
    with open(good, "w", encoding="utf-8") as f:
        f.write(log(cmsg()))
    with open(bad, "w", encoding="utf-8") as f:
        f.write(log(cmsg(trailers=("Co-authored-by: AI Bot <b@x.test>",))))
    def run_cli(*argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            return cli_mod.main(list(argv))
    record("edge", "cli check clean -> 0", run_cli("check", good) == 0)
    record("edge", "cli check suspect -> 1", run_cli("check", bad) == 1)
    record("edge", "cli report always -> 0", run_cli("report", bad) == 0)
    record("edge", "cli --json parses", run_cli("report", good, "--json") == 0)
    record("edge", "cli missing path -> exit 2", run_cli("check", "__nope__.log") == 2)

    c = disclose.parse_commit(cmsg())
    record("functional", "AuthorDate extracted from fuller format", c["date"].startswith("Mon Oct 5"))

    r = disclose.audit(log(cmsg(trailers=("AI-assisted: YES",))))
    record("edge", "uppercase YES disclosure value accepted", r["disclosed_ai"] == 1)

    r = disclose.audit(log(cmsg(trailers=("Co-authored-by: gemini <g@x.test>",))))
    record("edge", "model name as co-author display name flagged", r["undeclared_suspect"] == 1)


def main():
    tmp = tempfile.mkdtemp(prefix="aidisclose_test_")
    try:
        t_functional(tmp)
        t_error_paths(tmp)
        t_extreme_edges(tmp)
    finally:
        for root, _, files in os.walk(tmp, topdown=False):
            for f in files:
                try:
                    os.unlink(os.path.join(root, f))
                except OSError:
                    pass
            try:
                os.rmdir(root)
            except OSError:
                pass
    fails = [r for r in _results if r[2] == "FAIL"]
    for fam, name, status, detail in _results:
        print("[%s] %-10s %s%s" % (status, fam, name, (" | " + detail) if detail else ""))
    print("\n%d checks, %d failed" % (len(_results), len(fails)))
    print("SUMMARY: PASS %d/%d" % (len(_results) - len(fails), len(_results)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
