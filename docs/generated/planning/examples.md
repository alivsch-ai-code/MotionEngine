# Trajektorienplanung nach Werling – Beispiele

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · **Beispiele** · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## [examples/custom_nodes/python/my_collision_checker.py](../../../examples/custom_nodes/python/my_collision_checker.py)

Example: own collision checker for the Werling trajectory planner (kind="collision_checker").

Exact rectangle overlap test with the separating axis theorem (SAT) instead of the circle
approximation. Usage:

    "collision": {"checker": "python:examples/custom_nodes/python/my_collision_checker.py:BoxCollisionChecker"}

The checker receives once per cycle the prediction, the common time grid of the check horizon
and the ego geometry (prepare) and then evaluates batches of candidates (check). It must return
the time of the first collision so that the planner can select the fallback trajectory.

Verwendet: `vdsim.planning.collision`

Ausführen: `python examples/custom_nodes/python/my_collision_checker.py`

## [examples/custom_nodes/python/my_cost_function.py](../../../examples/custom_nodes/python/my_cost_function.py)

Example: own cost term for the Werling trajectory planner (kind="cost_term").

Usage in a planner configuration (configs/planning/*.json or API):

    "cost": {"custom": [{"spec": "python:examples/custom_nodes/python/my_cost_function.py:KeepRightCost",
                         "params": {"weight": 2.0}}]}

A separable term implements lateral() and/or longitudinal() and is evaluated on the candidate
sets (cheap, enters the cost sorting). A term with SCOPE = "combined" implements combined()
and is evaluated in the re-ranking window on world trajectories. Only the consistent Werling
terms keep the Bellman guarantee; an additional term shifts the optimum (see theory.md).

Verwendet: `vdsim.planning.cost`

Ausführen: `python examples/custom_nodes/python/my_cost_function.py`

## [examples/planning/common.py](../../../examples/planning/common.py)

Shared helpers of the planning examples (plots are saved to examples/planning/output/).

Ausführen: `python examples/planning/common.py`

## [examples/planning/consistency.py](../../../examples/planning/consistency.py)

Zeitliche Konsistenz (Werling 2011, 3.2, Satz 3, Abb. 3.2).

Rückkehr zur Spurmitte aus 2 m Querablage mit zyklischer Neuplanung bei drei Planungsperioden:
Werling-Planer (absolutes Endzeitraster, Start auf der alten Trajektorie) gegen den naiven
Frenet-Planer (relatives Raster, Neuplanung vom Messzustand). Der konsistente Planer liefert
unabhängig von der Periode dieselbe Bewegung.
Bild: examples/planning/output/consistency.png

Verwendet: `vdsim.planning.simulation`

Ausführen: `python examples/planning/consistency.py`

## [examples/planning/evasion.py](../../../examples/planning/evasion.py)

Ausweichen um ein liegengebliebenes Fahrzeug bei Gegenverkehr (Werling 2011, 3.5.4, 5.3).

Ein stehendes Fahrzeug blockiert die eigene Spur, auf der Gegenspur kommt ein Fahrzeug
entgegen. Der Werling-Planer optimiert Quer- und Längsbewegung kombiniert: er verzögert leicht,
lässt den Gegenverkehr passieren und weicht dann aus. Zum Vergleich der sequentielle Planer
(erst längs, dann quer, Werling 3.1).
Bild: examples/planning/output/evasion.png

Verwendet: `vdsim.planning.simulation`

Ausführen: `python examples/planning/evasion.py`

## [examples/planning/following.py](../../../examples/planning/following.py)

Folgefahrt hinter einem bremsenden Vorderfahrzeug (Werling 2011, 3.5.2) mit Ablösestrategie.

Aktiv sind Geschwindigkeithalten (v_ref = 25 m/s) und Folgen (s_ref = s_v - [k0 + kv ṡ_v]).
Der Modus mit dem kleinsten Anfangsruck setzt sich durch (Schritt 6). Das Vorderfahrzeug fährt
mit 15 m/s, bremst ab t = 12 s mit -2 m/s² bis 5 m/s und beschleunigt ab t = 25 s wieder.
Bild: examples/planning/output/following.png

Verwendet: `vdsim.planning`, `vdsim.planning.planner`, `vdsim.planning.simulation`

Ausführen: `python examples/planning/following.py`

## [examples/planning/lane_change.py](../../../examples/planning/lane_change.py)

Spurwechsel mit dem Werling-Planer auf gerader und gekrümmter Straße (Werling 2011, 3.5.1).

Die Verhaltensebene legt die Referenzkurve auf die Mitte der Zielspur; der Planer führt den
Spurwechsel als Rückkehr auf d = 0 aus. Ausgabe: Draufsicht mit Kandidatensatz, d(t), Quer-
beschleunigung und Geschwindigkeit; Bild in examples/planning/output/lane_change.png.

Verwendet: `vdsim.planning`, `vdsim.planning.planner`, `vdsim.planning.simulation`

Ausführen: `python examples/planning/lane_change.py`

## [examples/planning/stopping.py](../../../examples/planning/stopping.py)

Anhalten an einer Haltelinie aus 50 km/h (Werling 2011, 3.5.2) mit Regimewechsel.

Unterhalb von v_s - Hysterese wechselt der Planer von d(t) mit Schwerpunkt auf d(s) mit
Hinterachsmitte (3.5.1, 3.5.4). Die Fahrzeugfront steht exakt auf der Haltelinie.
Bild: examples/planning/output/stopping.png

Verwendet: `vdsim.planning`, `vdsim.planning.planner`, `vdsim.planning.simulation`

Ausführen: `python examples/planning/stopping.py`

## Szenarien und Konfigurationen

| Datei | Titel | Beschreibung |
|---|---|---|
| [configs/planning/comfort.json](../../../configs/planning/comfort.json) | comfort | Komfortabel: niedrige Beschleunigungsgrenzen, langsamere Manöver (kleineres k_tau). Zusätzlich gewichteter Komfortterm (nicht konsistent: Bellman-Garantie entfällt teilweise). |
| [configs/planning/default.json](../../../configs/planning/default.json) | default | Werling-Standardparametrierung: nur konsistente Kostenterme (Bellman-Garantie), absolutes Endzeitraster, Bi-level-Stabilisierung. |
| [configs/planning/sporty.json](../../../configs/planning/sporty.json) | sporty | Sportlich: schnellere Manöver (größeres k_tau), höhere Grenzen, kleinere Sicherheitsabstände. Nur konsistente Kostenterme. |
