# Aktorik – Latenzkette, Lenkaktor, Kennlinienfehler – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Totzeiten müssen Vielfache des Reglertakts sein (es wird gerundet).
- Die Latenz ist dem Schätzer bekannt (internes Modell = reales System).
- Die Kennlinie ist symmetrisch und zeitinvariant; Hysterese, Spiel und Reibung im Lenkstrang fehlen.
- Nur die Lenkung hat eine Latenzkette; Antrieb und Bremse wirken verzögerungsfrei.

## Anwendungsgrenzen der Verfahren

### [Latenzkette aus Totzeit und PT1](theory.md#latency_chain)

Jitter und variable Buslast werden nicht abgebildet.

### [Wirkkette des Lenkaktors](theory.md#steering_actuator_chain)

Nur Vorderachslenkung; keine Lenkmomentschnittstelle.

### [Kennlinienfehler des Lenkaktors](theory.md#steering_characteristic_error)

Nur multiplikative, statische Fehler.
