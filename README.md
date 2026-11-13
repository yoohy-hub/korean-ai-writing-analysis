# Korean AI collaborative writing analysis

[한국어 안내](README.ko.md) · [Data dictionary](DATA_DICTIONARY.ko.md) · [Data availability](DATA_AVAILABILITY.md)

**Huan-Yi Liu** · Institute of Humanities, Sungkyunkwan University · [ORCID 0009-0000-9116-9810](https://orcid.org/0009-0000-9116-9810)

This package contains the Python code and pseudonymized numerical and categorical data that fall within the analytical scope of the manuscript. Learner texts, direct identifiers, original identifiers, identity keys and the original Excel/JSONL files are not distributed. Date of publication-scope review: **2026-11-14**.

## Study design and measures

Twenty-eight intermediate learners of Korean completed three writing tasks (self-introduction, secondhand sale and social networking service [SNS]) in the first semester of the 2026 academic year. Each task yielded a learner draft (A), an AI-generated version (B) and a collaboratively revised final version (C), giving 84 tasks and 252 texts in total. Draft A was produced before Version B. The AI tools, the prompts and whether A was provided to the AI were not controlled separately; B is therefore not assumed to be independent of A.

The paper reports six automated measures across F1–F3:

| Category | Measures | Count |
| --- | --- | ---: |
| F1 Output fluency | Character, eojeol and sentence counts | 3 |
| F2 Lexical diversity | MATTR20 | 1 |
| F3 Syntactic complexity | Mean sentence length and predicates per sentence | 2 |
| Total | | 6 |

F4 is the number of manually coded grammatical errors per 100 eojeol. F5–F8 measure form–source correspondence. F9 assigns a single representative information-adjustment code to each meaning unit, whereas F10 permits multiple expression-adjustment codes. A proposition in C is classified as A/B-common when it occurs in both A and B. Integration refers to the combination of content elements from both versions, including propositions and the relations between them; it is not limited to information unique to either version. All coding values are retained as originally assigned.

## Repository contents and usage

| Path | Contents |
| --- | --- |
| `data/text_metrics.csv` | 252 rows: pseudonymous keys, the six measures reported in the paper, previously coded F4 error rates and counts, and the short-text flag |
| `data/source_metrics.csv` | 84 rows of F5–F8 form–source measures and counts |
| `data/meaning_codes.csv` | 802 coded units with pseudonymous keys and F9/F10 labels (no text or free-text notes) |
| `paper_metrics.py`, `reproduce.py` | Preprocessing within the paper's scope and measurement of separately authorized external texts |
| `rq1_reproduce.py`, `rq2_reproduce.py`, `public_statistics.py` | Reproduction of the statistical analyses from the distributed numerical and categorical data |
| `reference/aggregates/` | Reference results within the paper's scope; previously reported adjusted omnibus p-values are provided for reference only |
| `reference/public_replay/` | Separate BCa benchmark based on the public participant ordering |
| `tests/`, `validation/` | Validation checks and reports for the current release scope |
| `SHA256SUMS.json`, `파일검증.py` | Checksums for verifying the integrity of the distributed files |

Run the following commands with Python 3.12 from the package root directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -B 파일검증.py
python -B 검증실행.py --output new_run/synthetic-tests.json
python -B public_statistics.py --output new_run/statistics
```

In Windows PowerShell, activate the virtual environment with `.venv\Scripts\Activate.ps1`. Each output directory must not already exist. The statistical reproduction produces 13 tables and `validation_report.json`; it neither reruns the NLP pipeline nor reclassifies the manual coding.

To measure separately authorized original texts, supply a CSV file containing the pseudonymous `participant_id` and `task_id`, `genre`, `A_text`, `B_text` and `C_text` columns, with optional `A_manual_error_count`, `B_manual_error_count` and `C_manual_error_count` columns. This file is not included in the release.

```bash
python -B reproduce.py --input "/path/to/restricted-pseudonymized-texts.csv" --output new_run/measurement
```

The command outputs numerical summaries only and leaves the input file unchanged. Restricted texts must not be added to the public repository; the public package is not a corpus of learner texts. Any telephone number shown in a public example must use the placeholder `010-0000-0000`.

## Computational scope and limitations

Measures are first computed for each text. For each learner and version, the values from the three tasks are then averaged with equal weights, yielding repeated measures for the 28 learners. Texts are not concatenated for remeasurement. Error rates are averaged across texts rather than computed from pooled error counts and pooled eojeol totals. Task-level comparisons are based on each learner's change from A to C (C − A).

The reproduction scripts independently recompute the point estimates, the omnibus p-values before multiplicity adjustment (with the Greenhouse–Geisser correction where applicable) and the within-measure pairwise tests, including the Holm adjustment across the three pairwise comparisons for each measure. **The previously reported adjusted omnibus p-values are retained in the reference tables only. They are not recalculated by the public code and are excluded from any claim of independent computational agreement.** These reference values should not be interpreted as newly estimated adjusted results.

F1–F3 are analyzed with repeated-measures ANOVA, following the documented decision rule based on Mauchly's test and the Greenhouse–Geisser correction. F4 is analyzed with the Friedman test and pairwise Wilcoxon tests. MATTR20 is computed with a moving window of 20 morphemes. For texts with 1–19 retained morphemes, the whole-text type–token ratio (TTR) is used instead, and texts with no retained morphemes are coded as missing. This short-text rule applies to one text. Manual grammatical-error labels are not assigned by the Kiwi morphological analyzer.

F5, F6 and F7 use different denominators (A-exclusive types, B-exclusive types and all C types, respectively); they are therefore not proportions that sum to 100%. F8 is defined as (RB − RA)/(RB + RA), following the documented conventions for zero and missing values. Morphological bigrams are sets of unique surface-form/POS types extracted after punctuation removal and may span sentence boundaries.

The RQ2 BCa intervals are based on 20,000 bootstrap resamples with seed 20260820. Because the participant order was randomized for public release, the finite Monte Carlo resampling differs from that of the original analysis. Consequently, eight interval endpoints differ from the original reference values, with a maximum absolute difference of 0.0031929721. The original reference limits are retained, and a separate benchmark based on the public ordering is validated. Computational agreement does not establish the validity of the manual coding, intercoder reliability or a causal educational effect.

## License and citation

The executable code is released under the [MIT License](LICENSE). The pseudonymized analytical data, tables, validation records and documentation are released under [CC BY 4.0](LICENSE-DATA.md). Original learner materials that are not distributed are not covered by this release. For citation information, see [CITATION.cff](CITATION.cff).

> Liu, H.-Y. (2026). *Korean AI collaborative writing analysis: Code and pseudonymized analytical data* (Version 1.0.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.24191921

In-text citation: **Liu (2026)** or **(Liu, 2026)**. When referring to the study's findings, cite the related journal article separately.
