# JAC Class 12 Study Materials (2012–2026)

A curated collection of 59 theory / subjective previous years' question papers (PYQs) for Jharkhand Academic Council (JAC) Class 12 board examinations covering Physics, Chemistry, Mathematics (PCM), and English Core.

---

## Repository Structure

```
study_materials/
├── chemistry/       # 14 Theory Papers (2012–2020, 2022–2026)
├── english/         # 17 Theory Papers (2012–2020, 2023–2026)
├── mathematics/     # 13 Theory Papers (2012–2020, 2023–2026)
└── physics/         # 15 Theory Papers (2012–2020, 2022–2026)
```

---

## Catalog

### Chemistry (14 Papers)
- `2012_chemistry_paper.pdf`
- `2013_chemistry_paper.pdf`
- `2014_chemistry_paper.pdf`
- `2015_chemistry_paper.pdf`
- `2016_chemistry_paper.pdf`
- `2017_chemistry_paper.pdf`
- `2018_chemistry_paper.pdf`
- `2019_chemistry_paper.pdf`
- `2020_chemistry_paper.pdf`
- `2022_chemistry_30002.pdf`
- `2023_chemistry_14090.pdf`
- `2024_chemistry_55091.pdf`
- `2025_chemistry_10275.pdf`
- `2026_chemistry_2256.pdf`

### English Core (17 Papers)
- `2012_english_core.pdf`
- `2013_english_core.pdf`
- `2014_english_core.pdf`
- `2015_english_core.pdf`
- `2016_english_core.pdf`
- `2017_english_core.pdf`
- `2018_english_core.pdf`
- `2019_english_core.pdf`
- `2020_english_core.pdf`
- `2023_english_a-core-3037.pdf`
- `2024_english_a-core-43020.pdf`
- `2024_english_a-core-44037.pdf`
- `2025_english_9325.pdf`
- `2025_english_a-core-9120.pdf`
- `2025_english_a-core-9222.pdf`
- `2026_english_a-core-1101.pdf`
- `2026_english_a-core-1203.pdf`

### Mathematics (13 Papers)
- `2012_mathematics_paper.pdf`
- `2013_mathematics_paper.pdf`
- `2014_mathematics_paper.pdf`
- `2015_mathematics_paper.pdf`
- `2016_mathematics_paper.pdf`
- `2017_mathematics_paper.pdf`
- `2018_mathematics_paper.pdf`
- `2019_mathematics_paper.pdf`
- `2020_mathematics_paper.pdf`
- `2023_mathematics_12087.pdf`
- `2024_mathematics_53088.pdf`
- `2025_mathematics_9661.pdf`
- `2026_mathematics_1642.pdf`

### Physics (15 Papers)
- `2012_physics_paper.pdf`
- `2013_physics_paper.pdf`
- `2014_physics_paper.pdf`
- `2015_physics_paper.pdf`
- `2016_physics_paper.pdf`
- `2017_physics_paper.pdf`
- `2018_physics_paper.pdf`
- `2019_physics_paper.pdf`
- `2020_physics_paper.pdf`
- `2022_physics_30001.pdf`
- `2023_physics_8078.pdf`
- `2024_physics_49079.pdf`
- `2025_physics_9865.pdf`
- `2025_physics_jan-2025.pdf`
- `2026_physics_1846.pdf`

---

## Solved Question Bank (`data/` + `jac_pyqs.html`)

Every paper in the catalog has been transcribed, question by question, into
`data/<subject>/<key>.json`, with the printed options, the correct option and a
**written model answer** for each question (MCQ answers explain *why*).

- **56 papers · 2,187 questions**, covering Physics (530), Chemistry (510),
  Mathematics (506) and English Core (641).
- `manifest.json` lists all 59 PDFs with a per-paper status
  (`done`, `excluded-practical`, `excluded-elective`).
- `jac_pyqs.html` is the generated, fully offline single-file site: open it in any
  browser to browse by subject → chapter → paper, or to search.
- `qa_check.py` validates the JSON (structure, option counts, chapter labels,
  answer format, control characters); `python3 qa_check.py --all` checks every paper,
  `python3 qa_check.py --full jac_pyqs.html` checks the built site against `data/`.
- `build.py` regenerates `jac_pyqs.html` from `data/` and `template.html`.
- `_work/` holds the one-off generator script for each paper, so any paper can be
  corrected at source and rebuilt rather than hand-edited.
- `node tools/smoke.js` walks the built site headlessly in jsdom (needs
  `npm i jsdom`): every subject tab → every chapter → every marks / category /
  topic bucket (row counts are checked against the bucket badges) → a question of
  each type → option select, *Check Answer*, *View Solution*, star, Previous/Next,
  plus the Starred tab and *All Starred*. It also asserts that the bundled KaTeX
  really typesets the math and reports no `.katex-error`. A full run covers 61
  chapters, ~1,740 buckets and 61 questions in about 7 seconds.
