# Rights & Development Observatory

A Streamlit research dashboard combining the supplied cleaned country-year data, a 599-file development-framework catalogue, and an English-document topic-search pilot. Nothing has been deployed.

## Run locally

Use Python 3.12 (tested). From this directory:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

There are no required secrets, API keys, live Drive connections, or paid services. Data and text are bundled. The first topic search loads and caches the bundled local search index; subsequent searches reuse it. If the corpus changes, the index is rebuilt locally. Exact-phrase search works without building the model.

## Deploy later

Push the contents of this directory to your GitHub repository using Git, including `data/` and `.streamlit/config.toml`. The bundled index contains large binary files, so a Git push is preferable to browser file upload. In Streamlit Community Cloud, select `app.py` as the entry point and Python 3.12. Install dependencies from `requirements.txt` automatically. Do not upload a virtual environment or credentials. This package does not create or change any GitHub repository or hosted app.

Bundled document text and score data will be accessible to users of a public app and readers of a public repository. Confirm redistribution permissions before making them public. Original Drive permissions do not protect bundled extracted text. The package contains extracted texts and source links, not original PDF/DOCX binaries.

## Pages

- **Overview:** catalogue counts, searchable English document count, rights coverage and regional coverage.
- **Country trends:** six rights, separate CL/PR chart, year filter (default through 2023), overlapping framework links, CSV export.
- **Regional comparison:** equal-country means, contributing-country counts, and fixed-cohort option. Includes country/economy records only.
- **Document library:** full catalogue with geographic filters, filename dates, extraction coverage and Drive links.
- **Topic search:** keyword, exact phrase or corpus-trained semantic retrieval; country and regional filters; grouped source passages and exportable evidence overview.
- **Data & methods:** corpus inclusion audit, methodological limitations and data download.

## Score data

`data/df_rights.csv` is the supplied cleaned dataset: 3,588 rows, 138 geographic labels, 2000–2025. No scores, ratings or missing values are changed. Country names are standardized at load time for display/linking. `resolved_code`, `region` and `scope` are derived fields; `wb_code` is preserved. Vietnam, Somalia and other legacy names are explicitly mapped where necessary.

The six right columns are listed in `core.RIGHTS`. CL/PR are separate 1–7 ratings with higher values meaning less freedom. Year alignment and prior imputation are inherited from the supplied CSV, not revalidated against the original spreadsheets. The file has no imputation flags; the app cannot distinguish observed from previously filled entries. Numeric scores should be interpreted according to the original codebook; the dashboard does not invent a substantive scale definition.

Replace `data/df_rights.csv` to update permanent scores, or use the sidebar CSV upload for a session-only replacement. Required fields: `year`, `country`, the six right columns and `CL Rating`, `PR Rating`. Capitalized `Year`/`Country` are accepted. `wb_code` and `Status` are optional. Duplicates, invalid years and non-numeric scores are rejected rather than silently averaged. No arbitrary input is executed.

## Regional aggregation

