# MATLAB-Integration (Import, Interpreter, Analyse, Konvertierung) – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`_Analyzer._control`](../../../vdsim/matlab/analysis.py#L466) | Abschn. 4.2 | [Matlab control structure](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_matlab_analysis.py](../../../tests/matlab/test_matlab_analysis.py) | Code (@trace) |
| [`analyze`](../../../vdsim/matlab/analysis.py#L582) | Abschn. 9.2 | [Matlab analysis](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Aho et al. (2006)](../references.md#aho2006) | [test_matlab_analysis.py](../../../tests/matlab/test_matlab_analysis.py) | Code (@trace) |
| [`generate`](../../../vdsim/matlab/codegen/__init__.py#L18) | Abschn. 8 | [Matlab codegen](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Aho et al. (2006)](../references.md#aho2006) | [test_matlab_codegen.py](../../../tests/matlab/test_matlab_codegen.py) | Code (@trace) |
| [`Interpreter.call`](../../../vdsim/matlab/interpreter.py#L237) | Abschn. Language Fundamentals | [Matlab interpreter](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [MathWorks und Inc. (2024)](../references.md#mathworks_matlab) | [test_matlab_component.py](../../../tests/matlab/test_matlab_component.py), [test_matlab_interpreter.py](../../../tests/matlab/test_matlab_interpreter.py) | Code (@trace) |
| [`parse`](../../../vdsim/matlab/parser.py#L607) | Abschn. 4.4 | [Matlab parser](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Aho et al. (2006)](../references.md#aho2006) | [test_matlab_codegen.py](../../../tests/matlab/test_matlab_codegen.py), [test_matlab_parser.py](../../../tests/matlab/test_matlab_parser.py) | Code (@trace) |
| [`infer_types`](../../../vdsim/matlab/typeinfer.py#L521) | Abschn. 6.5 | [Matlab type inference](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Aho et al. (2006)](../references.md#aho2006) | – | Code (@trace) |
| [`verify_file`](../../../vdsim/matlab/verify.py#L194) | – | [Matlab codegen verification](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [MathWorks und Inc. (2024)](../references.md#mathworks_matlab) | [test_matlab_codegen.py](../../../tests/matlab/test_matlab_codegen.py) | Code (@trace) |
