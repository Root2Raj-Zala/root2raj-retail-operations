# Data contract and reproducibility

Input: unchanged UCI Online Retail workbook, 541,909 rows and the eight named source columns checked by analysis.py. Source: https://archive.ics.uci.edu/dataset/352/online+retail. Chen, D. (2015), DOI https://doi.org/10.24432/C5BW33, CC BY 4.0.

Grain: one invoice line. CustomerID and descriptions may be missing. An invoice is not a line and a customer is not an invoice. Exact complete-row duplicates are removed with retained-duplicate sensitivity reported; that is an analytical assumption rather than proof of faulty source records.

After type normalization, records are partitioned into positive sale, cancellation credit, negative adjustment or excluded. Credits require a C-prefixed invoice and negative quantity. Prices must be positive, quantity nonzero, values finite and dates/invoices present. Customer IDs are not a prerequisite for revenue totals, but they are for customer-level analysis.

Recorded line value is quantity times unit price. Positive sale values, absolute cancellation credits and signed adjustments reconcile to the commercial net. Monthly aggregates and a separate SQLite calculation are checked independently. Local SQL evidence omits CustomerID; only aggregates and code are published.

```bash
python -m pip install -r requirements.txt
python analysis.py
```

The script downloads the public source if absent. Inspect outputs/validation.json, requiring every check to be true, and outputs/results.json for measured definitions and limitations. Raw data and outputs/retail.sqlite stay local. GitHub Actions repeats the entire analysis on a fresh runner.
