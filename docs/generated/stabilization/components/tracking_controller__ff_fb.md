# Vorsteuerung + Rückführung (längs)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/ff_fb` · Version 1.0.0

**Beschleunigungsvorsteuerung aus der Trajektorie mit Rückführung von Geschwindigkeits- und Längsfehler.**

## Zweck

Zeitbasiertes Längstracking (Trajektorie statt Bahn).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `ff_fb` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.classic_longitudinal.FeedForwardFeedback`](../../../../vdsim/stabilization/classic_longitudinal.py#L109) |
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
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |
| `k_v` | Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |

## Theorie

$a=a_d+k_v(v_d-v)-k_se_t$

## Verfahren

[Feedforward](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Vorwärtsfahrt

## Einschränkungen

- Stellbeschränkungen nur geklemmt

## Validierung

- tests/stabilization/test_stabilization_classic.py

## Quellen

[Åström und Hägglund (2006)](../../references.md#astrom2006), [Werling (2011)](../../references.md#werling2011)

## Expertenmodus: Herleitungen und Hinweise

Fehlerdynamik $\ddot e_t+k_v\dot e_t+k_se_t=0$, stabil für $k_v,k_s>0$.
