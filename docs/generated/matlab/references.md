# MATLAB-Integration (Import, Interpreter, Analyse, Konvertierung) – Quellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · **Quellen** · [Rückverfolgbarkeit](traceability.md)


| Zitat | Quelle | Typ | Verwendet in |
|---|---|---|---|
| [Aho et al. (2006)](../references.md#aho2006) | Aho, A. V.; Lam, M. S.; Sethi, R.; Ullman, J. D. (2006): Compilers: Principles, Techniques, and Tools. 2. Addison-Wesley. ISBN 978-0-321-48681-3. | Fachbuch | analyze (@trace), generate (@trace), infer_types (@trace), module.yaml, parse (@trace) |
| [IEEE (2019)](../references.md#ieee754_2019) | IEEE (2019): IEEE Standard for Floating-Point Arithmetic (IEEE 754-2019). DOI 10.1109/IEEESTD.2019.8766229. | Industriestandard | module.yaml |
| [JTC1/SC22/WG21 (2017)](../references.md#iso_cpp17) | JTC1/SC22/WG21, I. (2017): ISO/IEC 14882:2017 Programming languages — C++. | Industriestandard | module.yaml |
| [MathWorks und Inc. (2024)](../references.md#mathworks_matlab) | MathWorks, T.; Inc. (2024): MATLAB Language Fundamentals (Operators and Elementary Operations, Operator Precedence, Matrix Indexing, Functions). The MathWorks, Inc.. https://www.mathworks.com/help/matlab/language-fundamentals.html. | Offizielle Dokumentation | Interpreter.call (@trace), module.yaml, verify_file (@trace) |
| [MathWorks und Inc. (2024)](../references.md#mathworks_precedence) | MathWorks, T.; Inc. (2024): Operator Precedence. https://www.mathworks.com/help/matlab/matlab_prog/operator-precedence.html. | Offizielle Dokumentation | module.yaml |
| [Developers (2024)](../references.md#rust_reference) | Developers, T. R. P. (2024): The Rust Reference. https://doc.rust-lang.org/reference/. | Offizielle Dokumentation | module.yaml |
| [Werling (2011)](../references.md#werling2011) | Werling, M. (2011): Ein neues Konzept für die Trajektoriengenerierung und -stabilisierung in zeitkritischen Verkehrsszenarien. Dissertation. KIT Scientific Publishing (Schriftenreihe des Instituts für Angewandte Informatik / Automatisierungstechnik, Band 34). ISBN 978-3-86644-631-1. https://publikationen.bibliothek.kit.edu/1000021738. | Dissertation / Abschlussarbeit | _Analyzer._control (@trace), module.yaml |
