# Werling: Lyapunov mit Orientierungsstabilisierung (Satz 4)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/werling_kinematic_orientation` · Version 1.0.0

**Lyapunov-basierter Trackingregler der Hinterachsmitte mit Orientierungsstabilisierung für langsame Vorwärts- und Rückwärtsfahrt.**

## Zweck

Stabilisiert Position, Orientierung, Geschwindigkeit und Lenkwinkel des erweiterten kinematischen Einspurmodells entlang der Solltrajektorie, auch im Stand und rückwärts (Werling 4.2.3).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `werling_kinematic_orientation` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.werling_kinematic.WerlingKinematicOrientation`](../../../../vdsim/stabilization/werling_kinematic.py#L221) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | Fahrzeugzustand (Schwerpunkt) | – |
| `trajectory` | `PlannedTrajectory` | – | Solltrajektorie der Hinterachsmitte | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k1` | k1 (Positionsfehler) | 1/m² | 0.5 | 0 | – |
| `k2` | k2 (Orientierungsfehler) | 1/m | 2 | 0 | – |
| `k3` | k3 (Geschwindigkeitsfehler) | 1/s | 2 | 0 | – |
| `k4` | k4 (Lenkfehler, Backstepping) | 1/s | 10 | 0 | – |
| `gamma_drive` | Kräfteverhältnis Antrieb (<0: aus Antriebslayout) | - | -1 | -1 | 1 |
| `gamma_brake` | Kräfteverhältnis Bremsen | - | 0.75 | 0 | 1 |
| `taylor_switch` | Grenze Taylor-Näherung | rad | 0.5 | 0 | 1.5 |
| `mu` | Reibwert (<0: aus Fahrzeug/Umgebung) | - | -1 | – | – |

## Theorie

Invariante Fehler im Frenet-Rahmen der Solltrajektorie (4.9), fiktives Regelgesetz für $\kappa_\delta$ (4.11), virtueller Eingang $w_2=\dot v$ (4.12), Backstepping auf $u_1=\dot\delta$ (4.16)-(4.18), Rücksubstitution (4.15), (4.7).

## Verfahren

[Backstepping](../../README.md#konzepte-ohne-dokumentation) (undokumentiert), [Invariant tracking error](../../README.md#konzepte-ohne-dokumentation) (undokumentiert), [Erweitertes kinematisches Einspurmodell](../theory.md#kesm), [Lyapunov-Tracking mit Orientierungsstabilisierung](../theory.md#lyapunov_orientation)

## Annahmen

- Keine Reifenschräglaufwinkel (langsame Fahrt, kinematisches Einspurmodell)
- Alle Zustände gemessen, Lenkwinkel |delta| < pi/2
- Antriebs- und Bremskräfte werden von unterlagerten Regelkreisen schnell eingestellt

## Einschränkungen

- Front schwenkt bei großen Korrekturen aus (Referenzpunkt Hinterachse)
- Keine Stellgrößenbeschränkung im Regelgesetz (Reserve durch die Planung)
- Für schnelle Fahrt ungeeignet (Schräglauf vernachlässigt)

## Validierung

- tests/stabilization/test_stabilization_kinematic.py

## Umgesetzte Gleichungen

- `werling2011:(4.9)`
- `werling2011:(4.10)`
- `werling2011:(4.11)`
- `werling2011:(4.12)`
- `werling2011:(4.15)`
- `werling2011:(4.16)`
- `werling2011:(4.17)`
- `werling2011:(4.18)`
- `werling2011:(4.7)`
- `werling2011:(A.10)-(A.13)`

## Quellen

[Khalil (2002)](../../references.md#khalil2002), [Werling et al. (2010)](../../references.md#werling2010tro), [Werling (2011)](../../references.md#werling2011)

## Expertenmodus: Herleitungen und Hinweise

Mit $V_c=\frac{1}{2}[k_1e_t^2+k_1e_n^2+e_\psi^2+e_v^2+e_\delta^2]$ gilt $\dot V_c=-\dot s_dk_2e_\psi^2-k_3e_v^2-k_4e_\delta^2\leq0$; LaSalle liefert asymptotische Stabilität von $[e_t,e_n,e_\psi,e_v,e_\delta]=0$ für $\dot s_d\ne0$ (Satz 4). Vorwärts und rückwärts über $\varsigma$, kein Lenkwinkelsprung im Stand, da keine Division durch $v$.

## Verwendung

Tests: [tests/stabilization/test_stabilization_kinematic.py](../../../../tests/stabilization/test_stabilization_kinematic.py), [tests/stabilization/test_stabilization_layers.py](../../../../tests/stabilization/test_stabilization_layers.py)
