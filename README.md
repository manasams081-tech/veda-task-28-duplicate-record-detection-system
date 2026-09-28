# MatchLens — Duplicate Record Detection System

**VEDA Technology — Task 28 | Python Programming Track**

MatchLens is a local web application that identifies **exact duplicates** and **potential near-duplicates** in customer or transaction CSV records.

## Tools used

- Python
- Pandas
- Python standard-library `difflib.SequenceMatcher` for fuzzy matching

No Flask, Streamlit, React, Bootstrap, or other third-party framework is used. The local web server uses Python's built-in `http.server`.

## Deliverables

- `duplicate_detector.py` — reusable duplicate detection engine
- `app.py` — local web application server
- `web/` — unique MatchLens dashboard UI
- `sample_data/customers_demo.csv` — test dataset containing exact and near-duplicate examples
- `reports/` — sample generated reports for the supplied demo dataset
- `outputs/` — runtime-generated reports after a browser scan
- `requirements.txt` — dependency list
- `README.md` — setup and usage guide

## Features

1. Upload a CSV from the browser.
2. Select important matching fields.
3. Normalize text before comparison.
4. Detect exact duplicates using normalized equality.
5. Detect potential duplicates using `difflib.SequenceMatcher`.
6. Choose a fuzzy-match threshold from 50% to 99%.
7. Export:
   - `exact_duplicate_report.csv`
   - `potential_duplicate_report.csv`
   - `cleaned_dataset.csv`
8. Potential matches are **never automatically deleted**.

## Run locally

### Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:8000
```

### Test the supplied sample

1. Start the app.
2. Upload `sample_data/customers_demo.csv`.
3. Keep `name`, `email`, `phone`, and `city` selected.
4. Keep the threshold at `82%`.
5. Click **Run duplicate scan**.
6. Download all three reports.

## Why exact and potential matches are separate

Exact matches are normalized-equality matches. Potential matches use fuzzy similarity and therefore need human validation. The system intentionally does not delete uncertain records automatically, following the task's mini-guide.

## Notes

- CSV uploads are processed locally by this application.
- The demo limits fuzzy matching to 1,500 rows to keep the local browser experience responsive.
- For large datasets, run the core engine in a batch workflow or process smaller batches.
