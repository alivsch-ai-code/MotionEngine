# Theorie: Komponenten-Framework

## Komponentenmodell mit typisierten Ports {#component_model}

### Ziel und Zweck
Einheitliche Beschreibung aller Bausteine der Wirkkette, damit Komponenten derselben Ebene austauschbar, prüfbar und dokumentierbar sind.

### Theorie
Eine Komponente ist ein zeitdiskretes System

$$\mathbf{y}_k = g(\mathbf{x}_k, \mathbf{u}_k, \mathbf{p}), \qquad \mathbf{x}_{k+1} = f(\mathbf{x}_k, \mathbf{u}_k, \mathbf{p}, \Delta t)$$

mit benannten, typisierten Eingängen $\mathbf{u}$, Ausgängen $\mathbf{y}$, Parametern $\mathbf{p}$ und internem Zustand $\mathbf{x}$. Komponenten mit Durchgriff implementieren `step()` (= $g$ und $f$ zusammen). Komponenten ohne Durchgriff ($g$ hängt nicht von $\mathbf{u}_k$ ab) implementieren `output()` und `update()`; der Executor ruft zuerst alle `output()` auf und kann so Rückkopplungsschleifen ohne algebraische Schleife auswerten. Rückführungs-Ports lesen den Wert des vorherigen Schritts ($\mathbf{u}_k = \mathbf{y}_{k-1}$).

### Herleitung
Eine Schleife ist genau dann algebraisch, wenn alle Komponenten auf ihr direkten Durchgriff haben. Eine Komponente ohne Durchgriff oder ein Rückführungs-Port (Verzögerung um einen Schritt) auf jeder Schleife genügt, damit eine topologische Ausführungsreihenfolge existiert (Prinzip der Blockdiagramm-Simulation).

### Annahmen
Jede Komponente kennt ihre Ports statisch (Klassenattribute); Custom Nodes dürfen Ports dynamisch über `ports()` melden.

### Randbedingungen
Pflichtattribute KIND, NAME, VERSION, LABEL, INPUTS, OUTPUTS, PARAMS, PERIOD, DOC (docs/specs/contracts.md, Abschn. 3).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\mathbf{u}, \mathbf{y}$ | Eingänge, Ausgänge | – | `INPUTS`, `OUTPUTS` |
| $\mathbf{p}$ | Parameter | – | `PARAMS`, `self.params` |
| $\mathbf{x}$ | interner Zustand | – | `get_state()` |
| $\Delta t$ | Periode | s | `PERIOD` |

### Anwendungsgrenzen
Ereignisdiskrete Logik muss in diskreten Schritten abgebildet werden.

### Vor- und Nachteile
- Vorteil: austauschbar, testbar, automatische Dokumentation über `describe()`.
- Nachteil: Mehraufwand für sehr kleine Bausteine.

### Numerische Aspekte
Hot Reload überträgt den Zustand per `get_state()`/`set_state()`.

### Praktische Auswirkungen
Planer, Regler und Fahrzeugmodelle aus verschiedenen Paketen und Sprachen lassen sich im Grapheditor verbinden.

### In einfachen Worten
Jeder Baustein hat beschriftete Stecker mit festgelegtem Datentyp. Passt der Stecker, kann man Bausteine beliebig tauschen.

### Quellen
[@martin2017], [@werling2011, Abschn. 2.3]

## Versionierte Plugin-Registry {#plugin_registry}

### Ziel und Zweck
Komponenten über Namen und Versionsbereiche finden und erzeugen; mehrere Versionen parallel.

### Theorie
Abbildung $(\mathrm{kind}, \mathrm{name}) \mapsto \{\mathrm{version} \mapsto \mathrm{Klasse}\}$. Auflösung eines Spec-Strings: aus allen passenden Versionen wird die höchste gewählt. Bereiche:

- `^M.m.p`: $v_1 = M$ und $v \ge (M, m, p)$
- `~M.m.p`: $(v_1, v_2) = (M, m)$ und $v \ge (M, m, p)$
- `>=M.m.p` sowie exakte Gleichheit (Versionsvergleich lexikografisch auf Zahlentripeln).

### Herleitung
Semantic Versioning: Änderungen der MAJOR-Version sind inkompatibel, MINOR fügt kompatible Funktionen hinzu, PATCH behebt Fehler. Ein Graph, der `^1` verlangt, erhält deshalb die neueste kompatible Version.

### Annahmen
Versionen im Format MAJOR.MINOR.PATCH; fehlende Teile werden mit 0 ergänzt.

### Randbedingungen
Eingebaute Pakete aus `BUILTIN_MODULES` werden beim ersten Zugriff importiert.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $v$ | Version als Tripel | – | `parse_version()` |
| Bereich | Versionsbedingung | – | `constraint` |

### Anwendungsgrenzen
Keine Vorabversionen und Build-Metadaten.

### Vor- und Nachteile
- Vorteil: reproduzierbar (Ergebnisse speichern die exakte Version), erweiterbar.
- Nachteil: globale Registry (Tests müssen Registrierungen aufräumen).

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
`trajectory_planner/werling@^1` bleibt nach einer Fehlerkorrektur gültig.

### In einfachen Worten
Eine Bibliothek mit Bausteinen, die jeder Baustein mit Name und Versionsnummer betritt; man kann „die neueste 1er-Version“ ausleihen.

### Quellen
[@semver2]

