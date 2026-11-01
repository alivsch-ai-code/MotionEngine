"""Command line for the automated-driving platform (Werling trajectory planning and stabilization).

    python run_ad.py --list                          scenarios and components
    python run_ad.py highway_cut_in                  run a scenario with the default stack, print KPIs
    python run_ad.py highway_cut_in --controller tracking_controller/stanley_pi --save out/run1
    python run_ad.py highway_cut_in --compare-controllers werling_bilevel stanley_pi lqr_ff_fb
    python run_ad.py highway_cut_in --sweep stack.planner.params.cost.k_jerk=0.5,1,2
    python run_ad.py highway_cut_in --monte-carlo 20 --vary scenario_params.lead_speed=normal:20:2
    python run_ad.py highway_cut_in --benchmark 3
"""

import argparse
import json
import sys

from vdsim import api
from vdsim.core.logging_setup import setup_logging
from vdsim.research import format_benchmark, kpi_label


def _value(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _print_kpis(kpis):
    for key, value in kpis.items():
        if isinstance(value, (int, float)):
            label, unit = kpi_label(key)
            print(f"  {label:<36} {value:>12.4g} {unit}")


def _print_table(batch):
    keys = ["collision", "min_distance", "min_ttc", "max_e_n", "rms_e_n", "max_ay", "rms_jerk_long",
            "plan_time_mean", "consistency_max", "mean_speed"]
    keys = [k for k in keys if k in batch.kpi_keys()]
    print(f"{'Variante':<28}" + "".join(f"{k[:14]:>15}" for k in keys))
    for r in batch.records:
        if not r.get("ok"):
            print(f"{r['label']:<28}  FEHLER: {r.get('error')}")
            continue
        print(f"{r['label']:<28}" + "".join(f"{r['kpis'].get(k, float('nan')):>15.4g}" for k in keys))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scenario", nargs="?")
    p.add_argument("--list", action="store_true", help="Szenarien und Komponenten anzeigen")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--duration", type=float, default=None)
    p.add_argument("--param", action="append", default=[], help="Szenarioparameter name=wert")
    for layer in ("planner", "controller", "behavior", "plant", "perception", "prediction"):
        p.add_argument(f"--{layer}", default=None, help=f"Komponente der Ebene {layer} (kind/name[@version])")
    p.add_argument("--stack", default=None, help="Stack-Definition als JSON-Datei")
    p.add_argument("--save", default=None, help="Ergebnis speichern (Pfad ohne Endung)")
    p.add_argument("--compare-controllers", nargs="+", default=None)
    p.add_argument("--compare-planners", nargs="+", default=None)
    p.add_argument("--sweep", action="append", default=[], help="pfad=w1,w2,...")
    p.add_argument("--monte-carlo", type=int, default=0)
    p.add_argument("--vary", action="append", default=[], help="pfad=normal:mittel:std | uniform:min:max")
    p.add_argument("--workers", type=int, default=0)
    p.add_argument("--benchmark", type=int, default=0)
    p.add_argument("--out", default=None, help="Batch-Ergebnis als CSV/JSON")
    args = p.parse_args(argv)
    setup_logging()

    if args.list or not args.scenario:
        print("Szenarien:")
        for sc in api.list_scenarios():
            print(f"  {sc['name']:<34} {sc.get('title', '')}")
        print("\nKomponenten:")
        for c in api.list_components():
            print(f"  {c['kind']}/{c['name']}@{c['version']:<10} {c['label']}")
        return 0

    stack = {}
    if args.stack:
        with open(args.stack, encoding="utf-8") as f:
            stack = json.load(f)
    for layer in ("planner", "controller", "behavior", "plant", "perception", "prediction"):
        spec = getattr(args, layer)
        if spec:
            stack[layer] = {"component": spec}
    scenario_params = dict(kv.split("=", 1) for kv in args.param)
    scenario_params = {k: _value(v) for k, v in scenario_params.items()}
    base = {"scenario": args.scenario, "stack": stack, "seed": args.seed, "duration": args.duration,
            "scenario_params": scenario_params}

    if args.benchmark:
        print(format_benchmark(api.benchmark(args.scenario, stack, args.benchmark, args.duration)))
        return 0

    batch = None
    if args.compare_controllers or args.compare_planners:
        layer = "controller" if args.compare_controllers else "planner"
        kind = "tracking_controller" if layer == "controller" else "trajectory_planner"
        names = args.compare_controllers or args.compare_planners
        variants = {n: {"component": n if "/" in n else f"{kind}/{n}"} for n in names}
        batch = api.compare(base, layer, variants, args.workers)
    elif args.sweep:
        grid = {}
        for item in args.sweep:
            path, values = item.split("=", 1)
            grid[path] = [_value(v) for v in values.split(",")]
        batch = api.sweep(base, grid, args.workers)
    elif args.monte_carlo:
        dists = {}
        for item in args.vary:
            path, spec = item.split("=", 1)
            kind, a, b = spec.split(":")
            dists[path] = ({"dist": "normal", "mean": float(a), "std": float(b)} if kind == "normal"
                           else {"dist": "uniform", "low": float(a), "high": float(b)})
        batch = api.monte_carlo(base, dists, args.monte_carlo, args.seed or 0, args.workers)

    if batch is not None:
        _print_table(batch)
        if args.monte_carlo:
            stats = batch.statistics()
            print(f"\nKollisionsrate {stats['_runs']['collision_rate']:.3f}, fehlgeschlagen {stats['_runs']['failed']}")
        if args.out:
            batch.to_csv(args.out + ".csv")
            batch.to_json(args.out + ".json")
        return 0

    result = api.run(args.scenario, stack, args.seed, args.duration, scenario_params, snapshots=bool(args.save))
    print(f"{result.name}: {result.duration:.1f} s simuliert, Abbruch: {result.metadata.get('stop_reason', '-')}")
    _print_kpis(result.kpis)
    if args.save:
        print("gespeichert:", result.save(args.save))
    return 0


if __name__ == "__main__":
    sys.exit(main())
