# Evidence dictionary
scenario_summary.csv: one row per lookback window and policy. matched_value_gbp is allocated candidate credit value; unmatched_identified_value_gbp is known-ID credit value without allocated capacity; missing_id_credit_value_gbp is unidentifiable credit value. coverage_all_pct divides matched value by all credits; coverage_identified_pct divides by known-ID credits. value_weighted_lag_days averages candidate lags weighted by allocated GBP.
lag_distribution.csv: matched credit GBP by scenario and inclusive upper-bound lag bucket.
monthly_linkage.csv: scenario × credit month; denominators refer to credits recorded in that month. December 2011 is partial.
No invoice or customer identifiers are exported. Amounts are historical GBP, with floating-point calculations checked to tolerances.
