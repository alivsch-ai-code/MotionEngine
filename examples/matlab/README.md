# MATLAB-Skripte importieren, analysieren und konvertieren

`kin_tracking_with_orientation_stab.m` ist der Lyapunov-Trackingregler mit Orientierungsstabilisierung aus Werling 2011, Anhang A.5. Er ist originalgetreu transkribiert. Die dort verwendete, aber nicht abgedruckte Hilfsfunktion `normalize_angle` ist als Subfunction ergänzt.

## Ausführen ohne MATLAB

```python
from vdsim.matlab import Interpreter
it = Interpreter.from_file("examples/matlab/kin_tracking_with_orientation_stab.m")
delta_dot, F_l = it.call(None, 1.0, 2.0, 0.3, 0.05, 0.01, 2.0, 0.1, 1,   # Sollwerte (Hinterachse), varsigma
                          1.2, 1.9, 0.35, 2.1, 0.02,                       # Messgrößen
                          1.2, 1.4, 1500, 2500, 0.1,                       # l_v, l_h, m, J, gam
                          1, 2, 3, 4)                                      # k1..k4
```

## Als Komponente laden

```python
from vdsim.matlab import load_matlab_component
ctrl = load_matlab_component("examples/matlab/kin_tracking_with_orientation_stab.m",
                             backend="python",            # oder "interpreter"
                             params={"l_v": 1.2, "l_h": 1.4, "m": 1500, "J": 2500, "gam": 0.1,
                                     "k1": 1, "k2": 2, "k3": 3, "k4": 4})
print(ctrl.INPUTS.keys(), ctrl.OUTPUTS.keys())   # Ports aus der Funktionssignatur
out = ctrl.step(0.0, {...})                      # {"delta_dot": ..., "F_l": ...}
```

Im Graph-Format reicht der Spec-String `"matlab:examples/matlab/kin_tracking_with_orientation_stab.m"`, optional mit `:funktion`. Die Werte in `params` werden zu konstanten Parametern, die übrigen Eingänge zu Ports. Skalare Ports haben den Typ `float`, Vektoren den Typ `Vector`.

## Analysieren und konvertieren (CLI)

```powershell
python -m vdsim.matlab analyze examples\matlab\kin_tracking_with_orientation_stab.m            # Zusammenfassung
python -m vdsim.matlab analyze examples\matlab\kin_tracking_with_orientation_stab.m --latex    # Formeln
python -m vdsim.matlab analyze examples\matlab\kin_tracking_with_orientation_stab.m --dot dataflow > a5.dot
python -m vdsim.matlab convert examples\matlab\kin_tracking_with_orientation_stab.m --to all --out build\a5
python -m vdsim.matlab toolchains                                                              # Compiler
```

`convert --to all` erzeugt die Unterordner `python/`, `cpp/` (Header, Implementierung, `matlab_runtime.hpp`) und `rust/`. Nicht übersetzbare Konstrukte werden mit Zeile und Spalte gemeldet. Die Dateien werden dann nicht geschrieben (`--force` überschreibt dieses Verhalten).

## Eigene Skripte vorbereiten

- **Signatur:** Pro Datei eine Hauptfunktion mit Ein- und Ausgängen (`function [u, y] = regler(x, k)`); lokale Funktionen sind erlaubt.
- **Doku:** Den Hilfetext direkt unter die Funktionszeile schreiben; er wird zur Komponenten-Doku.
- **Gleichungen:** Gleichungsnummern als Kommentar `% (4.11)` an die Zeile setzen. Sie erscheinen in Analyse, LaTeX-Ausgabe und generiertem Code.
- **Typhinweise:** Vektoreingänge mit einem Kommentar `%#type x: vector(3)` (auch `row`, `matrix(2,2)`) markieren oder `input_types={"x": "vector"}` übergeben.
- **Persistente Zustände** (`persistent`) werden beim Reset der Komponente gelöscht. In C++ und Rust werden sie zu einem State-Struct, das der Aufrufer hält.
- **Für C++/Rust:** Skalare und reelle Matrizen mit skalaren Indizes verwenden und Arrays vorab mit `zeros(m, n)` anlegen. Keine Strings außer in `fprintf`/`disp`/`error`, keine Zellen und Structs.
- **Eigene Built-ins** für den Interpreter: `vdsim.matlab.register_builtin("sat", lambda x, lo, hi: min(max(x, lo), hi))`.
