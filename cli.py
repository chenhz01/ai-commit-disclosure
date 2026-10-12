"""CLI for ai-commit-disclosure."""
import argparse
import json
import sys

import disclose


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ai-commit-disclosure",
                                 description="Audit git logs for AI-contribution disclosure hygiene and report the disclosure rate.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="gate: FAIL if any AI-looking commit lacks disclosure")
    p_check.add_argument("inputs", nargs="+", help="git log dumps (.txt/.log) or directories")
    p_check.add_argument("--json", action="store_true")

    p_rep = sub.add_parser("report", help="disclosure-rate report, no gate")
    p_rep.add_argument("inputs", nargs="+")
    p_rep.add_argument("--json", action="store_true")

    args = ap.parse_args(argv)

    def run_report(inputs):
        reports = []
        for p in inputs:
            import os
            if os.path.isdir(p):
                reports.append(disclose.audit_dir(p))
            elif os.path.exists(p):
                reports.append(disclose.audit_file(p))
            else:
                print("error: path not found: %s" % p, file=sys.stderr)
                return None
        return merge(reports)

    def merge(reports):
        if len(reports) == 1:
            return reports[0]
        m = {k: reports[0][k] for k in ("total", "disclosed_ai", "undeclared_suspect",
                                        "human", "ai_involved")}
        for r in reports[1:]:
            for k in m:
                m[k] += r[k]
        rate = m["disclosed_ai"] / m["ai_involved"] if m["ai_involved"] else 1.0
        m["disclosure_rate"] = round(rate, 4)
        m["missing_disclosure"] = [s for r in reports for s in r["missing_disclosure"]]
        m["commits"] = [c for r in reports for c in r["commits"]]
        return m

    rep = run_report(args.inputs)
    if rep is None:
        return 2
    if args.json:
        print(json.dumps(rep, indent=2, ensure_ascii=False))
    else:
        print("commits: %d | AI-involved: %d | disclosed: %d | undeclared suspects: %d"
              % (rep["total"], rep["ai_involved"], rep["disclosed_ai"],
                 rep["undeclared_suspect"]))
        print("disclosure rate: %.1f%%" % (rep["disclosure_rate"] * 100))
        for sha in rep["missing_disclosure"]:
            print("  MISSING disclosure: %s" % sha)
    if args.cmd == "check":
        v = disclose.gate_verdict(rep)
        print("verdict: %s" % v)
        return 1 if v == "FAIL" else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
