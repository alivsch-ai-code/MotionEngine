# api – Beispiele

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · **Beispiele** · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## [run_ad.py](../../../run_ad.py)

Command line for the automated-driving platform (Werling trajectory planning and stabilization).

python run_ad.py --list                          scenarios and components
python run_ad.py highway_cut_in                  run a scenario with the default stack, print KPIs
python run_ad.py highway_cut_in --controller tracking_controller/stanley_pi --save out/run1
python run_ad.py highway_cut_in --compare-controllers werling_bilevel stanley_pi lqr_ff_fb
python run_ad.py highway_cut_in --sweep stack.planner.params.cost.k_jerk=0.5,1,2
python run_ad.py highway_cut_in --monte-carlo 20 --vary scenario_params.lead_speed=normal:20:2
python run_ad.py highway_cut_in --benchmark 3

Verwendet: `vdsim.api`

Ausführen: `python run_ad.py`

## [run_api.py](../../../run_api.py)

REST/JSON API of the platform: python run_api.py --port 8765 [--token SECRET]

Verwendet: `vdsim.api.server`

Ausführen: `python run_api.py`
