# perception – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


**Noch nicht dokumentiert.** Es gibt keine handgeschriebene `theory.md` (`vdsim/perception/docs/theory.md`).

## Konzepte ohne Theorieabschnitt {#konzepte-ohne-theorie}

Folgende Konzepte werden im Code oder in der Paketdoku genannt, haben aber noch keinen Abschnitt `## … {#concept-id}`:

- `sensor_model`

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Sensor model](../README.md#konzepte-ohne-dokumentation) | [`sensor.visibility`](../../../vdsim/perception/sensor.py#L52) | [`perception/ground_truth`](components/perception__ground_truth.md), [`perception/object_sensor`](components/perception__object_sensor.md) | [bar_shalom2001 (fehlt in docs/references)](../references.md#bar_shalom2001), [vdsim (fehlt in docs/references)](../references.md#vdsim) |
