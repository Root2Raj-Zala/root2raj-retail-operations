CREATE TABLE "scenario_summary" (
  "window_days" INTEGER NOT NULL CHECK ("window_days" >= 0),
  "policy" TEXT NOT NULL,
  "matched_value_gbp" REAL NOT NULL CHECK ("matched_value_gbp" >= 0),
  "unmatched_identified_value_gbp" REAL NOT NULL CHECK ("unmatched_identified_value_gbp" >= 0),
  "missing_id_credit_value_gbp" REAL NOT NULL CHECK ("missing_id_credit_value_gbp" >= 0),
  "all_credit_value_gbp" REAL NOT NULL CHECK ("all_credit_value_gbp" >= 0),
  "identified_credit_value_gbp" REAL NOT NULL CHECK ("identified_credit_value_gbp" >= 0),
  "coverage_all_pct" REAL NOT NULL CHECK ("coverage_all_pct" >= 0),
  "coverage_identified_pct" REAL NOT NULL CHECK ("coverage_identified_pct" >= 0),
  "value_weighted_lag_days" REAL NOT NULL,
  PRIMARY KEY ("window_days", "policy")
) STRICT;

CREATE TABLE "lag_distribution" (
  "window_days" INTEGER NOT NULL CHECK ("window_days" >= 0),
  "policy" TEXT NOT NULL,
  "lag_bucket" TEXT NOT NULL,
  "matched_value_gbp" REAL NOT NULL CHECK ("matched_value_gbp" >= 0),
  PRIMARY KEY ("window_days", "policy", "lag_bucket")
) STRICT;

CREATE TABLE "monthly_linkage" (
  "window_days" INTEGER NOT NULL CHECK ("window_days" >= 0),
  "policy" TEXT NOT NULL,
  "month" TEXT NOT NULL,
  "matched_value_gbp" REAL NOT NULL CHECK ("matched_value_gbp" >= 0),
  "identified_credit_value_gbp" REAL NOT NULL CHECK ("identified_credit_value_gbp" >= 0),
  "all_credit_value_gbp" REAL NOT NULL CHECK ("all_credit_value_gbp" >= 0),
  "coverage_all_pct" REAL NOT NULL CHECK ("coverage_all_pct" >= 0),
  PRIMARY KEY ("window_days", "policy", "month")
) STRICT;