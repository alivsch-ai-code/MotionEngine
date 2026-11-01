# Laufzeitumgebung – Graph, Executor, Debugging, Versionierung, Custom Nodes – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `base_dt` | Basisschritt des Executors (s); alle Perioden müssen ganzzahlige Vielfache sein | – | – |
| `nodes[].period` | Abtastperiode eines Knotens (None = PERIOD der Komponente bzw. jeder Basisschritt) | – | – |
| `VDSIM_BUILD_DIR` | Umgebungsvariable für das Build-Verzeichnis nativer Nodes (Standard <temp>/vdsim_native) | – | – |
| `Executor(check_types=True)` | Laufzeit-Typprüfung aller Ein- und Ausgänge über framework.types.check_value | – | – |
| `Executor.realtime_factor` | Echtzeitfaktor für advance(wall_dt) | – | – |

## Parameter von [Konstante](components/node__constant.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `value` | Wert | – | 1 | – | – |

## Parameter von [Demux](components/node__demux.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `n` | Anzahl Eingänge | – | 2 | 1 | 64 |

## Parameter von [Verstärkung](components/node__gain.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k` | Verstärkung | – | 1 | – | – |

## Parameter von [Integrator](components/node__integrator.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k` | Verstärkung | – | 1 | – | – |
| `initial` | Anfangswert | – | 0 | – | – |
| `lower` | Untere Grenze | – | -inf | – | – |
| `upper` | Obere Grenze | – | inf | – | – |

## Parameter von [Tiefpass (PT1)](components/node__lowpass.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `T` | Zeitkonstante | s | 0.1 | 0 | – |
| `K` | Verstärkung | – | 1 | – | – |
| `initial` | Anfangswert | – | 0 | – | – |

## Parameter von [Mux](components/node__mux.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `n` | Anzahl Eingänge | – | 2 | 1 | 64 |

## Parameter von [Produkt](components/node__product.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `ops` | Operationen (z. B. '*/') | – | ** | – | – |

## Parameter von [Rampe](components/node__ramp.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `slope` | Steigung | 1/s | 1 | – | – |
| `t_start` | Startzeit | s | 0 | 0 | – |
| `initial` | Anfangswert | – | 0 | – | – |

## Parameter von [Ratenbegrenzer](components/node__rate_limiter.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `rising` | Max. Anstiegsrate | 1/s | 1 | 0 | – |
| `falling` | Max. Abfallrate | 1/s | 1 | 0 | – |
| `initial` | Anfangswert | – | 0 | – | – |

## Parameter von [Begrenzung](components/node__saturation.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `lower` | Untere Grenze | – | -1 | – | – |
| `upper` | Obere Grenze | – | 1 | – | – |

## Parameter von [Scope](components/node__scope.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `n` | Anzahl Eingänge | – | 1 | 1 | 16 |
| `max_samples` | Max. Abtastwerte | – | 100000 | 1 | – |

## Parameter von [Sinus](components/node__sine.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `amplitude` | Amplitude | – | 1 | – | – |
| `frequency` | Frequenz | Hz | 1 | 0 | – |
| `phase` | Phase | rad | 0 | – | – |
| `offset` | Offset | – | 0 | – | – |

## Parameter von [Sprung](components/node__step.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `t_step` | Sprungzeit | s | 1 | 0 | – |
| `initial` | Anfangswert | – | 0 | – | – |
| `final` | Endwert | – | 1 | – | – |

## Parameter von [Summe](components/node__sum.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `signs` | Vorzeichen (z. B. '+-') | – | ++ | – | – |

## Parameter von [Schalter](components/node__switch.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `threshold` | Schwelle | – | 0 | – | – |

## Parameter von [Standardwert](components/node__typed_default.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `type_name` | Datentyp | – | ObjectList | – | – |

## Parameter von [Verzögerung (z⁻¹)](components/node__unit_delay.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `initial` | Anfangswert | – | 0 | – | – |

## Parametersatz `ConstantParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `value` | Wert | – | 1 | – | – |

## Parametersatz `StepParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `t_step` | Sprungzeit | s | 1 | 0 | – |
| `initial` | Anfangswert | – | 0 | – | – |
| `final` | Endwert | – | 1 | – | – |

## Parametersatz `SineParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `amplitude` | Amplitude | – | 1 | – | – |
| `frequency` | Frequenz | Hz | 1 | 0 | – |
| `phase` | Phase | rad | 0 | – | – |
| `offset` | Offset | – | 0 | – | – |

## Parametersatz `RampParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `slope` | Steigung | 1/s | 1 | – | – |
| `t_start` | Startzeit | s | 0 | 0 | – |
| `initial` | Anfangswert | – | 0 | – | – |

## Parametersatz `TypedDefaultParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `type_name` | Datentyp | – | ObjectList | – | – |

## Parametersatz `GainParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k` | Verstärkung | – | 1 | – | – |

## Parametersatz `SumParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `signs` | Vorzeichen (z. B. '+-') | – | ++ | – | – |

## Parametersatz `ProductParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `ops` | Operationen (z. B. '*/') | – | ** | – | – |

## Parametersatz `SaturationParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `lower` | Untere Grenze | – | -1 | – | – |
| `upper` | Obere Grenze | – | 1 | – | – |

## Parametersatz `SwitchParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `threshold` | Schwelle | – | 0 | – | – |

## Parametersatz `MuxParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `n` | Anzahl Eingänge | – | 2 | 1 | 64 |

## Parametersatz `DelayParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `initial` | Anfangswert | – | 0 | – | – |

## Parametersatz `IntegratorParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k` | Verstärkung | – | 1 | – | – |
| `initial` | Anfangswert | – | 0 | – | – |
| `lower` | Untere Grenze | – | -inf | – | – |
| `upper` | Obere Grenze | – | inf | – | – |

## Parametersatz `LowPassParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `T` | Zeitkonstante | s | 0.1 | 0 | – |
| `K` | Verstärkung | – | 1 | – | – |
| `initial` | Anfangswert | – | 0 | – | – |

## Parametersatz `RateLimiterParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `rising` | Max. Anstiegsrate | 1/s | 1 | 0 | – |
| `falling` | Max. Abfallrate | 1/s | 1 | 0 | – |
| `initial` | Anfangswert | – | 0 | – | – |

## Parametersatz `ScopeParams` (`vdsim.runtime.blocks`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `n` | Anzahl Eingänge | – | 1 | 1 | 16 |
| `max_samples` | Max. Abtastwerte | – | 100000 | 1 | – |

## Konfigurationsdateien, die Komponenten dieses Pakets verwenden

| Datei | Titel | Komponenten |
|---|---|---|
| [configs/graphs/examples/custom_nodes_kette.json](../../../configs/graphs/examples/custom_nodes_kette.json) | custom_nodes_kette | `node/typed_default` |
| [configs/graphs/examples/integrator_regelkreis.json](../../../configs/graphs/examples/integrator_regelkreis.json) | integrator_regelkreis | `node/gain`, `node/integrator`, `node/saturation`, `node/scope`, `node/step`, `node/sum` |
| [configs/graphs/examples/multirate_zoh.json](../../../configs/graphs/examples/multirate_zoh.json) | multirate_zoh | `node/clock`, `node/gain`, `node/rate_limiter`, `node/scope`, `node/sine`, `node/unit_delay` |
| [configs/graphs/examples/pt1_sprungantwort.json](../../../configs/graphs/examples/pt1_sprungantwort.json) | pt1_sprungantwort | `node/lowpass`, `node/scope`, `node/step` |
