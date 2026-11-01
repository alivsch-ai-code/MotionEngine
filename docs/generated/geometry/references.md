# Geometrie – Referenzkurven und Frenet-Koordinaten – Quellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · **Quellen** · [Rückverfolgbarkeit](traceability.md)


| Zitat | Quelle | Typ | Verwendet in |
|---|---|---|---|
| [de Boor (2001)](../references.md#deboor2001) | de Boor, C. (2001): A Practical Guide to Splines. revised edition. Springer (Applied Mathematical Sciences 27). | Fachbuch | ReferenceLine.evaluate (module.yaml), module.yaml, theory.md |
| [Werling et al. (2010)](../references.md#werling2010icra) | Werling, M.; Ziegler, J.; Kammel, S.; Thrun, S. (2010): Optimal Trajectory Generation for Dynamic Street Scenarios in a Frenét Frame. In: IEEE International Conference on Robotics and Automation (ICRA). DOI 10.1109/ROBOT.2010.5509799. | Fachartikel | module.yaml, theory.md |
| [Werling (2011)](../references.md#werling2011) | Werling, M. (2011): Ein neues Konzept für die Trajektoriengenerierung und -stabilisierung in zeitkritischen Verkehrsszenarien. Dissertation. KIT Scientific Publishing (Schriftenreihe des Instituts für Angewandte Informatik / Automatisierungstechnik, Band 34). ISBN 978-3-86644-631-1. https://publikationen.bibliothek.kit.edu/1000021738. | Dissertation / Abschlussarbeit | ReferenceLine.from_points (module.yaml), ReferenceLine.project (@trace), ReferenceLine.to_cartesian (@trace), ReferenceLine.to_frenet (@trace), curvature_profile (module.yaml), links.yaml → package:geometry, module.yaml, theory.md |
