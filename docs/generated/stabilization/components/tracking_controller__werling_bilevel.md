# Werling: Bi-level-Stabilisierung (Umschaltung + Reinitialisierung)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/werling_bilevel` · Version 1.0.0

**Standard-Trackingregler: stoßfreie Umschaltung der drei Werling-Regler nach Referenzpunkt und Fahrtrichtung, dazu Reinitialisierungsauslösung und Bewegungsprädiktion für die Planung.**

## Zweck

Vereint Low-level-Stabilisierung (permanente Störungen, Modellfehler) mit der High-level-Stabilisierung durch Reinitialisierung bei Impulsstörungen (Werling 2.3, 4.4, 4.5).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `werling_bilevel` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.switching.WerlingBilevel`](../../../../vdsim/stabilization/switching.py#L60) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `v_switch` | Umschaltgeschwindigkeit v_s | m/s | 3 | 0.5 | 15 |
| `v_min_dynamic` | Mindestgeschwindigkeit des dynamischen Reglers | m/s | 1 | 0.1 | – |
| `forward_slow` | Regler langsam vorwärts: center / orientation | – | center | – | – |
| `c_t` | Schwellwert c_t (Längsfehleränderung) | m/s | 1 | 0.01 | – |
| `c_n` | Schwellwert c_n (Querfehleränderung) | m/s | 0.5 | 0.01 | – |
| `e_t_max` | absoluter Längsfehler e_max (0 = aus) | m | 0 | 0 | – |
| `e_n_max` | absoluter Querfehler e_max (0 = aus) | m | 0 | 0 | – |
| `e_theta_max` | absoluter Orientierungsfehler (0 = aus) | rad | 0 | 0 | – |
| `reinit_enabled` | Reinitialisierungsauslösung aktiv | – | True | – | – |
| `cooldown` | Sperrzeit nach einer Reinitialisierung | s | 0.3 | 0 | – |
| `max_hold` | max. Haltedauer der Anforderung | s | 0.5 | 0 | – |
| `prediction_dt` | Prädiktionszeit Delta t (Planungslatenz) | s | 0.1 | 0 | 1 |
| `mu` | Reibwert (<0: aus Fahrzeug/Umgebung) | - | -1 | – | – |
| `orientation` | Parameter Satz 4 | – | {…} | – | – |
| `center` | Parameter Satz 6 | – | {…} | – | – |
| `dynamic` | Parameter Satz 8 | – | {…} | – | – |

## Theorie

Umschaltung nach Abb. 4.13; elliptisches Maß $(\dot e_t/c_t)^2+(\dot e_n/c_n)^2\geq1$ (4.5.1) im Schwerpunkt bzw. geometrischen Mittelpunkt; Taylor-Prädiktion des Referenzpunkts über die Planungslatenz (4.5.2).

## Verfahren

[Bi-level-Stabilisierung (Planerseite)](../../planning/theory.md#bilevel_stabilization), [Stoßfreie Reglerumschaltung](../theory.md#controller_switching), [Bewegungsprädiktion für die Reinitialisierung](../../planning/theory.md#motion_prediction), [Reinitialisierung und Bewegungsprädiktion](../theory.md#reinitialization_trigger)

## Annahmen

- Planer setzt reference_point mit Hysterese um v_s (contracts.md Abschnitt 7)
- Planer beantwortet reinit_request mit einer Trajektorie mit reinitialized=True

## Einschränkungen

- Harte Umschaltung: kleine Stellgrößensprünge möglich, Verstärkungen abgestimmt
- Schwellwerte c_t, c_n experimentell (Standardwerte für die Mittelklasselimousine)

## Validierung

- tests/stabilization/test_stabilization_switching.py

## Umgesetzte Gleichungen

- `werling2011:Abb. 4.13`
- `werling2011:(4.58)`
- `werling2011:(4.59)`
- `werling2011:4.5.1`
- `werling2011:4.5.2`

## Quellen

[Werling et al. (2010)](../../references.md#werling2010tro), [Werling (2011)](../../references.md#werling2011)

## Designentscheidungen

- Reinitialisierungsanforderung gehalten bis zur Antwort (max_hold), danach Sperrzeit
- cog-Trajektorie unter v_min_dynamic: kinematischer Regler mit quasistatischer Umrechnung auf die Hinterachse

## Expertenmodus: Herleitungen und Hinweise

Jeder Teilregler ist für sich asymptotisch stabil (Sätze 4, 6, 8). Da beim Umschalten beide Modelle gültig sind und die Vorsteueranteile dominieren, bleiben die Sprünge klein; die Reinitialisierung setzt die Low-level-Fehler auf null (Werling 2.3).

## Verwendung

Tests: [tests/stabilization/test_stabilization_layers.py](../../../../tests/stabilization/test_stabilization_layers.py), [tests/stabilization/test_stabilization_switching.py](../../../../tests/stabilization/test_stabilization_switching.py)

Konfigurationen: [configs/stabilization/werling_bilevel_default.json](../../../../configs/stabilization/werling_bilevel_default.json), [configs/stabilization/werling_slow_orientation.json](../../../../configs/stabilization/werling_slow_orientation.json)
