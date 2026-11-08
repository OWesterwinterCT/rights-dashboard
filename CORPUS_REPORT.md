# English corpus audit

Snapshot: 7 November 2026. Every one of the 599 folder files was retrieved and assessed.

| Decision | Files |
|---|---:|
| Unique English texts included | 388 |
| Non-English files excluded | 208 |
| Duplicate English copies excluded | 3 |
| Unresolved or unreadable files | 0 |

The English corpus covers 103 filename-based geographic labels, including shared and regional scopes. Two bilingual English/Portuguese frameworks (Mozambique 2022–2026 and Cabo Verde 2023–2027) are included, with retrieval restricted to confidently English passages. Counts describe this audited snapshot; automated language detection and OCR are not substitutes for a line-by-line document review.

## Uniqueness and country associations

Three copies were removed from the search index: one manually reviewed Cambodia duplicate with corrupted font extraction, and two exact normalized-text duplicates (Belize 2017–2021 and Serbia and Montenegro 2005–2009 copies). Their original catalogue records and country associations remain available. A shared framework is indexed once; its passages must not automatically be treated as country-specific evidence for every associated label.

Both Pacific 2018–2022 versions remain because their annex content differs. Distinct periods and nonidentical editions are retained. Therefore, unique search documents are not necessarily unique policy frameworks.

## Recovery and quality

Text extraction was repaired where needed using the original PDFs. Palestine 2023–2025 was recovered with OCR of embedded page images. Namibia 2025–2029 and Georgia 2026–2030 required OCR after correcting microscopic PDF page scaling. Other fragmented texts were re-extracted with Poppler. The original Drive files were not modified. No external replacement documents were substituted.

Image-only or font-corrupted non-English files were reviewed using recovered page images/OCR where necessary. All automated and manual decisions are in `data/corpus_audit.csv`; manual reasons and duplicate links are also in `data/language_overrides.json`. The extraction method is recorded for each file.

OCR and PDF extraction can distort tables, symbols, columns and word order. Passage citations refer to extracted text, not verified page numbers. Consult original source links for definitive wording and layout.

## Geography and dates

The full catalogue has 135 country/economy labels, two regional labels, and one historical entity. Names come from filenames and have been normalized; they are not verified mappings of every country discussed inside a document. Filename period parsing leaves four files flagged for review: malformed dates or a single year rather than an interval.

The score CSV is byte-identical to the supplied attachment. Its cleaning, year alignment and prior imputations are inherited. Score provenance is not inferred from overlapping framework dates.