## Dependency Injection und Laufzeitkontext {#dependency_injection}

### Ziel und Zweck
Komponenten erhalten alles, was sie aus der Umgebung brauchen (Zeitschritt, Fahrzeug, Straße, Dienste), statt globalen Zustand zu lesen.

### Theorie
Ein Container bildet Schlüssel auf Fabriken ab; `resolve(key)` erzeugt rekursiv Abhängigkeiten (Fabriken bekommen den Container), merkt sich Singletons und erkennt Zyklen. Untergeordnete Scopes überschreiben Registrierungen und fallen sonst auf den Elterncontainer zurück. Der `RunContext` wird in `reset()` übergeben.

### Herleitung
Inversion of Control: Nicht die Komponente erzeugt ihre Abhängigkeiten, sondern die Umgebung reicht sie hinein. Das entkoppelt Algorithmen von Infrastruktur und macht sie testbar.

### Annahmen
Fabriken sind seiteneffektfrei bis auf die Objekterzeugung.

### Randbedingungen
Zyklische Abhängigkeiten führen zu `RuntimeError`.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| key | Dienstname | – | `key` |
| factory | Fabrikfunktion | – | `_factories` |
| scope | Kindcontainer | – | `scope()` |

### Anwendungsgrenzen
Keine Threadsicherheit.

### Vor- und Nachteile
- Vorteil: Batchläufe mit anderem Regler über einen Scope, ohne Code zu ändern.
- Nachteil: Abhängigkeiten sind erst zur Laufzeit sichtbar.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Runner und Tests stellen Straße, Fahrzeug und Dienste über Kontext und Container bereit.

### In einfachen Worten
Komponenten bekommen ihre Werkzeuge gereicht, statt sie selbst im Haus zu suchen.

### Quellen
[@fowler2004], [@martin2017]

## Deterministische Zufallszahlen und Reproduzierbarkeit {#deterministic_seeding}

### Ziel und Zweck
Bitgenau reproduzierbare Läufe, auch mit Rauschen und Monte-Carlo-Studien.

### Theorie
Jede Komponente erhält einen eigenen Zufallsstrom

$$\mathrm{seed}(\mathrm{Szenario}, \mathrm{Name}) = \mathrm{int}\left(\mathrm{SHA256}(\mathrm{seed} / \mathrm{name})_{0..3}\right)$$

(die ersten 4 Byte, little endian) und `numpy.random.default_rng(seed)`. Das Manifest speichert Versionen, Plattform, Git-Commit, Seed und einen SHA-256-Hash der Konfiguration.

### Herleitung
Hashfunktionen liefern für gleiche Eingaben gleiche, für unterschiedliche Namen praktisch unabhängige Startwerte; so beeinflusst eine neue Komponente die Zufallsfolgen der anderen nicht.

### Annahmen
Keine Wanduhrzeit und kein globaler Zufall in der Logik.

### Randbedingungen
32-Bit-Seeds.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| seed | Szenario-Seed | – | `RunContext.seed` |
| name | Stromname | – | `rng(name)` |

### Anwendungsgrenzen
Reproduzierbar nur bei gleichen Bibliotheksversionen (im Manifest dokumentiert).

### Vor- und Nachteile
- Vorteil: unabhängig von Aufrufreihenfolge und PYTHONHASHSEED.
- Nachteil: Kollisionen bei 32 Bit theoretisch möglich.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Monte-Carlo-Studien und Regressionstests liefern identische Zahlen.

### In einfachen Worten
Jeder Baustein bekommt seinen eigenen Würfel, der bei gleichem Szenario immer gleich fällt.

### Quellen
[@martin2017]

## Signaltypen und Codecs {#signal_type_system}

### Ziel und Zweck
Verbindliche Datentypen zwischen den Ebenen und flache Darstellung für native Komponenten (C++/Rust).

### Theorie
Typregistry `TYPES` (Name → Python-Typ); eine Verbindung Ausgang → Eingang ist zulässig, wenn die Namen gleich sind, einer `Any` ist oder beide aus {float, Vector} stammen. Codecs bilden jeden Typ auf ein float64-Array ab (Layouts in docs/specs/contracts.md, Abschn. 5), z. B. `EgoState` → [t, x, y, psi, vx, vy, r, ax, ay, delta, delta_rate, gear]; nicht gesetzte optionale Werte als NaN.

### Herleitung
Nominale Typisierung über Namen genügt für einen Grapheditor und ist sprachunabhängig.

### Annahmen
SI-Einheiten, erdfestes System x Osten, y Norden.

### Randbedingungen
Neue Typen über `register_type()`.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| TYPES | Typregistry | – | `TYPES` |
| compatible | Verbindungsprüfung | – | `compatible()` |

### Anwendungsgrenzen
Keine Einheitenprüfung an Ports (Einheiten nur dokumentiert).

### Vor- und Nachteile
- Vorteil: einfache, schnelle Prüfung; sprachneutrale Codecs.
- Nachteil: keine strukturelle Typprüfung.

### Numerische Aspekte
Codecs sind verlustfrei für float64.

### Praktische Auswirkungen
Der Wissensgraph verbindet Komponenten über ihre Port-Typen (consumes/produces).

### In einfachen Worten
Alle Bausteine einigen sich auf dieselben Datenformate, z. B. „Fahrzeugzustand“ oder „Solltrajektorie“.

### Quellen
[@martin2017]