World Bank country-region classifications are frozen in `data/world_bank_countries.json` (retrieved 2026-11-07 from https://api.worldbank.org/v2/country?format=json&per_page=400). They are contemporary groupings, applied consistently across all years, not historical boundaries. Palestine follows World Bank's West Bank and Gaza code for exploratory grouping only; this does not resolve differences between underlying source geographies.

Available-country means ignore missing scores, weighting each country equally. Changing composition can affect trends. Fixed composition retains only countries with non-missing values for the selected measure in **every calendar year** of the selected interval. Each region has its own cohort. Regional frameworks and Serbia and Montenegro are excluded from national means. No population weights, interpolations or causal interpretations are applied.

## English topic-search corpus

The delivered corpus contains **388 unique English documents** across **103 filename-based geographic labels**. All 599 files were audited: 208 non-English files and three duplicate copies were excluded from indexing, with no unresolved files. See `data/corpus_audit.csv` and `CORPUS_REPORT.md` for decisions. The full folder is audited, rather than selecting only a few countries. Language is detected from five dispersed text windows with a fixed random seed. At least four windows must confidently identify English. Ambiguous/mixed-language and unreadable files are separately flagged. Exact normalized-text duplicates and manually reviewed duplicate copies retain one representative. Distinct planning periods and versions are retained unless their normalized full text is identical or a documented manual review establishes duplicate copies. This conservative definition of uniqueness avoids accidentally discarding substantively different editions. Identical texts filed under multiple countries are indexed once while retaining every filename-based country association for filters; a retrieved passage does not necessarily discuss each tagged country. The two Pacific 2018–2022 versions are retained because their annex content differs.

Language detection is automated and should be reviewed for ambiguous cases. File counts do not equal unique policy frameworks. Similar but nonidentical files may be revisions rather than independent frameworks. The audit retains all 599 source IDs, titles and decisions. Original source links can require Drive access.

Texts are split into overlapping passages of 200 whitespace-separated words with a 160-word step. Stable references such as `DOCID:P0012` identify extracted-text passages, **not verified PDF page numbers**. Text extraction may alter tables. Problematic English PDFs were re-extracted or OCR-processed where needed, including PDFs with microscopic page scaling. This is not a line-by-line transcription guarantee.

### Search methods

1. **Keyword:** TF–IDF term and bigram similarity, English stop words removed.
2. **Exact phrase:** case-insensitive literal substring occurrences, including stop words.
3. **Semantic:** latent semantic analysis (LSA), trained locally on the English corpus. Truncated SVD reduces TF–IDF to 96 latent dimensions; cosine similarity retrieves related passages based on word co-occurrence. This is model-based, but it is not a pretrained language model and is weaker at paraphrases and rare concepts. Use English queries.

A fitted index is bundled as JSON and NumPy/SciPy arrays (no pickle). The corpus fingerprint is checked before loading; if it differs, the index is rebuilt locally and cached. Region/country filters restrict retrieval, not model training. Scores are relative similarity, not probabilities. Queries outside the vocabulary return no matches. At most 20 passages, two per document, are displayed. Results are grouped by country or region with source links and CSV export. These capped counts must not be read as regional prevalence. Evidence text is shown verbatim; the pilot provides an **extractive evidence overview**, not an LLM-written synthesis.

A generative cross-country summary can be added later behind an explicitly configured model, citation validation and public-app usage limits. No text is sent to an AI provider in this version. Streamlit usage telemetry is disabled in the bundled configuration. A pretrained model was not included because its setup triggered an unrelated telemetry connection; this local LSA implementation requires no network calls at runtime.

## Update the corpus

To rebuild from a fresh extraction, prepare one JSON per Drive ID in a separate directory with fields `doc_id`, `title`, `url`, `text`, and optionally `error`. Keep the full source catalogue in `data/catalogue_raw.json`. Then:

```bash
python scripts/prepare_corpus.py /path/to/extracted_json
python scripts/build_index.py
```

Override entries have a source document ID as key and an object with `status` (`english`, `non_english`, `duplicate`, or `unreadable`) and a review `reason`. For a bilingual document, set `status` to `english` and `bilingual` to `true`; only confidently English passages enter retrieval.

Rebuilding the full corpus index used approximately 1 GB peak process memory in the validation environment. Rebuild locally before deploying if you change the corpus; the app normally loads the precomputed index.

The preparation script replaces `data/pilot_text/`, writes the inclusion audit and regenerates `data/catalogue.csv`. Restart Streamlit to clear cached data. The original folder retrieval needs an authenticated Drive client; no account token is bundled. Add OCR upstream for image-only PDFs. Manual language decisions can be recorded in `data/language_overrides.json` as described in the corpus report.

## Test

```bash
pip install -r requirements-dev.txt
pytest -q
python scripts/build_index.py
```

Tests cover score validation, equal-country and fixed-cohort aggregation, geographic exclusions, search filtering and per-document result caps, and every Streamlit page. See `VALIDATION.md` for the delivered run results.

## Files

`app.py` UI; `core.py` data and aggregation; `search.py` offline retrieval; `scripts/` rebuilding and benchmarking; `tests/` checks; `data/` CSV, metadata and extracted English texts; `.streamlit/config.toml` theme; requirements and this README.
