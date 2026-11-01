# Komponenten-Framework der AD-Plattform – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Die Versionsauflösung kennt nur MAJOR.MINOR.PATCH (keine Vorabversionen wie 1.0.0-rc1).
- Der DI-Container erkennt Zyklen, aber keine Lebensdauerkonflikte zwischen Scopes.
- compatible() prüft nur Typnamen; float und Vector gelten als kompatibel.

## Anwendungsgrenzen der Verfahren

### [Komponentenmodell mit typisierten Ports](theory.md#component_model)

Ereignisdiskrete Logik muss in diskreten Schritten abgebildet werden.

### [Dependency Injection und Laufzeitkontext](theory.md#dependency_injection)

Keine Threadsicherheit.

### [Deterministische Zufallszahlen und Reproduzierbarkeit](theory.md#deterministic_seeding)

Reproduzierbar nur bei gleichen Bibliotheksversionen (im Manifest dokumentiert).

### [Versionierte Plugin-Registry](theory.md#plugin_registry)

Keine Vorabversionen und Build-Metadaten.

### [Signaltypen und Codecs](theory.md#signal_type_system)

Keine Einheitenprüfung an Ports (Einheiten nur dokumentiert).
