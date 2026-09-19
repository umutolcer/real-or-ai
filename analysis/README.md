# Real or AI? analysis

Analysis code for my CS 395 internship study at TU Delft (AI DeMoS Lab). The Streamlit app is in the main repo (`app.py`). This folder has the code behind the numbers and figures in the report.

## Files

- `analyze_study.py` - cleaning, statistics, figures and tables
- `anonymize_responses.py` - makes the shareable csv from the raw export
- `make_diagrams.py` - the two diagrams in the report
- `data/responses_anonymized.csv` - 30 participants, 318 rows (18 are duplicates, removed in the script)
- `data/detector_results.json` - UniversalFakeDetect predictions

## Run

```bash
pip install -r requirements.txt
python analyze_study.py
python make_diagrams.py
```

Everything goes to `report_outputs/`. You can also pass your own files: `python analyze_study.py responses.csv detector_results.json`. Without the detector file the human vs detector part is skipped.

## Notes

- duplicate rows: the first one per participant and item is kept
- "Not sure" counts as incorrect for accuracy, like in the app
- the confidence comparisons leave out "Not sure"
- 5 fast responders (median under 8 s) stay in, the output also has a check without them
- 30 people and 9 items, so everything is exploratory

The raw export has the names people typed in, so it is not in the repo. `anonymize_responses.py` removes them.
