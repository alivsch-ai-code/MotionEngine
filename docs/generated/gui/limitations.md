# Desktop-Anwendung (PySide6) – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Lange Simulationen blockieren die Oberfläche nicht, laufen im Modus „Echtzeit“ aber nur so schnell wie der GUI-Takt erlaubt.
- Die 3D-Ansicht benötigt OpenGL.
- Frenet-Projektion der Hindernisse nutzt die Mittellinie der Fahrspur aus result.road; weicht die Referenzlinie des Planers davon ab, sind die Hindernis-Frenet-Koordinaten Näherungen.
- Ego-Kollisionskreise werden an der aktuellen Pose gezeichnet (Offsets entlang der Gierrichtung ab dem Schwerpunkt); die zeitliche Rampe des Sicherheitsabstands (ramp_time) wird nicht animiert.
- Abbruch einer Simulation wirkt erst beim nächsten progress-Aufruf des Runners; Batch-Experimente sind nicht abbrechbar.
- Der Parameterdialog kennt Metadaten (Label, Einheit, Grenzen) nur für die oberste Ebene; verschachtelte Gruppen zeigen Feldnamen.
