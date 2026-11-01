"""Command line: run scenarios, print KPIs, export results and reports.

    python run_scenario.py --list
    python run_scenario.py iso_doppelspurwechsel_80 --plot
    python run_scenario.py kreisfahrt_r40 bremsen_100_abs --report bericht.pdf --summary bericht.md
    python run_scenario.py configs/scenarios/slalom_60.json --csv slalom.csv
    python run_scenario.py --all
"""

import argparse
from pathlib import Path

from vdsim.core.logging_setup import setup_logging
from vdsim.reporting import evaluate
from vdsim.simulation.scenario import Scenario, ScenarioManager
from vdsim.simulation.simulator import Simulator


def load(name_or_path, manager):
    path = Path(name_or_path)
    return Scenario.load(path) if path.suffix == ".json" else manager.load(name_or_path)


def main():
    parser = argparse.ArgumentParser(description="vdsim - Fahrdynamik-Szenarien ausführen")
    parser.add_argument("scenarios", nargs="*", help="Szenario-Namen (configs/scenarios) oder JSON-Dateien")
    parser.add_argument("--list", action="store_true", help="verfügbare Szenarien auflisten")
    parser.add_argument("--all", action="store_true", help="alle Szenarien ausführen")
    parser.add_argument("--plot", action="store_true", help="Übersichtsplots anzeigen")
    parser.add_argument("--report", help="PDF-Bericht schreiben")
    parser.add_argument("--summary", help="Engineering Summary (Markdown) schreiben")
    parser.add_argument("--csv", help="Zeitverläufe als CSV schreiben (nur ein Szenario)")
    args = parser.parse_args()

    setup_logging()
    manager = ScenarioManager()
    if args.list:
        for name in manager.names():
            sc = manager.load(name)
            print(f"{name:<32} {sc.name}  -  {sc.description}")
        return
    names = manager.names() if args.all else args.scenarios
    if not names:
        parser.print_help()
        return

    results = []
    for name in names:
        scenario = load(name, manager)
        result = Simulator.from_scenario(scenario).run()
        print(f"\n=== {scenario.name}  ({result.metadata['stop_reason']}, {result.metadata['wall_time']:.1f} s Rechenzeit)")
        for kpi in evaluate(result):
            rating = {"ok": "", "warn": "  <- Hinweis", "fail": "  <- nicht erfüllt"}.get(kpi.rating, "")
            print(f"  {kpi.group:<16} {kpi.label:<44} {kpi.formatted():>10} {kpi.unit}{rating}")
        results.append(result)

    if args.csv:
        results[0].to_csv(args.csv)
        print(f"\nCSV geschrieben: {args.csv}")
    if args.report:
        from vdsim.reporting.report_generator import generate_pdf
        generate_pdf(results, args.report)
        print(f"PDF-Bericht geschrieben: {args.report}")
    if args.summary:
        from vdsim.reporting.report_generator import save_summary
        save_summary(results, args.summary)
        print(f"Engineering Summary geschrieben: {args.summary}")
    if args.plot:
        import matplotlib.pyplot as plt

        from vdsim.visualization import plotter
        for result in results:
            plotter.overview_figure(result)
        if len(results) > 1:
            plotter.compare_figure(results)
        plt.show()


if __name__ == "__main__":
    main()
