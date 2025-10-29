# AI Talent Match App

This is a Streamlit-based dashboard that dynamically computes and visualizes employee–role fit
based on benchmark profiles using data from BigQuery.

## How it works
1. Input role name, job level, purpose, and benchmark employee IDs.
2. The app recomputes baseline TGV scores in BigQuery.
3. It calculates weighted match rates based on the Success Formula.
4. Results are displayed as a ranked talent list and visual breakdowns.

## Requirements
- Python 3.10+
- BigQuery credentials (service account)
- Libraries (see `requirements.txt`)

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```