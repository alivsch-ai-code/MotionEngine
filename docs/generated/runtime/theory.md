# Laufzeitumgebung – Graph, Executor, Debugging, Versionierung, Custom Nodes – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


Übernommen aus [vdsim/runtime/docs/theory.md](../../../vdsim/runtime/docs/theory.md).

Dieses Kapitel beschreibt die Verfahren des Pakets `vdsim.runtime`: das Ausführungsmodell des Executors, Multi-Rate mit Halteglied, die Behandlung algebraischer Schleifen, den Determinismus, die C-ABI der nativen Custom Nodes, den Hot-Reload-Ablauf, das Versionierungsmodell und die diskreten Grundblöcke.

## Ausführungsmodell und Zeitdiskretisierung {#synchronous_dataflow}

### Ziel und Zweck
Ein Graph aus Komponenten soll so ausgeführt werden, dass jede Komponente in jedem Schritt die aktuellen Werte ihrer Eingänge sieht, Regelkreise geschlossen werden können und das Ergebnis unabhängig von der Rechenzeit ist.

### Theorie
Der Executor folgt dem synchronen Datenflussmodell zeitdiskreter Blockdiagramme (Simulink, synchrone Sprachen): Alle Blöcke reagieren logisch gleichzeitig auf den Zeitpunkt $t_k$. Die Reihenfolge innerhalb des Schritts ergibt sich nur aus den Datenabhängigkeiten. Ein Basisschritt besteht aus vier Phasen:

1. `output(t_k)` aller fälligen Blöcke ohne Durchgriff (Ausgang hängt nur vom Zustand ab)
2. `step(t_k, u)` aller fälligen Blöcke mit Durchgriff in topologischer Reihenfolge
3. `update(t_k, u, T_i)` aller fälligen Blöcke ohne Durchgriff (Zustand um die eigene Periode fortschreiben)
4. Übernahme der Rückführungswerte, Aufzeichnung, Schritt-Listener

Die Zeit wird ganzzahlig geführt:

$$t_k = \mathrm{round}(k\,\Delta t,\ 12)$$

### Herleitung
Für einen Block mit Zustand $x$, Eingang $u$ und Ausgang $y$ gilt zeitdiskret $y_k = g(x_k, u_k)$ und $x_{k+1} = f(x_k, u_k)$. Hängt $g$ nicht von $u_k$ ab (kein Durchgriff), kann $y_k$ vor allen anderen Blöcken berechnet werden (Phase 1). Die Blöcke mit Durchgriff bilden einen gerichteten Graphen; ist er azyklisch, liefert eine topologische Sortierung eine gültige Reihenfolge (Phase 2). Erst wenn alle $u_k$ bekannt sind, wird $x_{k+1}$ berechnet (Phase 3).

### Annahmen
- Komponenten sind zeitdiskret; kontinuierliche Dynamik integrieren sie intern (z. B. mit Teilschritten).
- Ausgänge sind Funktionen von Zustand, Zeit und Eingängen; Komponenten haben keine verdeckten Kanäle untereinander.

### Randbedingungen
- Jede Periode ist ein ganzzahliges Vielfaches des Basisschritts.
- Jeder Eingang hat höchstens eine Quelle.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\Delta t$ | Basisschritt | s | `graph.base_dt` |
| $k$ | Schrittindex | – | `executor.tick` |
| $t_k$ | Zeitpunkt des Schritts | s | `executor.t` |
| $T_i$ | Periode des Knotens $i$ | s | `node.period`, `_RT.dt` |

### Anwendungsgrenzen
Steife oder ereignisgetriebene Systeme mit variabler Schrittweite werden nicht unterstützt; Nulldurchgänge werden nicht detektiert.

### Vor- und Nachteile
Vorteile: einfache, vorhersagbare Semantik, wie in Simulink und in Steuergeräten. Nachteile: Rückführungen über Blöcke mit Durchgriff brauchen einen expliziten Verzögerungsblock oder Rückführungs-Port.

### Numerische Aspekte
Durch die ganzzahlige Zeitführung entsteht auch nach $10^6$ Schritten keine Drift; $t_k$ ist auf 12 Dezimalstellen gerundet und damit für Vergleiche wie $t \ge t_\mathrm{Sprung}$ stabil.

### Praktische Auswirkungen
Ein Planer mit 10 Hz und ein Regler mit 100 Hz laufen exakt in den vorgesehenen Schritten. Ergebnisse sind zwischen Rechnern und Läufen vergleichbar.

