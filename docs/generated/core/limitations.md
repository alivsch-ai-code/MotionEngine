# Kern – Konventionen, Parameter, Schnittstellen, Registry – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Die klassische Registry kennt keine Versionen; zwei Plugins mit gleichem Namen überschreiben sich stillschweigend.
- Grenzen (min/max) in den Parametern sind GUI-Hinweise und werden beim Laden aus JSON nicht erzwungen.
- Die Konventionen gelten für den klassischen Simulator; die AD-Plattform nutzt zusätzlich die erdfesten Konventionen aus docs/specs/contracts.md (x Osten, y Norden).

## Anwendungsgrenzen der Verfahren

### [Koordinatensysteme, Vorzeichen und Schlupfdefinition](theory.md#iso8855_conventions)

Gilt für den klassischen Simulator. Die AD-Plattform (`vdsim.framework.types`) nutzt erdfest x Osten, y Norden; beide Systeme sind mathematisch positiv und damit verträglich.

### [Parameterschema und klassische Registry](theory.md#parameter_schema)

Keine Versionierung, keine Typprüfung der Konstruktorargumente.
