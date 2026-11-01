# Spurwechsel-Latenzstudie – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Öffentliche API

### `lane_change.plotting`

| Name | Art | Beschreibung |
|---|---|---|
| [`plot_simple(ideal, uncorrected, corrected, lane_width, title)`](../../../lane_change/plotting.py#L15) | Funktion | Overview: trajectories and the lateral offset built up against the ideal lane change |
| [`plot_characteristic(characteristic, k_full_lock, k_full_lock_assumed, k_lane_change)`](../../../lane_change/plotting.py#L44) | Funktion | Static view of the distorted steering characteristic up to full lock |
| [`plot_scenario(ideal, uncorrected, corrected, title)`](../../../lane_change/plotting.py#L84) | Funktion | – |
| [`plot_latency_comparison(ideal, corrected_runs, uncorrected, labels, uncorrected_case)`](../../../lane_change/plotting.py#L132) | Funktion | – |

### `lane_change.profiles`

| Name | Art | Beschreibung |
|---|---|---|
| [`lane_change_curvature(t, v, width, duration, t_start)`](../../../lane_change/profiles.py#L6) | Funktion | Sinusoidal curvature: heading returns to 0 and the lateral offset is ~width. |

### `lane_change.simulation`

| Name | Art | Beschreibung |
|---|---|---|
| [`simulate(v, k_des_fn, characteristic, latency, t_end, dt, use_correction, yaw_rate_noise_deg, seed)`](../../../lane_change/simulation.py#L10) | Funktion | – |

### `lane_change.vehicle_model`

| Name | Art | Beschreibung |
|---|---|---|
| [`vehicle_step(x, y, psi, v, k, dt)`](../../../lane_change/vehicle_model.py#L6) | Funktion | One Euler step: x' = v*cos(psi), y' = v*sin(psi), psi' = v*k |