### In einfachen Worten
Die Simulation läuft in festen Takten. In jedem Takt rechnet jeder Baustein, sobald alle seine Eingangswerte feststehen. Bausteine mit Gedächtnis (z. B. das Fahrzeug) geben zuerst ihren aktuellen Stand aus und rechnen erst am Ende des Takts weiter.

### Quellen
[[MathWorks (2024)](../references.md#simulink_exec)], [[Lee und Seshia (2017, Kap. 5–6)](../references.md#lee_seshia2017)], [[Edwards und Lee (2003)](../references.md#edwards_lee2003)]

## Multi-Rate und Halteglied {#multirate_zoh}

### Ziel und Zweck
Komponenten mit unterschiedlichen Abtastraten (Planer 10 Hz, Regler 100 Hz, Strecke 1 kHz) sollen in einem Graphen zusammenarbeiten.

### Theorie
Knoten $i$ mit Periode $T_i = n_i\,\Delta t$ rechnet genau in den Schritten mit $k \bmod n_i = 0$. Dazwischen hält er seine Ausgänge (Zero-Order-Hold):

$$y_i(t_k) = y_i(t_{m n_i}),\quad m = \lfloor k / n_i \rfloor$$

### Herleitung
Das Halteglied ergibt sich daraus, dass der Wertespeicher `executor.values` nur überschrieben wird, wenn der Knoten rechnet. Ein schneller Knoten, der einen langsamen liest, sieht daher immer den zuletzt berechneten Wert. Ein langsamer Knoten, der einen schnellen liest, tastet ihn zu seinen eigenen Zeitpunkten ab.

### Annahmen
- Alle Knoten beginnen bei $k = 0$ (keine Phasenverschiebung).
- `update()` erhält $T_i$ als Schrittweite.

### Randbedingungen
$T_i / \Delta t$ muss bis auf $10^{-9}$ ganzzahlig sein, sonst meldet die Validierung einen Fehler.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $n_i$ | Ticks je Abtastung | – | `graph.period_ticks(id)` |
| $T_i$ | Periode | s | `node.effective_period` |

### Anwendungsgrenzen
Keine Ratenübergangsblöcke mit Interpolation; Aliasing beim Unterabtasten wird nicht verhindert.

### Vor- und Nachteile
Einfach und deterministisch. Abtasten ohne Tiefpass kann Aliasing erzeugen; das ist bewusst sichtbar, weil reale Steuergeräte genauso arbeiten.

### Numerische Aspekte
Der Vergleich $k \bmod n_i$ ist exakt (ganzzahlig).

### Praktische Auswirkungen
Der Test `test_multirate_timing_exact_and_zoh` zeigt, dass ein 10-Hz-Knoten nach 1000 s genau bei $t = 1000{,}0$ s rechnet.

### In einfachen Worten
Langsame Bausteine rechnen nur jeden n-ten Takt und lassen ihren Ausgang dazwischen stehen, wie eine Anzeige, die nur ab und zu aktualisiert wird.

### Quellen
[[MathWorks (2024)](../references.md#simulink_exec)], [[Lee und Seshia (2017, Kap. 6)](../references.md#lee_seshia2017)]

## Algebraische Schleifen {#algebraic_loop}

### Ziel und Zweck
Rückkopplungen ohne Verzögerung haben keine eindeutige Berechnungsreihenfolge. Sie sollen erkannt und mit einer verständlichen Abhilfe gemeldet werden.

### Theorie
Kanten des Abhängigkeitsgraphen sind alle Verbindungen $u.\mathrm{out} \to v.\mathrm{in}$ zwischen Knoten mit Durchgriff, außer wenn der Eingang ein Rückführungs-Port ist (`feedback=True`). Ausgänge von Knoten ohne Durchgriff erzeugen keine Kante. Eine algebraische Schleife ist eine stark zusammenhängende Komponente mit mehr als einem Knoten oder eine Selbstkante.

### Herleitung
Ein Rückführungs-Port liest $y(t_{k-1})$ statt $y(t_k)$; damit hängt der Empfänger nicht vom aktuellen Wert ab und die Kante entfällt. Ein Block ohne Durchgriff liefert $y_k = g(x_k)$ ohne $u_k$; auch hier entfällt die Abhängigkeit. Die verbleibende Relation ist genau dann eine Halbordnung, wenn sie zyklenfrei ist. Die Zyklen findet der Tarjan-Algorithmus in $O(V + E)$, die Reihenfolge der Algorithmus von Kahn mit Einfügereihenfolge als Gleichstandsregel.

### Annahmen
Die Durchgriffseigenschaft (`DIRECT_FEEDTHROUGH`) und die Rückführungs-Ports sind korrekt deklariert.

### Randbedingungen
Rückführungs-Ports dürfen unverbunden sein (`optional=True`) und liefern im ersten Schritt `None`.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $G = (V, E)$ | Abhängigkeitsgraph | – | `Graph._dependency_edges()` |
| SCC | stark zusammenhängende Komponente | – | `_tarjan()` |

### Anwendungsgrenzen
Schleifen werden nicht iterativ gelöst; echte algebraische Gleichungssysteme müssen in einer Komponente gelöst werden.

### Vor- und Nachteile
Eindeutige, vorab prüfbare Semantik. Die zusätzliche Verzögerung durch UnitDelay oder Rückführung muss bei der Auslegung berücksichtigt werden.

### Numerische Aspekte
Keine; die Prüfung ist rein kombinatorisch.

### Praktische Auswirkungen
Die Meldung nennt die beteiligten Verbindungen und schlägt UnitDelay, Integrator oder einen Rückführungs-Port vor. Der Planer liest so den Reglerstatus des Vorschritts (Bi-level-Stabilisierung).

### In einfachen Worten
Wenn A auf B wartet und B auf A, kann keiner anfangen. Ein Verzögerungsglied oder ein Rückführungs-Port löst das auf, weil dann einer der beiden den Wert vom letzten Takt nimmt.

### Quellen
[[MathWorks (2024)](../references.md#simulink_exec)], [[Lee und Seshia (2017, Kap. 6)](../references.md#lee_seshia2017)], [[Werling (2011, Abschn. 2.3)](../references.md#werling2011)]

## Determinismus {#deterministic_execution}

### Ziel und Zweck
Zwei Läufe mit gleichem Graphen, gleichen Parametern und gleichem Seed sollen bitgleiche Ergebnisse liefern.

### Theorie
Die Ausführung ist eine reine Funktion von Graph, Parametern und Seed, wenn (1) die Reihenfolge eindeutig ist, (2) die Zeit nicht von der Wanduhr abhängt und (3) Zufall nur aus Generatoren mit festem Seed stammt.

### Herleitung
(1) Kahn mit Prioritätswarteschlange über die Einfügereihenfolge liefert eine eindeutige Sortierung; es wird nirgends über Mengen von Zeichenketten iteriert (Hash-Randomisierung). (2) $t_k$ ist ganzzahlig definiert; die Wanduhr wird nur für Profiler und Echtzeitmodus verwendet und beeinflusst nur, wie viele Schritte gerechnet werden, nicht deren Ergebnis. (3) `RunContext.rng(name)` liefert pro Komponente einen eigenen Generator mit Seed $\mathrm{sha256}(\mathrm{seed}/\mathrm{name})$; native Nodes erhalten diesen Seed in `vdsim_reset`.

### Annahmen
Komponenten halten sich an die Regel „Zufall nur über `context.rng`“, und native Bibliotheken rechnen IEEE-754-konform (keine schnellen Mathematikoptionen).

### Randbedingungen
Gleiche Plattform und gleiche Bibliotheksversionen; zwischen Betriebssystemen können libm-Funktionen im letzten Bit abweichen.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| seed | Szenario-Seed | – | `RunContext.seed` |

### Anwendungsgrenzen
Ein Echtzeitlauf mit `advance()` ist bis auf die Anzahl der gerechneten Schritte deterministisch.

### Vor- und Nachteile
Reproduzierbare Fehlersuche und Regressionstests. Komponenten dürfen keine Wanduhr verwenden.

### Numerische Aspekte
Der Pure-Pursuit-Regler liefert in Python, Rust und C++ bitgleiche Ergebnisse, weil alle drei dieselbe Operationsfolge und dieselbe CRT-Mathematik verwenden.

### Praktische Auswirkungen
`test_determinism_bit_identical` vergleicht die Aufzeichnungen zweier Läufe byteweise.

### In einfachen Worten
Gleiche Eingaben ergeben immer genau das gleiche Ergebnis, bis zur letzten Nachkommastelle.

### Quellen
[[Lee und Seshia (2017, Kap. 6)](../references.md#lee_seshia2017)], [[Edwards und Lee (2003)](../references.md#edwards_lee2003)]

## C-ABI der nativen Custom Nodes {#c_abi}

### Ziel und Zweck
Algorithmen in Rust, C++ oder C sollen mit denselben Ports wie native Python-Komponenten laufen, ohne Abhängigkeit von der Python-ABI.

### Theorie
Die Schnittstelle besteht aus C-Funktionen, die ausschließlich Zeiger auf `double`-Puffer, Längen und einen undurchsichtigen Handle austauschen (Version 1):

| Funktion | Aufgabe |
|---|---|
| `uint32_t vdsim_abi_version(void)` | ABI-Version (1) |
| `const char* vdsim_node_info(void)` | JSON: Name, Ebene, Version, Ports (Typnamen aus `framework.types`), Parameter (Name, Default, Label, Einheit) |
| `void* vdsim_create(const double* p, size_t n)` | Instanz mit Parametern in deklarierter Reihenfolge |
| `void vdsim_destroy(void* h)` | freigeben |
| `int32_t vdsim_reset(void* h, double dt, uint64_t seed)` | Zurücksetzen |
| `int32_t vdsim_step(h, t, n_in, in, in_len, n_out, out, out_cap, out_len)` | Schritt (mit Durchgriff) |
| `int32_t vdsim_fetch_outputs(h, n_out, out, out_cap, out_len)` | Ausgänge erneut kopieren, nachdem der Host Puffer vergrößert hat |
| `int32_t vdsim_output(h, t, n_out, out, out_cap, out_len)` / `vdsim_update(h, t, dt, n_in, in, in_len)` | Blöcke ohne Durchgriff |
| `size_t vdsim_get_state(h, buf, cap)` / `int32_t vdsim_set_state(h, buf, n)` | Zustand für Hot Reload |
| `const char* vdsim_last_error(h)` | Fehlermeldung |

Rückgabewerte: 0 = in Ordnung, 1 = Ausgangspuffer zu klein (benötigte Längen stehen in `out_len`), < 0 = Fehler. `out_len = 0` heißt „Ausgang nicht gesetzt“ (der Host hält den alten Wert). Nicht verbundene Eingänge haben die Länge 0.

### Herleitung
Die Werte werden mit den flachen Codecs aus contracts.md, Abschn. 5, kodiert (`framework.types.encode/decode`, ergänzt um `ControllerStatus`, `ControlInput`, `ActuatorCommand` in `runtime.codecs`). Die Header `vdsim_node.h` und `vdsim_node.rs` werden aus denselben Feldlisten erzeugt (`runtime.codegen`), sodass Layout-Konstanten, Strukturen und Python-Codecs nicht auseinanderlaufen können.

### Annahmen
- x86-64, `double` ist IEEE-754, `size_t` hat 64 bit.
- Ausnahmen bzw. Panics verlassen die Bibliothek nicht; die generierten Hüllen fangen sie ab.

### Randbedingungen
Nur Typen mit flachem Codec sind als Ports zulässig; der Loader prüft das beim Laden.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| `in[i]`, `in_len[i]` | Eingangspuffer i | – | `NativeComponent._in_ptrs` |
| `out_cap[i]` | Kapazität des Ausgangspuffers | – | `NativeComponent._out_caps` |

### Anwendungsgrenzen
Typen mit Zeichenketten oder verschachtelten Objekten (BehaviorCommand, PlannerDebug) haben noch keinen Codec.

### Vor- und Nachteile
Sprachneutral, keine Build-Abhängigkeiten, stabile ABI. Nachteil: Kodierung und ctypes-Aufruf kosten einige Mikrosekunden je Aufruf.

### Numerische Aspekte
NaN kodiert „nicht gesetzt“ (optionale Felder von ControlCommand). Ganzzahlige Felder werden gerundet.

### Praktische Auswirkungen
Der Test `test_rust_codec_roundtrip_all_types` schickt Werte aller Typen durch einen nativen Echo-Node und vergleicht die Kodierung bitweise.

### In einfachen Worten
Python und der native Code sprechen über einfache Zahlenlisten miteinander. Welche Zahl an welcher Stelle steht, ist fest vereinbart und wird für beide Seiten aus derselben Quelle erzeugt.

### Quellen
[[Project (2024)](../references.md#rust_ffi)], [[Foundation (2024)](../references.md#python_ctypes)], [[Microsoft (2024)](../references.md#msvc_dll)], [[Project (2024)](../references.md#cargo_book)]

## Hot Reload {#hot_reload}

### Ziel und Zweck
Custom Nodes sollen während einer laufenden Simulation geändert werden können, ohne den Zustand zu verlieren.

### Theorie
Ablauf in `HotReloader`:

1. Polling der Änderungszeit der Quelldateien (`mtime`, Größe).
2. Vorbereitung: Python lädt die Datei unter einem neuen Modulnamen; nativ wird neu gebaut (optional im Hintergrund-Thread).
3. Neue Instanz mit den Parametern der alten, `reset(context)`, dann `set_state(old.get_state())`.
4. Haben sich die Ports geändert, wird der Graph neu validiert; ist er ungültig, bleibt die alte Instanz aktiv.
5. Austausch im Graphen; der Executor kompiliert vor dem nächsten Schritt neu; die alte Instanz wird geschlossen (`FreeLibrary`).

### Herleitung
Für native Bibliotheken wird die DLL vor dem Laden in einen Schattenpfad `name_<pid>_<n>.dll` kopiert. Windows sperrt nur die Kopie, der Compiler kann das Original überschreiben. Jede Version hat einen eigenen Schattenpfad, sodass alte und neue Bibliothek kurzzeitig gleichzeitig geladen sein können (Zustandsübertragung).

### Annahmen
`get_state()` liefert den vollständigen Zustand; bei geänderter Zustandsstruktur ist die Komponente selbst für die Übersetzung zuständig.

### Randbedingungen
Fehler beim Laden, Bauen oder Übertragen lassen die alte Instanz aktiv und werden gemeldet; derselbe fehlerhafte Dateistand wird nicht erneut versucht.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| stamp | (mtime_ns, Größe bzw. Anzahl) | – | `PythonSource.stamp`, `NativeSource.stamp` |

### Anwendungsgrenzen
Von der Node-Datei importierte Hilfsmodule werden nicht neu geladen.

### Vor- und Nachteile
Kurze Iterationszyklen beim Reglerentwurf. Der Zustand der neuen Version kann inkonsistent sein, wenn sich seine Bedeutung geändert hat.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Ein Rust-Node wird bei einer Quelländerung in etwa 1–3 s neu gebaut und ausgetauscht.

### In einfachen Worten
Man speichert seinen Code, und die laufende Simulation übernimmt die neue Version, ohne von vorne anzufangen.

### Quellen
[[Foundation (2024)](../references.md#python_ctypes)], [[Microsoft (2024)](../references.md#msvc_dll)], [[Project (2024)](../references.md#rust_ffi)]

## Versionierungsmodell {#content_addressed_versioning}

### Ziel und Zweck
Änderungen an Graphen und Komponentenkonfigurationen sollen nachvollziehbar, vergleichbar und umkehrbar sein.

### Theorie
Jeder Schnappschuss ist das vollständige JSON-Dokument. Er wird über den SHA-256-Hash der kanonischen Darstellung (sortierte Schlüssel) identifiziert. Der Index `.history/<name>/index.json` speichert Kennung, Elternversion, Zeitstempel, Nachricht, Autor und Hash. Wiederherstellen schreibt den alten Stand zurück und legt einen neuen Schnappschuss an, die Historie bleibt also linear und vollständig. Komponentenversionen werden pro Knoten gepinnt (`version`); beim Laden wird die gepinnte Version bevorzugt und Abweichungen werden gewarnt.

### Herleitung
Gleicher Hash bedeutet gleicher Inhalt; ein Schnappschuss ohne Änderung erzeugt deshalb keine neue Version. Der Diff vergleicht Knoten nach ID, Parameter als flache Schlüssel (`params.cost.k_jerk`) und Verbindungen als Paare.

### Annahmen
Graphdateien sind klein (kB), vollständige Kopien sind unkritisch.

### Randbedingungen
Liegt die Datei in einem Git-Repository, wird jeder Schnappschuss zusätzlich committet (`git="auto"`).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $h$ | SHA-256 des kanonischen JSON | – | `Version.hash` |

### Anwendungsgrenzen
Keine Verzweigungen oder Zusammenführungen; dafür ist Git zuständig.

### Vor- und Nachteile
Robust und ohne externe Werkzeuge nutzbar. Speicherbedarf wächst linear mit der Anzahl der Versionen.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Der Editor kann vor jedem Lauf einen Schnappschuss anlegen und Ergebnisse mit dem Hash verknüpfen.

### In einfachen Worten
Jeder gespeicherte Stand bekommt einen Fingerabdruck. Man kann zwei Stände vergleichen und jederzeit zu einem alten zurückkehren.

### Quellen
[[Chacon und Straub (2014)](../references.md#git_book)]

## Diskrete Grundblöcke {#discrete_blocks}

### Ziel und Zweck
Integrator und PT1-Glied sind die Grundbausteine einfacher Regelkreise im Editor.

### Theorie
Integrator (explizites Euler-Verfahren, ohne Durchgriff):

$$y_{k+1} = \mathrm{sat}(y_k + K\,T_s\,u_k)$$

PT1-Glied, sprunginvariant diskretisiert (mit Durchgriff):

$$y_k = a\,y_{k-1} + (1 - a)\,K\,u_k,\quad a = e^{-T_s/T}$$

### Herleitung
Für $\dot y = (K u - y)/T$ und konstantes $u$ über ein Abtastintervall ist die exakte Lösung $y(t + T_s) = e^{-T_s/T} y(t) + (1 - e^{-T_s/T}) K u$. Der Integrator folgt aus $\dot y = K u$ mit Euler vorwärts.

### Annahmen
Eingang konstant über das Abtastintervall (Halteglied).

### Randbedingungen
$T > 0$; für $T = 0$ ist das PT1-Glied eine Verstärkung.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $T_s$ | Abtastzeit des Knotens | s | `sample_time` |
| $T$ | Zeitkonstante | s | `LowPassParams.T` |
| $K$ | Verstärkung | – | `k`, `K` |

### Anwendungsgrenzen
Der Euler-Integrator ist für $K T_s > 2$ in einem Regelkreis mit Verstärkung 1 instabil.

### Vor- und Nachteile
Einfach und exakt nachvollziehbar; der geschlossene Kreis hat die analytische Lösung $y_k = 1 - (1 - K T_s)^k$.

### Numerische Aspekte
Der Test `test_two_phase_integrator_loop_exact` vergleicht mit dieser Lösung bis auf $10^{-14}$.

### Praktische Auswirkungen
Der Integrator hat keinen Durchgriff und bricht daher Regelkreise auf.

### In einfachen Worten
Der Integrator summiert seinen Eingang auf, das PT1-Glied folgt seinem Eingang verzögert wie ein Thermometer.

### Quellen
[[Lee und Seshia (2017, Kap. 2)](../references.md#lee_seshia2017)], [[MathWorks (2024)](../references.md#simulink_exec)]

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Algebraische Schleifen](theory.md#algebraic_loop) | – | – | [Lee und Seshia (2017)](../references.md#lee_seshia2017), [MathWorks (2024)](../references.md#simulink_exec), [Werling (2011)](../references.md#werling2011) |
| [C-ABI der nativen Custom Nodes](theory.md#c_abi) | – | – | [Project (2024)](../references.md#cargo_book), [Microsoft (2024)](../references.md#msvc_dll), [Foundation (2024)](../references.md#python_ctypes), [Project (2024)](../references.md#rust_ffi) |
| [Versionierungsmodell](theory.md#content_addressed_versioning) | – | – | [Chacon und Straub (2014)](../references.md#git_book) |
| [Determinismus](theory.md#deterministic_execution) | – | – | [Edwards und Lee (2003)](../references.md#edwards_lee2003), [Lee und Seshia (2017)](../references.md#lee_seshia2017) |
| [Diskrete Grundblöcke](theory.md#discrete_blocks) | [`blocks.Integrator.update`](../../../vdsim/runtime/blocks.py#L367), [`blocks.LowPass.step`](../../../vdsim/runtime/blocks.py#L396) | [`node/integrator`](components/node__integrator.md), [`node/lowpass`](components/node__lowpass.md) | [Lee und Seshia (2017)](../references.md#lee_seshia2017), [MathWorks (2024)](../references.md#simulink_exec) |
| [Hot Reload](theory.md#hot_reload) | – | – | [Microsoft (2024)](../references.md#msvc_dll), [Foundation (2024)](../references.md#python_ctypes), [Project (2024)](../references.md#rust_ffi) |
| [Multi-Rate und Halteglied](theory.md#multirate_zoh) | – | – | [Lee und Seshia (2017)](../references.md#lee_seshia2017), [MathWorks (2024)](../references.md#simulink_exec) |
| [Ausführungsmodell und Zeitdiskretisierung](theory.md#synchronous_dataflow) | – | – | [Edwards und Lee (2003)](../references.md#edwards_lee2003), [Lee und Seshia (2017)](../references.md#lee_seshia2017), [MathWorks (2024)](../references.md#simulink_exec) |
