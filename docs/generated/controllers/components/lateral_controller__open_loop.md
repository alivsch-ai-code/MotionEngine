# Lenkung nach Tabelle (open loop)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `lateral_controller/open_loop` · klassische Registry

**Lenkung nach Zeittabelle des Manövers (ISO-Lenkmanöver ohne Rückführung).**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `lateral_controller` |
| Name | `open_loop` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.open_loop.OpenLoopSteering`](../../../../vdsim/controllers/open_loop.py#L11) |
| Schnittstelle | `vdsim.core.interfaces.LateralController` |
| Sprache | python |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `steer` | `float` | – | Radlenkwinkel-Anforderung vorne in rad | – |

## Parameter

_Keine Parameter._

## Quellen

[FMVSS No. 126 (49 CFR 571.126) (2007)](../../references.md#fmvss126), [ISO 4138:2021 (2021)](../../references.md#iso4138), [ISO 7401:2011 (2011)](../../references.md#iso7401)
