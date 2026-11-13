# Data and code availability

The public release is limited to the manuscript's analytical scope: six F1–F3 automated measures, the F4 grammatical-error measure, F5–F8 form-source measures, and existing F9/F10 coding labels. Measurements and manual coding cells retained in the package are copied unchanged from the existing analytical input. Release-scope review: 2026-11-14.

The package contains 252 text-measurement rows, 84 task-level source-measurement rows and 802 semantic-unit coding rows. Participant, task and unit IDs are independently randomized pseudonyms. Identity keys, original identifiers, departments, original text/alignment passages, free-text notes and original Excel/JSONL files are excluded. No learner-text corpus is distributed. Public telephone examples use 010-0000-0000.

The scripts replay paper-scope raw statistics and within-measure pairwise tests. Previously reported omnibus adjusted p-values remain in reference files only; they are not independently recalculated by the public code. This limitation is stated explicitly in the README and validation report.

NLP remeasurement requires separately authorized private text. `reproduce.py` accepts a pseudonymized external CSV and exports only the numerical measurements used in the paper. The input text is not bundled and is not modified. Existing error and meaning labels are not reclassified.

Code is MIT licensed; pseudonymized data, tables, validation records and documentation are CC BY 4.0. Undistributed original material is not covered by these licenses. Use the version DOI in CITATION.cff and cite the related journal article separately where relevant.
