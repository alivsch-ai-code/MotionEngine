# MATLAB-Integration: Verfahren

## Lexer und Parser {#matlab_parser}

### Ziel und Zweck
MATLAB-Quelltext von Reglern und Simulationen wird in einen abstrakten Syntaxbaum (AST) überführt. Dieser AST ist die gemeinsame Grundlage für Interpreter, Analyse und Code-Generatoren.

### Theorie
Die Grammatik ist kontextfrei bis auf drei lexikalische Sonderfälle:

1. `'` ist der Transpose-Operator, wenn ein Wert vorausgeht, und sonst ein String-Begrenzer.
2. In `[]` und `{}` trennen Leerzeichen Elemente: `[1 -2]` hat zwei Elemente, `[1 - 2]` eines.
3. `end` im Index bezeichnet den letzten Index.

Der Lexer löst diese Fälle mit einem Klammerstapel auf und fügt im Matrixliteral Kommas ein. Der Parser ist ein rekursiver Abstieg mit einer Funktion je Rangstufe:

$$\|\| < \&\& < | < \& < (<,\leq,>,\geq,==,\sim=) < : < (+,-) < (*,/,\backslash,.*,./) < \mathrm{unär} < (\hat{},.\hat{},',.')$$

Wie in MATLAB gilt: Unäres Minus bindet schwächer als die Potenz, also $-2^2=-4$. Der Exponent darf ein Vorzeichen tragen (`2^-1`).

Unterstützter Umfang:
- function-Dateien mit mehreren Ausgaben und Subfunctions, mit oder ohne `end`, verschachtelte Funktionen; Skripte mit lokalen Funktionen
- if/elseif/else, for (Bereiche, Vektoren, Matrizen spaltenweise), while, switch/case/otherwise (auch Zellen-Cases), break/continue/return, try/catch
- Bereiche `a:b:c`, Matrix- und Zellliterale, Indizierung bzw. Aufruf `f(x)`, `end` im Index, `x{i}`, `s.a`, `s.(name)`, anonyme Funktionen, Handles `@f`
- Strings `'…'` und `"…"`, Zahlen einschließlich `1e-3` und `2i`, Mehrfachzuweisung mit `~`
- global, persistent
- Kommentare `%` und `%{ … %}` (verschachtelt), Fortsetzung `...`, Befehlssyntax für `clc`, `clear all`, `format long` und Ähnliches

### Herleitung
Für jede Rangstufe $k$ gilt $E_k \to E_{k+1}\,(\mathrm{op}_k\,E_{k+1})^*$, also Linksassoziativität. Bereiche bilden eine Sonderstufe: $R \to A\,[:A\,[:A]]$. Postfix-Operationen werden iterativ an das Primärelement angehängt, nämlich Index, Zellindex, Feld und Transpose.

Ob Funktionen mit `end` abgeschlossen sind, wird vorab bestimmt:
- Ist die Zahl der `end` außerhalb von Indizes gleich der Zahl der Blocköffner einschließlich `function`, sind alle Funktionen mit `end` abgeschlossen.
- Ist sie um die Zahl der Funktionen kleiner, hat keine Funktion ein `end`.

### Annahmen
- Die Quelle ist syntaktisch gültiges MATLAB.
- Befehlssyntax wird nur für eine feste Liste von Anzeigebefehlen erkannt.

### Randbedingungen
- Kodierung UTF-8, ersatzweise Latin-1.
- Zeilenenden LF oder CRLF.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| Token | lexikalische Einheit mit Zeile und Spalte | – | `lexer.Token` |
| AST | Syntaxbaum | – | `nodes.MFile`, `nodes.Function` |

### Anwendungsgrenzen
Nicht unterstützt werden:
- `classdef`
- `eval`
- `arguments`-Blöcke
- Befehlssyntax beliebiger Funktionen
- `!`-Shell-Escape
- Matrix-Zeilen über `...` mit führenden Kommentaren

### Vor- und Nachteile
- Vorteile: kompakt und ohne Abhängigkeiten. Fehler werden mit Zeile und Spalte gemeldet. Kommentare bleiben erhalten und werden Anweisungen zugeordnet. Eine Gleichungsnummer in eigener Zeile gehört zur Anweisung darüber.
- Nachteil: Die Heuristiken (Befehlssyntax, Leerzeichen im Literal) decken nur gängigen Stil ab.

