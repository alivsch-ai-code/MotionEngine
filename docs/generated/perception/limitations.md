# perception – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.perception` gibt es noch keine handgeschriebene Dokumentation (`vdsim/perception/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init perception`


## Bekannte Grenzen des Pakets

_Noch nicht dokumentiert._

## [Objektsensor (Reichweite, Rauschen, Latenz)](components/perception__object_sensor.md)

Annahmen:

- Objekte als Rechtecke, Verdeckung nur in der Ebene (keine Höheninformation)
- Rauschen weiß und normalverteilt, Objekte unabhängig

Grenzen:

- kein Tracking, keine Falschalarme (Geisterobjekte)
- keine Sensorfusion mehrerer Sensoren
