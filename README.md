# Retail revenue, with the credits left in

A Root2Raj portfolio case study, implemented with AI assistance using a historical public dataset. This is portfolio work, not client work or employment experience. The portfolio owner holds an MSc in Data Science from the University of East London (May 2025).

## Business question
How much of recorded positive invoice value remains after cancellation credits, and how reliable are the customer and trend views?

## Verified findings
- 541,909 original rows; 5,268 exact duplicates removed under an explicit assumption.
- GBP 10,642,110.80 positive invoice-line value.
- GBP 893,979.73 cancellation credit value.
- GBP 9,748,131.07 net recorded invoice value.
- Credit value / positive value: 8.40%. This is not an item or order return rate.
- 24.93% of raw rows lack a customer ID. Identified purchasers cover 83.51% of positive sales value.
- Top 434 identified purchasers (10%, rounded up) contribute 61.45% of identified-purchaser positive value.
- Keeping duplicate rows adds GBP 24,573.74 to positive value.

## Method
The source remains unchanged. The analysis drops exact duplicate rows and reports sensitivity. A valid line has an invoice/date, finite numeric quantity/price, price > 0 and quantity != 0. Positive non-cancellation lines are sales; negative lines with invoice codes starting C are credits; negative non-cancellation lines are separate adjustments. All other lines are excluded and counted. Customer concentration uses identified purchasers and positive value only. Recorded values include non-merchandise codes and are not audited revenue or profit.

## Reproduce
Python 3.11+:

    python -m pip install -r requirements.txt
    python analysis.py

The script downloads the UCI workbook if absent. It checks schema and record count, then writes outputs/results.json, outputs/validation.json and a local outputs/retail.sqlite. Run queries.sql against that database to independently inspect the summaries. Website outputs contain aggregates, not customer identifiers.

## Validation
Eight checks pass: expected input row count, exhaustive row partition, duplicate reconciliation, value reconciliation, monthly reconciliation, bounded identified-customer coverage, nonnegative credit value and independent SQLite reconciliation. results.json contains the workbook SHA-256 hash and all definitions/limitations. The checks establish internal consistency, not source-accounting correctness.

## Limitations
Historical, single-retailer data: 1 December 2010 to 9 December 2011. December 2011 is partial and excluded from chart comparisons by default. Identical invoice lines may be legitimate repeats; deduplication is an assumption. Credits have not been matched to original purchases, so reasons, timing and actual return rates are unknown. Missing identifiers limit customer conclusions. No costs, experiment or measured commercial improvement are available.

## Proposed next decisions
Investigate the largest credited stock codes and invoice linkage. Keep credits alongside gross positive value in reports. Validate customer identifiers before retention targeting. Request costs and fulfilment data before profit or return-rate claims. These are recommendations, not observed improvements.

## Attribution
Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33. https://archive.ics.uci.edu/dataset/352/online%2Bretail. CC BY 4.0. The analysis cleans and aggregates the original data; no endorsement is implied.

