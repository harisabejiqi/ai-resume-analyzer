# AI Resume Analyzer

A web application that automatically evaluates and analyzes resumes (PDF/DOCX)
using NLP and AI techniques. Users upload a resume and, optionally, a job
description, and receive an overall score, extracted skills and entities,
missing-keyword analysis, semantic job-match scoring and concrete improvement
suggestions.

Developed as a BSc thesis project at UBT — *"Analysis, planning and development
of a web application for automated evaluation and analysis of career
documentation using artificial intelligence"*.

## How it works

```
resume file → parser → raw text → analyzer → structured entities
                                       ↓
job description → jd_parser → requirements → scorer → score + suggestions → JSON
                                       ↑
                     embeddings (SBERT) + calibration (Platt)
```

- **Parsing** — PyMuPDF (PDF) and python-docx (DOCX) text extraction.
- **Information extraction** — contact details, skills, education, work
  experience and resume sections (`app/services/analyzer.py`).
- **Job matching** — two methods, compared empirically in the thesis:
  - *TF-IDF + cosine similarity* (lexical baseline, scikit-learn)
  - *Sentence-BERT embeddings* (`all-MiniLM-L6-v2`, sentence-transformers),
    with a fitted logistic (Platt-style) calibration that maps raw cosine
    similarity onto an interpretable 0–100 scale.
- **Grammar checking** — offline LanguageTool with CV-specific filtering.
- **Scoring** — weighted total: skills 30%, education 20%, experience 20%,
  job relevance 30%, plus prioritized suggestions.

## Requirements

- Python 3.10+
- Node.js 18+ (only to build/develop the frontend)
- ~500 MB disk for the SBERT model (downloaded and cached on first run;
  the app falls back to TF-IDF if the model cannot load)

## Quick start (development)

Backend (Flask, port 5000):

```bash
pip install -r requirements.txt
python run.py
```

Frontend (Vite dev server, port 3000, proxies `/api` to Flask):

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Production

```bash
cd frontend && npm run build && cd ..
python run.py
```

Flask serves both the API and the built frontend on `http://localhost:5000`.

## API

`POST /api/analyze` — multipart form data:

| field | type | required |
|---|---|---|
| `resume` | file (PDF/DOCX) | yes |
| `job_description` | text | no |

Returns a JSON object with `analysis` (extracted entities), `score`
(total, breakdown, match score, suggestions), `grammar` and, when a job
description is provided, `job_description` (parsed requirements and skill
coverage). The response shape is typed in `frontend/src/types/index.ts`.

## Evaluation harness

The `eval/` module reproduces the thesis results (TF-IDF vs SBERT on a
hand-labeled 6×6 gold set of 36 resume–job pairs):

```bash
python -m eval.run_eval          # metrics + plots → eval/results/
python -m eval.run_extraction    # extraction P/R/F1 on 6 labeled resumes
python -m eval.calibrate         # refit the calibration mapping
```

All randomness is seeded; see `eval/README.md` for the labeling scheme and
how to extend the gold set.

## Project structure

```
app/               Flask API (routes + services)
  services/        parser, analyzer, jd_parser, scorer, embeddings,
                   calibration, grammar
frontend/          React 19 + TypeScript + Vite SPA
eval/              evaluation harness, gold datasets, results
thesis/            thesis document generator and figures (Albanian, UBT format)
run.py             entry point (Flask, port 5000)
```

## License and data

Uploaded documents are processed in memory / a temporary folder and deleted
after each request; nothing is stored permanently. The evaluation datasets
under `eval/data/` are synthetic documents written for this project.
