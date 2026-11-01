# prediction – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.prediction` gibt es noch keine handgeschriebene Dokumentation (`vdsim/prediction/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init prediction`


## Bekannte Grenzen des Pakets

_Noch nicht dokumentiert._

## [Konstante Beschleunigung (Frenet, Werling 3.5.2)](components/predictor__constant_acceleration.md)

Annahmen:

- Beschleunigung über den Horizont konstant
- keine Querbewegung relativ zur Spur
- an Verzweigungen folgt das Objekt der Standardfortsetzung der Spur

Grenzen:

- Spurwechsel und Abbiegen anderer Verkehrsteilnehmer werden nicht vorhergesagt

## [Spurfolge mit Querabsicht](components/predictor__lane_following.md)

Annahmen:

- Objekte folgen der Standardfortsetzung der Spur

Grenzen:

- Abbiegeabsichten an Kreuzungen werden nicht geschätzt
