"""CLI of the MATLAB integration.

    python -m vdsim.matlab convert datei.m --to python|cpp|rust|all --out ordner [--function f] [--force]
    python -m vdsim.matlab analyze datei.m [--json] [--dot dataflow|calls] [--latex]
    python -m vdsim.matlab run datei.m 1.0 2.0 ...        (interpreter, scalar arguments)
    python -m vdsim.matlab toolchains
"""

from __future__ import annotations

import argparse
import json
import sys


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(prog="python -m vdsim.matlab", description="MATLAB-Import, Analyse und Konvertierung")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("convert", help="MATLAB nach Python/C++/Rust konvertieren")
    c.add_argument("file")
    c.add_argument("--to", default="all", choices=["python", "cpp", "rust", "all"])
    c.add_argument("--out", default=".")
    c.add_argument("--function", default=None)
    c.add_argument("--force", action="store_true", help="auch bei Fehlern schreiben")
    a = sub.add_parser("analyze", help="Regellogik analysieren")
    a.add_argument("file")
    a.add_argument("--json", action="store_true")
    a.add_argument("--dot", choices=["dataflow", "calls"])
    a.add_argument("--latex", action="store_true", help="Zuweisungen als LaTeX ausgeben")
    a.add_argument("--function", default=None)
    r = sub.add_parser("run", help="Funktion im Interpreter ausführen")
    r.add_argument("file")
    r.add_argument("args", nargs="*", type=float)
    r.add_argument("--function", default=None)
    sub.add_parser("toolchains", help="gefundene Compiler anzeigen")
    ns = ap.parse_args(argv)

    from .errors import MatlabError
    try:
        if ns.cmd == "convert":
            from .convert import convert_file
            results = convert_file(ns.file, ns.to, ns.out, function=ns.function, force=ns.force)
            failed = False
            for t, code in results.items():
                state = "OK" if code.ok else "FEHLER"
                print(f"{t}: {state} -> {', '.join(code.files) if (code.ok or ns.force) else 'nicht geschrieben'}")
                for d in code.diagnostics:
                    print("  " + str(d))
                failed |= not code.ok
            return 1 if failed else 0
        if ns.cmd == "analyze":
            from .analysis import analyze
            res = analyze(ns.file)
            if ns.json:
                print(res.to_json())
            elif ns.dot:
                print(res.to_dot(ns.dot, ns.function))
            elif ns.latex:
                for a in res.function(ns.function).assignments:
                    eq = f"  ({', '.join(a['equations'])})" if a["equations"] else ""
                    print(f"Z. {a['line']:>3}: {a['latex']}{eq}")
            else:
                print(res.summary())
            return 0
        if ns.cmd == "run":
            from .interpreter import Interpreter
            out = Interpreter.from_file(ns.file).call(ns.function, *ns.args)
            print(out)
            return 0
        if ns.cmd == "toolchains":
            from .toolchains import available, probe_cpp, probe_rust_link
            info = available()
            info["rust_link_ok"], info["cpp_link_ok"] = probe_rust_link()[0], probe_cpp()[0]
            print(json.dumps(info, indent=2, ensure_ascii=False))
            return 0
    except MatlabError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
