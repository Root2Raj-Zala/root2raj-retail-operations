CREATE TABLE "model_scorecard" (
  "model" TEXT NOT NULL,
  "selected_on_validation" INTEGER NOT NULL,
  "validation_mae_units" REAL NOT NULL CHECK ("validation_mae_units" >= 0),
  "validation_wape_pct" REAL NOT NULL CHECK ("validation_wape_pct" >= 0),
  "test_mae_units" REAL NOT NULL CHECK ("test_mae_units" >= 0),
  "test_wape_pct" REAL NOT NULL CHECK ("test_wape_pct" >= 0),
  PRIMARY KEY ("model")
) STRICT;

CREATE TABLE "holdout_forecasts" (
  "StockCode" TEXT NOT NULL,
  "date" TEXT NOT NULL,
  "units" INTEGER NOT NULL CHECK ("units" >= 0),
  "Gradient boosting 15 leaves" REAL NOT NULL,
  "Gradient boosting 31 leaves" REAL NOT NULL,
  "Trailing 7-day mean" REAL NOT NULL,
  "Same weekday last week" REAL NOT NULL,
  "Yesterday" REAL NOT NULL,
  "Ridge alpha=100" REAL NOT NULL,
  "Ridge alpha=1" REAL NOT NULL,
  PRIMARY KEY ("StockCode", "date")
) STRICT;

CREATE TABLE "per_product_errors" (
  "StockCode" TEXT NOT NULL,
  "model" TEXT NOT NULL,
  "mae_units" REAL NOT NULL CHECK ("mae_units" >= 0),
  "wape_pct" REAL NOT NULL CHECK ("wape_pct" >= 0),
  PRIMARY KEY ("StockCode", "model")
) STRICT;