### Numerische Aspekte
Zahlen werden als IEEE-754-double gelesen; der Originaltext bleibt für die Codeausgabe erhalten.

### Praktische Auswirkungen
Syntaxfehler im importierten Skript erscheinen in der GUI und der CLI mit Position.

### In einfachen Worten
Das Programm liest das MATLAB-Skript Wort für Wort, erkennt Rechenzeichen und Befehle und baut daraus eine Baumstruktur, mit der der Rechner weiterarbeiten kann.

### Quellen
[@aho2006, Kap. 3–4], [@mathworks_precedence], [@mathworks_matlab]

## Interpreter und Semantik-Unterschiede {#matlab_interpreter}

### Ziel und Zweck
Die originale Regellogik wird ohne MATLAB ausgeführt. Sie dient als Referenz für alle Konvertierungen.

### Theorie
Der Interpreter wertet den AST direkt aus, ohne Zwischencode. Werte werden so dargestellt:
- Skalare als Python-float, -bool oder -complex
- Arrays als 2-D-numpy-Arrays
- Strings als `str`
- `MStruct`, `MCell`, `MFunction`

Namen werden in dieser Reihenfolge aufgelöst: Variable → lokale bzw. verschachtelte Funktion → Built-in (Registry) → `name.m` im Suchpfad.

Semantik-Unterschiede, die in Interpreter und Generatoren umgesetzt sind:

