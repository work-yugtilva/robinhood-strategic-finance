# Data quality report

**Cutoff:** 2026-09-28. **Status:** VALIDATED FINANCIALS; Q4 PLATFORM-ASSET REVISION DOCUMENTED

Financial rows: 14 (2023 Q1–2026 Q2). Monthly KPI rows: 44 (Jan 2023–Aug 2026). Quarterly KPI rows: 14 (through 2026 Q2).

Sources for proof gates: [Robinhood Q2 2026 release](https://www.globenewswire.com/news-release/2026/07/29/3335576/0/en/robinhood-reports-second-quarter-2026-results.html); [SEC company-facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0001783879.json); [2025 amended 10-K/A](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000029/0001783879-26-000029-index.htm); [2025 Q3 10-Q](https://www.sec.gov/Archives/edgar/data/1783879/000178387925000310/0001783879-25-000310-index.html); [Robinhood Q4 2025 release](https://www.globenewswire.com/news-release/2026/02/10/3235771/0/en/robinhood-reports-fourth-quarter-and-full-year-2025-results.html).

## Proof gates
- 2026 Q2 revenue: 776.0 + 389.0 + 143.0 = 1308.0 USD million.
- 2026 Q2 operating expenses: six categories sum to 734.0 vs 734.0 USD million.
- 2026 Q2 adjusted EBITDA: 742.0 EBITDA + 105 SBC + 23 restructuring − 106 deconsolidation gain − 23 equity gains = 741.0, matching reported 741.0 USD million.
- 2025 Q4 FY-minus-nine-month checks (amended 10-K/A, Q3 10-Q, company Q4 release; USD million):

  - revenue_m: 4473.0 − 3190.0 = 1283.0; Q4 release 1283.0.
  - operating_expense_m: 2379.0 − 1746.0 = 633.0; Q4 release 633.0.
  - net_income_m: 1883.0 − 1278.0 = 605.0; Q4 release 605.0.

## Annual SEC statement ties (USD million; tolerance ±1)
- 2023 revenue_m: SEC annual 1865.0; sum of four release quarters less SEC annual 0.0.
- 2023 operating_expense_m: SEC annual 2401.0; sum of four release quarters less SEC annual 0.0.
- 2023 net_income_m: SEC annual -541.0; sum of four release quarters less SEC annual 0.0.
- 2024 revenue_m: SEC annual 2951.0; sum of four release quarters less SEC annual 0.0.
- 2024 operating_expense_m: SEC annual 1897.0; sum of four release quarters less SEC annual 0.0.
- 2024 net_income_m: SEC annual 1411.0; sum of four release quarters less SEC annual 0.0.
- 2025 revenue_m: SEC annual 4473.0; sum of four release quarters less SEC annual 0.0.
- 2025 operating_expense_m: SEC annual 2379.0; sum of four release quarters less SEC annual 0.0.
- 2025 net_income_m: SEC annual 1883.0; sum of four release quarters less SEC annual 0.0.

## Reconciliation and extraction exceptions
- All populated quarterly revenue/expense category sums, pretax/net income, operating-income arithmetic, and adjusted EBITDA adjustment rows tie within ±1 USD million.
- No release retrieval or parse failures.

## Coverage gaps and source differences
- SEC filing HTML and Robinhood IR downloads returned HTTP 403 in this environment. SEC company-facts supplies standard tagged GAAP revenue cross-checks; Robinhood-authored GlobeNewswire releases supply statements, non-GAAP reconciliations, and accessible monthly KPI tables. Filing-specific product revenue note details and some operating metrics remain unavailable from this cache.
- Quarter-end months (March, June, September, December) lack standalone releases in this archive, but the following month’s company release reports their values in its prior-month comparison column. Those values are backfilled with that release as provenance. Values absent from both columns remain null.
- Monthly KPI headings and fields change over time; blanks in the processed files are undisclosed or unavailable, never inferred zero.
- In 2025 Q2–Q3 the monthly crypto volume table split Robinhood App and Bitstamp rows; the total is missing in this monthly parser. Phase 3 separately registers Q2 $28B App + $7B Bitstamp and Q3 $80B total from company quarterly releases. The monthly blanks remain blank; analytical quarterly volume uses the cited quarterly disclosure.
- Q2 2026 event-contract volume is 13.5B from summing rounded monthly data versus 13.6B reported in the quarterly release. Phase 3 uses 13.6B for quarterly revenue-per-contract analysis and retains the monthly sum in the processed KPI table.
- Adjusted EBITDA is company-reported and separately recomputed from the adjustment rows in all 14 accessible quarterly releases. The reconciliation is non-GAAP and should not be conflated with operating income.
- Material difference threshold for rounded earnings-release assets versus monthly period-end assets: USD 1 billion. Both values are preserved; the revised monthly value is the quarter-end aggregation input.

### Missing financial fields (quarters of 14)
- adjusted_ebitda_m: 0
- adjusted_ebitda_recomputed_m: 0
- brokerage_transaction_expense_m: 0
- credit_loss_expense_m: 7
- crypto_revenue_m: 0
- depreciation_amortization_adjustment_m: 0
- ebitda_non_gaap_m: 0
- equities_revenue_m: 0
- event_contracts_revenue_m: 13
- general_administrative_expense_m: 0
- income_tax_expense_m: 0
- interest_expense_adjustment_m: 0
- marketing_expense_m: 0
- net_income_m: 0
- net_interest_revenue_m: 0
- operating_expense_m: 0
- operating_income_m: 0
- operations_expense_m: 0
- options_revenue_m: 0
- other_income_m: 0
- other_revenue_m: 0
- other_transaction_revenue_m: 12
- pretax_income_m: 0
- revenue_m: 0
- sbc_adjustment_m: 8
- technology_development_expense_m: 0
- transaction_revenue_m: 0
- unclassified_transaction_revenue_m: 0

### Missing monthly KPI fields (months of 44)
- assets_under_custody_b: 18
- cash_deposits_b: 41
- cash_sweep_b: 0
- crypto_notional_b: 3
- equity_notional_b: 0
- event_contracts_b: 34
- funded_customers_m: 11
- margin_book_b: 0
- net_cumulative_funded_accounts_m: 33
- net_deposits_b: 0
- options_contracts_m: 0
- platform_assets_b: 26

### Missing quarterly-only operating fields (quarters of 14)
- arpu_usd_annualized: 0
- gold_subscribers_m: 2
- investment_accounts_m: 4
- platform_assets_earnings_b: 8

### Material platform-asset source differences
- 2025Q4: precise month-end 322.1 USD billion; rounded earnings release 324.0 USD billion; difference 1.9 USD billion.
- Robinhood explicitly revised December 2025 assets after the preliminary 2026-02-10 earnings release to reflect final crypto pricing data. The 2026-02-19 [January operating release](https://investors.robinhood.com/news-releases/news-release-details/robinhood-markets-inc-reports-january-2026-operating-data) and [2025 10-K/A](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000029/hood-20251231.htm) report $322.1B; use it as canonical. Keep preliminary $324B for audit. See [reconciliation](reports/Q4_2025_PLATFORM_ASSET_RECONCILIATION.md).

## Comparability and modeling limits
- TradePMR (2025), Bitstamp (2025), and WonderFi (2026) change the scope of customers, assets, and/or volume. Historical growth spanning those dates is not a clean organic measure.
- February 2026 cash-sweep program changes moved balances to free credit; July 2026 Trump Accounts affected platform assets and deposits without an equivalent funded-customer change. Treat both as definition breaks.
- Product-level active users, retention, CAC, and contribution margin are not a consistent public series. Later work may calculate labeled aggregate proxies; none are reported here.
- Historical outputs are source facts and arithmetic only. No 2026 Q3 financial result, forecast, initiative ROI, or strategic recommendation is included.

## Rebuild
`python3 -m src.pipeline` uses local `data/raw/` cache and fetches missing releases; `--refresh` re-downloads sources. Network failures name the source. Raw HTML/JSON is ignored by Git; checksums and retrieval URLs are in `data/source_manifest.csv`.
