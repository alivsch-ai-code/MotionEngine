# world – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.world` gibt es noch keine handgeschriebene Dokumentation (`vdsim/world/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init world`


## Bekannte Grenzen des Pakets

_Noch nicht dokumentiert._

## [Szenario-Engine](components/world__scenario_engine.md)

Annahmen:

- Ego-Umriss als Rechteck; Mittelpunkt in der Mitte zwischen den Achsen (Überhänge gleich)
- Akteure reagieren auf das Ego über IDM, sofern es ihre Spur belegt

Grenzen:

- keine Fahrzeugdynamik der Akteure (kinematische Bewegung entlang der Spur)
- Störungen wie die Seitenwindböe werden nur als Ereignis gemeldet, nicht selbst eingeprägt
