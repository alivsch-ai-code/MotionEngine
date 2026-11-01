# Theorie: Kern

## Koordinatensysteme, Vorzeichen und Schlupfdefinition {#iso8855_conventions}

### Ziel und Zweck
Alle Modelle, Regler und Auswertungen verwenden dieselben Achsen, Vorzeichen und Größendefinitionen. Nur so ergeben z. B. ein Reifenmodell und ein Fahrzeugmodell zusammen die richtige Kraftrichtung.

### Theorie
Fahrzeugfestes System nach ISO 8855: $x$ nach vorn, $y$ nach links, $z$ nach oben. Der Gierwinkel $\psi$ ist gegen den Uhrzeigersinn positiv. Ein positiver Lenkwinkel $\delta$ lenkt nach links. Der Schräglaufwinkel ist so definiert, dass ein positiver Winkel eine positive (nach links wirkende) Seitenkraft erzeugt. Der Längsschlupf ist

$$\kappa = \frac{\omega R - v_{x,w}}{\vert v_{x,w} \vert}$$

und beim Antreiben positiv, beim Bremsen negativ. Statische Achslasten folgen aus dem Momentengleichgewicht um die Achsen:

$$F_{z,v} = m g \frac{l_h}{l}, \qquad F_{z,h} = m g \frac{l_v}{l}$$

### Herleitung
Die Achslasten ergeben sich aus $\sum M = 0$ um die Hinterachse: $F_{z,v}\, l - m g\, l_h = 0$. Die Schlupfdefinition bezieht die Differenz aus Umfangsgeschwindigkeit $\omega R$ und Längsgeschwindigkeit des Radmittelpunkts auf den Betrag der Längsgeschwindigkeit. So bleibt das Vorzeichen beim Rückwärtsrollen konsistent.

### Annahmen
- Starres, ebenes Fahrbahnkoordinatensystem.
- Radreihenfolge in allen Arrays: FL, FR, RL, RR.
- Wankwinkel $> 0$ hebt die linke Seite, Nickwinkel $> 0$ bedeutet Bug nach unten.

### Randbedingungen
Die Fahrzeugmodelle begrenzen den Nenner der Schlupfdefinition nach unten (`slip_speed_floor` = 3 m/s), weil $\kappa$ für $v \to 0$ singulär wird.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\psi$ | Gierwinkel | rad | `psi` |
| $\delta$ | Radlenkwinkel | rad | `steer_front`, `delta_f` |
| $\kappa$ | Längsschlupf | – | `kappa`, `slip_ratio` |
| $\omega$ | Raddrehzahl | rad/s | `omega`, `wheel_speed` |
| $R$ | dynamischer Radhalbmesser | m | `wheel_radius` |
| $l, l_v, l_h$ | Radstand, Schwerpunktabstände | m | `wheelbase`, `cg_to_front`, `cg_to_rear` |
| $g$ | Erdbeschleunigung | m/s² | `G` |

### Anwendungsgrenzen
Gilt für den klassischen Simulator. Die AD-Plattform (`vdsim.framework.types`) nutzt erdfest x Osten, y Norden; beide Systeme sind mathematisch positiv und damit verträglich.

### Vor- und Nachteile
- Vorteil: genormt, deckt sich mit Fachliteratur und Messtechnik.
- Nachteil: SAE J670 verwendet teils andere Vorzeichen (z nach unten); importierte Daten müssen umgerechnet werden.

### Numerische Aspekte
Die Schlupfsingularität bei Stillstand wird durch eine Mindestgeschwindigkeit im Nenner entschärft. Sie verändert den Schlupf unterhalb dieser Geschwindigkeit und begrenzt die Steifigkeit der Raddrehdynamik (siehe [Teilschritte](#stable_substeps)).

### Praktische Auswirkungen
Wer ein neues Modell oder einen Regler schreibt, muss nur diese eine Konvention kennen. Plots, Bericht und KPIs zeigen dieselben Vorzeichen.

### In einfachen Worten
Alle Programmteile sprechen dieselbe Sprache: vorne ist x, links ist y, Lenken nach links ist positiv. Schlupf sagt, wie viel schneller oder langsamer sich das Rad dreht, als das Auto fährt.

### Quellen
[@iso8855], [@mitschke2014]

## Parameterschema und klassische Registry {#parameter_schema}

### Ziel und Zweck
Parameter und Plugins sollen sich selbst beschreiben, damit GUI-Masken, JSON-Dateien, Berichte und diese Dokumentation automatisch entstehen.

### Theorie
Jedes Feld einer Parameter-Datenklasse wird mit `param(default, unit, label, min=, max=)` angelegt. Die Metadaten liegen in `dataclasses.Field.metadata`. Die Registry ist eine Abbildung $(\mathrm{kind}, \mathrm{name}) \mapsto \mathrm{Klasse}$, die durch Dekoratoren beim Import gefüllt wird.

### Herleitung
Entwurfsmuster „Registry“ plus „Selbstbeschreibung durch Metadaten“: Statt eines separaten Schemas wird die Beschreibung direkt am Feld gespeichert. Damit ist die Beschreibung immer synchron mit dem Code.

### Annahmen
Plugins werden beim Import registriert; die eingebauten Module werden beim ersten `get()` importiert.

### Randbedingungen
Erlaubte Arten (`KINDS`): vehicle_model, tire_model, lateral_controller, longitudinal_controller, chassis_system, maneuver, trajectory_loader.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| kind | Plugin-Art | – | `kind` |
| name | Plugin-Name | – | `name`, `registry_name` |
| unit, label | Einheit, Bezeichnung | – | `metadata["unit"]`, `metadata["label"]` |

### Anwendungsgrenzen
Keine Versionierung, keine Typprüfung der Konstruktorargumente.

### Vor- und Nachteile
- Vorteil: minimaler Aufwand für neue Komponenten.
- Nachteil: Namenskollisionen werden nicht gemeldet; die versionierte Registry in `vdsim.framework.plugins` löst das.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Ein neues Reifenmodell ist nach `@register("tire_model", "x")` sofort in Szenarien, GUI und Doku verfügbar.

### In einfachen Worten
Jeder Parameter trägt ein Namensschild mit Einheit und erlaubtem Bereich. Jedes Modell meldet sich unter einem Namen an, damit man es im Szenario einfach auswählen kann.

### Quellen
[@martin2017]