| Aspekt | MATLAB | Python/numpy | C++ | Rust |
|---|---|---|---|---|
| Indexbasis | 1 | 0 (Umrechnung `i - 1`) | `Mat(i)` 1-basiert | `Mat::get(i)` 1-basiert |
| Speicherordnung | spaltenweise | zeilenweise (C); lineare Indizes über `ravel(order="F")` | `Mat` spaltenweise | `Mat` spaltenweise |
| Vektoren | Spalten $n\times 1$ / Zeilen $1\times n$ | 2-D-Arrays (nicht 1-D) | `Mat` | `Mat` |
| Zuweisung | Kopiersemantik | Referenz: `.copy()` bzw. funktionales `m_set` | Wertsemantik | `.clone()` |
| `*` | Matrixprodukt | `@` | `mlab::matmul` | `mlab::matmul` |
| `^` | `x^2` | `x ** 2` | `std::pow` | `f64::powf` |
| `mod(-1,3)` | 2 | `m_mod` (Vorzeichen des Divisors) | `mlab::mod` | `mlab::modulo` |
| `round(2.5)` | 3 (weg von 0) | `m_round` (Python `round` = Banker's) | `std::round` | `f64::round` |
| `sign(0)` | 0 | `m_sign` | `mlab::sign` | `mlab::sign` (nicht `signum`) |
| `max(a, NaN)` | ignoriert NaN | `np.fmax`, `np.nanmax` | `std::fmax` | `f64::max` |
| `1/0` | Inf | ZeroDivisionError (Python-float) | Inf | Inf |
| `a:s:b` | $a+ks$ | `m_colon` | `mlab::colon` | `mlab::colon` |
| Wachsen `x(n+1)=v` | erlaubt | `m_set` | Ausnahme | panic |

### Herleitung
Der Colon-Operator wird mit $n=\lfloor (b-a)/s + 4\,\varepsilon \max(1,|q|)\rfloor$ und $x_k=a+ks$, $k=0\ldots n$ berechnet; das letzte Element wird auf $b$ begrenzt. `mod` wird als $r=\mathrm{fmod}(a,m)$ und $r+m$ bei verschiedenem Vorzeichen berechnet; das ist für alle Darstellungen exakt.

### Annahmen
- Reelle double-Rechnung.
- Skalare Ergebnisse werden zu Python-Skalaren normalisiert (1×1 → float), wie MATLAB jedes 1×1-Array als Skalar behandelt.

### Randbedingungen
- Höchstens 2 Dimensionen.
- Rekursionstiefe bis 256.
- Höchstens $10^7$ Iterationen je while-Schleife.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $a,s,b$ | Start, Schritt, Ende eines Bereichs | – | `m_colon(a, s, b)` |
| $\varepsilon$ | Maschinengenauigkeit | – | `eps` |

### Anwendungsgrenzen
- keine Ganzzahltypen (int8…uint64), keine single-Genauigkeit
- keine Struct-Arrays, keine N-D-Arrays, keine Klassen
- `rand`/`randn` deterministisch über einen Seed (nicht MATLAB-kompatible Folgen)

### Vor- und Nachteile
- Vorteile: kein MATLAB nötig, erweiterbar über `register_builtin`, deterministisch.
- Nachteil: Langsamer als kompilierter Code. Für Simulationen gibt es deshalb `backend="python"`.

### Numerische Aspekte
Skalare Funktionen laufen über `math`, Arrays über numpy, in denselben Aufrufen wie im generierten Python-Code. Das ergibt Bitgleichheit. Bei Definitionsbereichsfehlern wechselt der Interpreter auf komplexe Ergebnisse, etwa bei `sqrt(-1)`.

### Praktische Auswirkungen
Ein MATLAB-Regler lässt sich als Komponente in der Simulation betreiben. Persistente Zustände werden bei `reset()` gelöscht und beim Hot Reload übertragen.

### In einfachen Worten
Der Rechner spielt das MATLAB-Programm Schritt für Schritt nach. Dabei beachtet er die Eigenheiten von MATLAB, zum Beispiel dass das Zählen bei 1 beginnt.

### Quellen
[@mathworks_matlab], [@ieee754_2019]

## Typinferenz {#matlab_type_inference}

### Ziel und Zweck
Statisch typisierte Zielsprachen brauchen Typen, die Python-Ausgabe braucht die Unterscheidung Skalar/Matrix (z. B. `*` gegenüber `@`).

### Theorie
Verband: unknown ⊑ {scalar, bool, array(r×c), string, cell, struct, func}. Join: scalar ⊔ bool = scalar und scalar ⊔ array = array; bei abweichenden Größen wird die Größe unbekannt. Die Analyse ist flussunabhängig: Der Typ einer Variablen ist der Join über alle Zuweisungen, iteriert bis zum Fixpunkt (Schleifen). Lokale Funktionen werden je Argumentsignatur inferiert.

### Herleitung
Regeln (Auszug):
- elementweise Operationen: Broadcasting der Größen
- `A*B`: $(r_A \times c_B)$
- Index mit nur skalaren Argumenten: Skalar
- `zeros(m,n)` mit Literalen: feste Größe
- Reduktion eines Vektors: Skalar

### Annahmen
Eingänge sind skalar, sofern weder ein Hinweis noch die Verwendung etwas anderes nahelegen. Als Verwendung zählen indiziert, iteriert oder an `numel`/`sum`/… übergeben.

### Randbedingungen
Hinweise können übergeben werden:
- per `input_types={"x": "vector"}`
- als Kommentar `%#type x: vector(3)`, `%#type A: matrix(2,2)` oder `%#type v: row`

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\tau(x)$ | Typ der Variablen $x$ | – | `FunctionTypes.env[x]` |

### Anwendungsgrenzen
Variablen, die ihren Typ wechseln (zuerst Skalar, dann Matrix), werden als Matrix geführt. Im Native-Code ergibt das eine Diagnose.

### Vor- und Nachteile
Einfach und robust. Typen, die vom Programmpfad abhängen, werden nicht unterschieden.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Bestimmt die Porttypen der Komponente (`float` oder `Vector`) und die Deklarationen in C++/Rust.

### In einfachen Worten
Das Programm findet heraus, welche Größen einzelne Zahlen und welche Zahlenlisten oder Tabellen sind.

### Quellen
[@aho2006, Kap. 6]

## Analyse der Regellogik {#matlab_analysis}

### Ziel und Zweck
Die Regellogik wird für GUI und Dokumentation darstellbar: wer wovon abhängt, welche Gleichung wo umgesetzt ist, wie komplex der Code ist.

### Theorie
Die Datenabhängigkeit ergibt sich aus den Lese- und Schreibmengen jeder Zuweisung. Hinzu kommen Steuerabhängigkeiten über if-, while-, for- und switch-Bedingungen. Die transitive Hülle liefert, von welchen Eingängen jeder Ausgang abhängt. Aufrufe lokaler Funktionen werden über deren eigene Ausgangsabhängigkeiten abgebildet.

Die zyklomatische Komplexität ist $M = 1 + \#\mathrm{if/elseif} + \#\mathrm{for/while} + \#\mathrm{case} + \#\{\&\&,\|\|\}$.

### Herleitung
$D(v)=\bigcup_{\text{Zuweisungen an }v}(\mathrm{Lese}(s)\cup \mathrm{Steuer}(s))$, $D^*(o)=$ transitive Hülle, Ausgangsabhängigkeit $=D^*(o)\cap\mathrm{Eingänge}$.

### Annahmen
Gleichungsnummern stehen in Kommentaren in der Form `(4.11)`, `(4.10a)` oder `(A.10)`.

### Randbedingungen
- Export als JSON (`to_json`).
- Export als Graphviz-DOT (`to_dot("dataflow"|"calls")`).
- LaTeX im matplotlib-mathtext-Umfang.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $D(v)$ | direkte Abhängigkeiten | – | `FunctionAnalysis.dependencies` |
| $M$ | zyklomatische Komplexität | – | `complexity["cyclomatic"]` |

### Anwendungsgrenzen
Die Analyse ist flussunabhängig (keine Pfadsensitivität). Die Datenflüsse in verschachtelte Funktionen werden nicht verfolgt.

### Vor- und Nachteile
Schnell und erklärbar. Die Abhängigkeiten sind konservativ, also eher zu viele als zu wenige.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Für A.5 zeigt die Analyse zum Beispiel: $\dot\delta$ hängt nicht von $k_3$, $m$, $J$, $\gamma$ und $\dot v_d$ ab, nur $F_l$.

### In einfachen Worten
Es entsteht eine Landkarte des Programms: welche Größe aus welcher berechnet wird und wo welche Formel aus dem Buch steht.

### Quellen
[@aho2006, Kap. 9]

## Erkennung der Regelungsstruktur {#matlab_control_structure}

### Ziel und Zweck
Rückführungs- und Vorsteueranteile werden automatisch ausgewiesen, z. B. für Reviews und Dokumentation.

### Theorie
Die Signale werden heuristisch klassifiziert:
- Verstärkungen: Eingänge wie `k1…kn`, `Kp`, `kd`, `gain*`
- Sollgrößen: Namen mit `_d`, `_ref`, `_des`, `_soll` bzw. `r`, `w`
- Regelfehler: Variablen `e_*`, `err*` sowie Differenzen aus Soll- und Messgröße
- Messgrößen: Eingänge in solchen Differenzen

Jede Zuweisung wird in additive Terme zerlegt:
- Ein Term mit Verstärkung × fehlerabhängigem oder gemessenem Signal ist eine **Rückführung**.
- Ein Term mit Sollgröße ohne Verstärkung und ohne Fehler ist eine **Vorsteuerung**.

Ein persistenter Zustand mit `x = x + …` (fehlerabhängig) gilt als Integrator, eine Differenz aus Fehler und gespeichertem Fehler als Differenzierer. Daraus folgt die P/I/D-Klassifikation.

### Herleitung
Für A.5 ergeben sich:
- Vorsteuerung: $\kappa_d$ (4.11), $\dot v_d$ (4.12), $\dot\kappa_d$ (4.18)
- Rückführung: die Terme mit $k_1\ldots k_4$, darunter $-k_4 e_\delta$ (4.17)

### Annahmen
Die Namenskonventionen der Regelungstechnik werden eingehalten.

### Randbedingungen
Das Ergebnis steht in `FunctionAnalysis.control`.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $k_i$ | Verstärkungen | – | `control["gains"]` |
| $e$ | Regelfehler | – | `control["errors"]` |

### Anwendungsgrenzen
Die Erkennung ist heuristisch und kann bei abweichender Namensgebung Terme falsch zuordnen.

### Vor- und Nachteile
Sie liefert ohne Modellwissen einen guten Überblick, ersetzt aber keine regelungstechnische Analyse.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Reine Rückführungsregler werden als solche ausgewiesen (Fixture `pure_feedback.m`), PID-Regler mit persistenten Zuständen ebenso (`pid_controller.m`).

### In einfachen Worten
Das Programm erkennt, welcher Teil des Reglers auf Abweichungen reagiert und welcher Teil vorausschauend den Sollwert direkt einspeist.

### Quellen
[@werling2011, Abschn. 4.2, Anh. A.5]

## Code-Generierung und Verifikation {#matlab_codegen}

### Ziel und Zweck
Die Regellogik wird nach Python (numpy), C++17 und Rust übersetzt, wobei Kommentare, Gleichungsreferenzen und Namen erhalten bleiben.

### Theorie
Die Übersetzung ist syntaxgesteuert und erfolgt über den typisierten AST:
- **Python:** `math` für Skalare, numpy für Arrays, Hilfsfunktionen aus `pyruntime` werden mitkopiert.
- **C++:** `double`, `mlab::Mat` in `matlab_runtime.hpp`, Struct für mehrere Ausgaben, State-Struct mit `std::optional` für persistente Variablen.
- **Rust:** `f64`, eingebettetes Modul `mlab`, Tupel für mehrere Ausgaben, State-Struct mit `Option<f64>`.

Variablen, deren erste Verwendung eine unbedingte Zuweisung auf oberster Ebene ist, werden dort deklariert. Alle übrigen werden am Funktionsanfang deklariert.

### Herleitung
Die Verifikation ist ein Back-to-Back-Test. Für $N$ Zufallseingaben wird $\max_i |y_i^{\mathrm{Ziel}}-y_i^{\mathrm{Interpreter}}|$ bestimmt (`vdsim.matlab.verify`). Ein generiertes `main` liest die Eingaben aus einer Datei und gibt die Ausgaben mit voller Genauigkeit aus: `%.17g` in C++, `{:e}` in Rust.

### Annahmen
Die Ziel-Compiler kontrahieren keine FMA: `/fp:precise` bzw. `-ffp-contract=off`, Rust kontrahiert nie.

### Randbedingungen
Nicht übersetzbare Konstrukte erzeugen eine Diagnose (Fehler mit Zeile und Spalte). `convert_file` schreibt dann nichts, außer mit `force=True`.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $y^{\mathrm{Ziel}}$ | Ausgaben des generierten Codes | – | `run_python`, `run_native` |

### Anwendungsgrenzen
Für C++ und Rust gilt:
- Unterstützt: Skalare, logische Skalare, reelle Matrizen mit skalaren Indizes, Schleifen über Bereiche und Zeilenvektoren, numerisches switch.
- Nicht unterstützt: Strings (außer Literalen in fprintf/disp/error), Zellen, Structs, globale Variablen, try/catch, verschachtelte Funktionen, Bereichs- und logische Indizierung, Wachsen von Arrays, Matrixdivision und Matrixpotenz.

Python kann zusätzlich Strings, Structs (SimpleNamespace), eindimensionale Zellen (Listen), Wachsen und allgemeine Indizierung.

### Vor- und Nachteile
- Vorteile: lesbarer Code ohne Abhängigkeiten.
- Nachteil: Die Matrixklasse ist nicht auf Geschwindigkeit optimiert.

### Numerische Aspekte
Python ist bitgleich zum Interpreter, da beide dieselben Funktionsaufrufe nutzen. C++ und Rust nutzen dieselbe CRT-Mathematik (MSVC: `sin`, `pow`). Abweichungen entstehen nur durch abweichende Summationsreihenfolgen bei Matrizen und liegen im Bereich $10^{-15}$ relativ.

### Praktische Auswirkungen
Der A.5-Regler lässt sich direkt als C++- oder Rust-Node (`cpp:`, `rust:`) einbinden.

### In einfachen Worten
Das MATLAB-Programm wird automatisch in andere Programmiersprachen übersetzt. Ein Test prüft, dass überall dieselben Zahlen herauskommen.

### Quellen
[@aho2006, Kap. 5, 8], [@iso_cpp17], [@rust_reference], [@ieee754_2019]
