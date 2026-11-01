# behavior – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.behavior` gibt es noch keine handgeschriebene Dokumentation (`vdsim/behavior/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init behavior`


## Bekannte Grenzen des Pakets

_Noch nicht dokumentiert._

## [Regelbasierte Verhaltensplanung](components/behavior_planner__rule_based.md)

Annahmen:

- Kartenwissen (Spuren, Markierungen, Haltelinien) ist exakt bekannt
- Objekte tragen lane_id/s/d der Szenario-Engine bzw. Perception

Grenzen:

- keine Neuplanung der Route bei verpasster Ausfahrt
- Linksabbiegen bei Grün: einfache Zeitlückenprüfung gegen den Gegenverkehr
