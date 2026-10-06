# Root2Raj: Data Science and Data Architecture Contributions

Two reproducible public-data experiments extend the original retail value audit with model evaluation, constrained linkage algorithms, executable data contracts and lineage.

AI-assisted portfolio work by Ruturajsinh Zala. These experiments are not client work, employment, achieved business improvements, or proof of independent coding proficiency.

| Contribution | Public notebook | Evidence |
|:--|:--|:--|
| Credit linkage under uncertainty | [Kaggle](https://www.kaggle.com/code/ruturajsinhzala/root2raj-credit-linkage-under-uncertainty) | Eight capacity-constrained FIFO/LIFO and lookback scenarios; candidate coverage and timing sensitivity |
| Retail demand forecasting benchmark | [Kaggle](https://www.kaggle.com/code/ruturajsinhzala/root2raj-retail-demand-forecasting-benchmark) | Three baselines, Ridge and gradient boosting; chronological validation, held-out evaluation and per-product errors |

Notebook links are recorded after Kaggle publication; see publication.json for verified versions.

## Why these experiments are useful

The credit notebook avoids treating cancellation codes as verified product returns. It links credits only to strictly earlier same-customer, same-product, exact-price sale capacity; capacity cannot be reused. Missing customer IDs remain unlinked. The 90-day experiment covers about 48.24% of all credit value, with a 3.69-day difference in value-weighted lag between FIFO and LIFO. These are candidates, not established links.

The forecasting notebook selects its 12-product catalog using only initial training data. Lagged features and rolling means use earlier observations only. Validation chooses a model before the test is scored. The Kaggle run selected the 31-leaf gradient boosting model and reported 79.07% held-out WAPE, compared with 106.83% for the same-weekday baseline: 25.99% relative error reduction on this specific holdout. The local run selected the 15-leaf model and reported 78.70% WAPE (26.33% relative error reduction). Local evidence files in this repository describe the local run; the public Kaggle notebook describes its own recorded environment. WAPE is an error measure and can exceed 100%; these results are not an accuracy percentage or inventory savings claim.

## Reproduction is environment-specific

Model selection remains validation-only in both environments. The difference between local and Kaggle results is disclosed rather than selecting the more flattering number. The notebooks display and export exact package versions; methods, source input and split boundaries are fixed, but model results should not be assumed identical across library versions and platforms.

The latest Kaggle revisions keep downloaded workbooks in /kaggle/temp, outside saved output artifacts. Older version 1 runs also saved the original licensed public workbook in their working directory; the source is unchanged UCI data, not private user data. Latest gold exports contain no invoice or customer identifiers.

## Data architecture

- Bronze: unchanged source workbook, verified by SHA-256 and row/schema checks.
- Silver: explicit duplicate handling and sale/credit classification.
- Gold: declared aggregate table grains, SQLite STRICT types, NOT NULL constraints, primary keys and nonnegative measures.
- Contracts: version 1.0.0 with a documented breaking-change rule.
- Lineage: source, implementation and CSV hashes, transformation nodes and edges.
- Validation: SQL integrity and row counts, duplicate rejection, capacity tests, future-perturbation tests, and schema failure tests.
- Privacy: no invoice or customer IDs are exported; the raw workbook is not redistributed.

The architecture is a local reference implementation. It does not claim a deployed warehouse, production monitoring or live orchestration.

## Reproduce

Install requirements into your preferred environment, then run:

    python -m unittest -v test_credit_linkage test_demand_benchmark test_evidence_contracts

To execute both notebooks locally after installing requirements:

    python run_notebooks.py --source-workbook "path/to/Online Retail.xlsx"

The default run directory is .runs inside this project; project-specific caches also stay there. The default kernel uses the same Python interpreter that runs this command. Omit --source-workbook to download the original from UCI. Use --kernel if you have a named Jupyter environment.

Execute either self-contained notebook with Internet enabled or an attached unchanged Online Retail.xlsx. CPU is sufficient. The notebook exports CSVs, charts, results.json, validation.json, environment.json, gold.sqlite, gold_schema.sql, data_contracts.json, lineage.json and a downloadable evidence ZIP.

The source modules are reusable:
- credit_linkage.py: capacity-constrained matching and scenario summaries.
- demand_benchmark.py: training-only catalog selection, daily panels, shifted features and model evaluation.
- evidence_contracts.py: schema contracts, queryable gold products and lineage.

## Provenance and limitations

Source: Chen, D. (2015), [Online Retail](https://archive.ics.uci.edu/dataset/352/online%2Bretail), UCI Machine Learning Repository. DOI [10.24432/C5BW33](https://doi.org/10.24432/C5BW33), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Workbook SHA-256: 43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d

Historical records from a single UK retailer. Exact duplicate removal is an assumption. Credit matching is affected by missing earlier history, missing IDs and exact-price requirements. Forecasting assumes no-record days mean zero observed units, excludes credits, and observes actual previous test days for each one-day-ahead forecast. Stockouts, promotions and future demand are not fully observed. Neither experiment establishes causality or globally novel methods.

Code: Apache 2.0; see LICENSE in this directory. Derived evidence: CC BY 4.0 with attribution to the original source.
