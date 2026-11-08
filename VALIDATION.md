# Validation

Validated 7 November 2026, Python 3.12. Runtime package versions are listed in `requirements-tested.txt`. Python 3.12 is also specified for deployment.

- Ten automated tests passed: data uniqueness/numeric validation, equal-country and fixed-cohort means, exclusion of regional entities, rejection of duplicate inputs, search filters and caps, malformed filename dates, all six Streamlit pages, full corpus audit and uniqueness, exact source-CSV hash, persisted index round-trip, and duplicate country associations (some tests cover multiple checks).
- All 599 catalogue records were audited. Final decisions: 388 unique English documents, 208 non-English files, 3 duplicate copies, zero unresolved files.
- 56,682 extracted-text passages indexed. Corpus index rebuild and reload succeeded in 34 seconds in this environment; build peak process memory was approximately 1 GB. This is a measurement, not a performance guarantee.
- Semantic queries for freedom of expression, disability inclusion, climate resilience and access to justice returned source-linked passages. Similarity rankings remain exploratory and require human relevance review.
- The actual Streamlit semantic-search form was submitted successfully against the full bundled corpus, displaying source expanders and evidence tables without an application exception.
- A fresh app-only semantic-search check used approximately 638 MiB peak process memory in this environment. Multi-user and hosted performance were not load-tested.
- Search is entirely local. No AI API key, pretrained model download, or paid model call is required.
- No GitHub repository, external deployment or hosted app was created.

An unrelated pytest plugin emitted a deprecation warning; tests passed. Browser pixel-level rendering and deployment in Streamlit Community Cloud were not independently tested. OCR text was sampled for readability rather than checked word by word. The first version provides extractive evidence overviews, not LLM-generated narrative summaries.
