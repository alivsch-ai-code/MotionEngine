# MATLAB-Integration (Import, Interpreter, Analyse, Konvertierung) – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


**Noch nicht dokumentiert.** Es gibt keine handgeschriebene `theory.md` (`vdsim/matlab/docs/theory.md`).

## Konzepte ohne Theorieabschnitt {#konzepte-ohne-theorie}

Folgende Konzepte werden im Code oder in der Paketdoku genannt, haben aber noch keinen Abschnitt `## … {#concept-id}`:

- `matlab_analysis`
- `matlab_codegen`
- `matlab_codegen_verification`
- `matlab_control_structure`
- `matlab_import`
- `matlab_interpreter`
- `matlab_parser`
- `matlab_type_inference`

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Matlab analysis](../README.md#konzepte-ohne-dokumentation) | [`analysis.analyze`](../../../vdsim/matlab/analysis.py#L582) | – | [Aho et al. (2006)](../references.md#aho2006) |
| [Matlab codegen](../README.md#konzepte-ohne-dokumentation) | [`codegen.generate`](../../../vdsim/matlab/codegen/__init__.py#L18) | – | [Aho et al. (2006)](../references.md#aho2006) |
| [Matlab codegen verification](../README.md#konzepte-ohne-dokumentation) | [`verify.verify_file`](../../../vdsim/matlab/verify.py#L194) | – | [MathWorks und Inc. (2024)](../references.md#mathworks_matlab) |
| [Matlab control structure](../README.md#konzepte-ohne-dokumentation) | [`analysis._Analyzer._control`](../../../vdsim/matlab/analysis.py#L466) | – | [Werling (2011)](../references.md#werling2011) |
| [Matlab import](../README.md#konzepte-ohne-dokumentation) | – | – | – |
| [Matlab interpreter](../README.md#konzepte-ohne-dokumentation) | [`interpreter.Interpreter.call`](../../../vdsim/matlab/interpreter.py#L237) | – | [MathWorks und Inc. (2024)](../references.md#mathworks_matlab) |
| [Matlab parser](../README.md#konzepte-ohne-dokumentation) | [`parser.parse`](../../../vdsim/matlab/parser.py#L607) | – | [Aho et al. (2006)](../references.md#aho2006) |
| [Matlab type inference](../README.md#konzepte-ohne-dokumentation) | [`typeinfer.infer_types`](../../../vdsim/matlab/typeinfer.py#L521) | – | [Aho et al. (2006)](../references.md#aho2006) |
