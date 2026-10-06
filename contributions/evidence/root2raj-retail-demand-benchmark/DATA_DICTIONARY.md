# Evidence dictionary
model_scorecard.csv: seven candidates; validation and test MAE (units) and WAPE (%). selected_on_validation flags the pre-test choice.
holdout_forecasts.csv: stock code × date × observed units, followed by each model's predicted units. These are daily product aggregates; no customer or invoice IDs.
per_product_errors.csv: test MAE and WAPE by product and model, where product aggregate units are positive.
All forecasts use observations available through the previous day. WAPE can exceed 100%. Derived evidence is CC BY 4.0; code is Apache 2.0.
