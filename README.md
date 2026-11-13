# Korean AI collaborative writing analysis

[한국어 안내](README.ko.md) · [Data dictionary](DATA_DICTIONARY.ko.md) · [Data availability](DATA_AVAILABILITY.md)

**Huan-Yi Liu** · Institute of Humanities, Sungkyunkwan University · [ORCID 0009-0000-9116-9810](https://orcid.org/0009-0000-9116-9810)

This package provides Python code and pseudonymized numerical/categorical data within the manuscript's analytical scope. Learner texts, direct identifiers, original identifiers, identity keys and original Excel/JSONL files are not distributed. Publication-scope review date: **2026-11-14**.

## Study and paper measures

Twenty-eight intermediate Korean learners completed self-introduction, secondhand-sale and SNS tasks in the first semester of the 2026 academic year. Each task has a learner draft (A), an AI-written version (B) and a collaboratively revised final version (C): 84 tasks and 252 texts. A preceded B. AI tools, prompts and whether A was supplied to the AI were not separately controlled; B is not assumed to have been generated independently of A.

The paper reports exactly six automated F1–F3 measures:

| Category | Measures | Count |
| --- | --- | ---: |
| F1 Output fluency | Character, eojeol and sentence counts | 3 |
| F2 Lexical diversity | MATTR20 | 1 |
| F3 Syntactic complexity | Mean sentence length and predicates per sentence | 2 |
| Total | | 6 |

F4 uses manually coded grammatical errors per 100 eojeol. F5–F8 measure form-source correspondence. F9 assigns one representative information-adjustment code per meaning unit; F10 allows multiple expression-adjustment codes. A/B-common means that a proposition in C occurs in both A and B. Integration combines content elements from both versions, including propositions and relations between propositions; it is not restricted to information unique to each version. Existing coding values are preserved.

## Files and execution

| Path | Contents |
| --- | --- |
| `data/text_metrics.csv` | 252 rows; pseudonymous keys, the six paper measurements, existing F4 error measurements/counts and the short-text flag |
| `data/source_metrics.csv` | 84 rows of F5–F8 form-source measurements/counts |
| `data/meaning_codes.csv` | 802 coded units, with pseudonymous keys and F9/F10 labels; no text or free-form notes |
| `paper_metrics.py`, `reproduce.py` | Paper-scope preprocessing and authorized external-text measurement |
| `rq1_reproduce.py`, `rq2_reproduce.py`, `public_statistics.py` | Statistical replay from the distributed numerical/categorical data |
| `reference/aggregates/` | Paper-scope reference results; previously reported omnibus adjusted p-values are reference-only |
| `reference/public_replay/` | Separate public-order BCa benchmark |
| `tests/`, `validation/` | Current scoped checks and reports |
| `SHA256SUMS.json`, `파일검증.py` | Distribution integrity |

Use Python 3.12 from the package root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -B 파일검증.py
python -B 검증실행.py --output new_run/synthetic-tests.json
python -B public_statistics.py --output new_run/statistics
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. Output directories must be new. Statistical replay generates 13 tables and `validation_report.json`. It does not rerun NLP or reclassify manual coding.

For separately authorized original text, the measurement input is a CSV with pseudonymous `participant_id`/`task_id`, `genre`, `A_text`, `B_text`, `C_text`, and optional `A_manual_error_count`/`B_manual_error_count`/`C_manual_error_count` columns. It is not included in this release.

```bash
python -B reproduce.py --input "/path/to/restricted-pseudonymized-texts.csv" --output new_run/measurement
```

This command exports numerical summaries only and does not modify its input. Do not add restricted text to the public repository. The public package is not a learner-text corpus. Any public telephone example must be `010-0000-0000`.

## Computational scope and limits

Each text is measured first. The three task measurements are averaged with equal weight within each learner and version, producing 28 learners' repeated measures. Texts are not concatenated and remeasured. Error rates are averaged across texts, rather than calculated from pooled errors and pooled eojeol totals. Task comparisons use each learner's C-minus-A changes.

The replay independently recomputes point estimates, omnibus p-values before multiplicity adjustment (with Greenhouse–Geisser correction where applicable) and within-measure pairwise tests, including Holm adjustment within each measure's three pairs. **Previously reported omnibus adjusted p-values are retained in the reference tables only. They are not recalculated by the public code and are excluded from independent-agreement claims.** These references must not be interpreted as freshly estimated adjusted results.

F1–F3 use repeated-measures ANOVA with the documented Mauchly/Greenhouse–Geisser rule. F4 uses Friedman and pairwise Wilcoxon tests. MATTR20 uses a 20-morpheme window; 1–19 retained morphemes use whole-text TTR, and zero morphemes give a missing value. One text uses the short-text rule. Kiwi does not determine the manual grammatical-error labels.

F5, F6 and F7 have different denominators (A-exclusive types, B-exclusive types and all C types); they are not percentages that sum to 100%. F8 is `(RB-RA)/(RB+RA)`, with the documented zero/missing conventions. Morphological bigrams are unique surface-form/POS type sets after punctuation removal and may cross sentence boundaries.

RQ2 BCa intervals use 20,000 resamples and seed 20260820. Randomized public participant ordering changes finite Monte Carlo resampling. Eight interval endpoints differ from original references, with maximum absolute difference 0.0031929721. Original reference limits are retained, and a separate public-order benchmark is checked. Computational agreement does not establish manual coding validity, intercoder reliability or a causal educational effect.

## License and citation

Executable code: [MIT](LICENSE). Pseudonymized analytical data, tables, validation records and documentation: [CC BY 4.0](LICENSE-DATA.md). Undistributed original learner material is not licensed by this release. See [CITATION.cff](CITATION.cff).

> Liu, H.-Y. (2026). *Korean AI collaborative writing analysis: Code and pseudonymized analytical data* (Version 1.0.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.24191921

In text: **Liu (2026)** or **(Liu, 2026)**. Cite the related journal article separately when referring to its findings.
