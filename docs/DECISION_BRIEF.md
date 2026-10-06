# Decision brief: revenue definitions before a customer strategy

The source contains 541,909 real historical invoice lines. Keeping cancellation credits in the reporting picture changes the interpretation of positive sales. The 8.4% credit-to-positive-value ratio is a monetary ratio, not a customer return rate: credits are not linked to the original purchases.

About a quarter of raw rows lack customer IDs. Customer concentration describes only identified customers; it should not be presented as a complete customer population. Exact duplicate removal changes positive value by GBP 24,573.74. The analysis reports that sensitivity because the source has no unique line identifier that proves each repeated record is an ingestion duplicate.

December 2011 ends on the ninth. A full-month trend comparison would be misleading, so that partial month is distinguished. Non-merchandise codes, recorded prices and adjustments mean net recorded value is not audited revenue, margin or profit.

Recommended business next step: agree ledger definitions and credit matching with the data owner, validate customer identifiers and assess whether the historical period represents the intended decision. No commercial improvement or customer action is claimed from this portfolio analysis.

Interview explanation: I worked from genuine public records, kept positive sales and credits separate, made cleaning assumptions visible and reconciled the calculations independently in SQL. Implementation was AI-assisted; this is portfolio evidence, not client employment.
