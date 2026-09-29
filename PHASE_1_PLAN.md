# Robinhood Strategic Finance & Operating Model — approved scope

**Central question:** Robinhood has rapidly increased customer assets and expanded its product set. Which financial and operating drivers are actually converting that scale into sustainable revenue and operating profit, and what would need to happen for that growth to continue?

**Independent project:** This is an independent portfolio project based solely on publicly available information and is not affiliated with Robinhood Markets, Inc.

**Source cutoff:** September 28, 2026. Historical financials end at 2026 Q2; July and August 2026 are monthly operating observations, not Q3 financial results.

## Approved analytical scope

The finished work should explain customer scale, trading activity, realized monetization, product mix, interest-bearing balances, and expense growth. It should distinguish more stable sources of revenue from market-activity and interest-rate exposure, and use a 12-quarter driver-based forecast (2026 Q3–2029 Q2) to test what must be true for sustainable operating-profit growth. Facts, arithmetic, estimates, and assumptions must be labeled **REPORTED**, **DERIVED**, **ESTIMATED**, and **ASSUMPTION**.

Headline historical economics are revenue and transaction revenue per funded customer, platform assets and deposits per funded customer, company ARPU, product-level realized revenue per unit of disclosed volume, and incremental operating margin. Marketing expense divided by net customer additions may appear only as a **marketing efficiency proxy**; it is not CAC. Public data do not support a headline LTV, product contribution margin, or initiative ROI.

The later strategic investment scenario analysis compares three broad paths: **Customer & Asset Growth**, **Transaction Product Expansion**, and **Recurring / Less Market-Sensitive Monetization**. For each path it will show required assumptions, revenue and operating-profit implications, sensitivities, downside risks, and break-even conditions. The analysis will avoid assigning unsupported product returns.

The approved workbook has **12 tabs**: Cover, Sources, Assumptions, Historical Financials, Operating KPIs, Revenue Drivers, Expense Build, Forecast, Scenarios, Sensitivity, Strategic Analysis, and Executive Dashboard. GAAP and adjusted EBITDA reconciliation belongs inside the historical/expense tabs. The later executive deck should have 6–8 takeaway-led slides.

## Historical source inventory

Use SEC filings for tagged GAAP facts and filing references, and Robinhood-authored quarterly and monthly releases for detailed statement tables and operating metrics. The [SEC company-facts API](https://data.sec.gov/api/xbrl/companyfacts/CIK0001783879.json) supplies standard taxonomy facts; it does not expose every company-specific category. The canonical [quarterly-results archive](https://investors.robinhood.com/financials/quarterly-results) and [monthly-metrics archive](https://investors.robinhood.com/financials/monthly-metrics) identify company publications. Where IR direct download is blocked, record both the canonical IR page and the Robinhood-authored GlobeNewswire retrieval URL in `data/source_manifest.csv`.

| Period | SEC accession | Period | SEC accession |
|---|---|---|---|
| 2023 Q1 | [0001783879-23-000117](https://www.sec.gov/Archives/edgar/data/1783879/000178387923000117/0001783879-23-000117-index.htm) | 2023 Q2 | [0001783879-23-000175](https://www.sec.gov/Archives/edgar/data/1783879/000178387923000175/0001783879-23-000175-index.htm) |
| 2023 Q3 | [0001783879-23-000268](https://www.sec.gov/Archives/edgar/data/1783879/000178387923000268/) | 2023 FY | [0001783879-24-000054](https://www.sec.gov/Archives/edgar/data/1783879/000178387924000054/0001783879-24-000054-index.htm) |
| 2024 Q1 | [0001783879-24-000145](https://www.sec.gov/Archives/edgar/data/1783879/000178387924000145/0001783879-24-000145-index.htm) | 2024 Q2 | [0001783879-24-000233](https://www.sec.gov/Archives/edgar/data/1783879/000178387924000233/0001783879-24-000233-index.htm) |
| 2024 Q3 | [0001783879-24-000296](https://www.sec.gov/Archives/edgar/data/1783879/000178387924000296/0001783879-24-000296-index.htm) | 2024 FY | [0001783879-25-000049](https://www.sec.gov/Archives/edgar/data/1783879/000178387925000049/0001783879-25-000049-index.htm) |
| 2025 Q1 | [0001783879-25-000145](https://www.sec.gov/Archives/edgar/data/1783879/000178387925000145/0001783879-25-000145-index.htm) | 2025 Q2 | [0001783879-25-000251](https://www.sec.gov/Archives/edgar/data/1783879/000178387925000251/0001783879-25-000251-index.htm) |
| 2025 Q3 | [0001783879-25-000310](https://www.sec.gov/Archives/edgar/data/1783879/000178387925000310/0001783879-25-000310-index.html) | 2025 FY | [10-K/A 0001783879-26-000029](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000029/0001783879-26-000029-index.htm) |
| 2026 Q1 | [0001783879-26-000062](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000062/0001783879-26-000062-index.htm) | 2026 Q2 | [0001783879-26-000114](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000114/0001783879-26-000114-index.htm) |

The amended FY 2025 filing corrected EDGAR formatting; retain the original 10-K accession in metadata and use the amended filing for annual checks. A [Robinhood-authored Q4 release](https://www.globenewswire.com/news-release/2026/02/10/3235771/0/en/robinhood-reports-fourth-quarter-and-full-year-2025-results.html) supplies the quarter-only cross-check. [August 2026 operating data](https://www.globenewswire.com/news-release/2026/09/10/3359962/0/en/robinhood-markets-inc-reports-august-2026-operating-data.html) is the last monthly publication inside the cutoff.

## Phase 2 data architecture

Source URLs and accessions → ignored local raw cache with SHA-256 manifest → normalized quarterly financial and monthly KPI facts → quarterly KPI aggregates only when all required months are disclosed → reconciliation and coverage report. `data/source_registry.csv` records individual populated facts and arithmetic with approved fields; `data/data_dictionary.csv` records units, frequency, stock/flow status, aggregation, and definition breaks. Missing values remain null. The run command and files are in [README.md](README.md).

Quarterly financials cover **2023 Q1–2026 Q2 (14 rows)**. Monthly KPI periods cover **January 2023–August 2026 (44 rows)**. Completed quarterly KPI periods cover the same 14 quarters. Monthly flows sum to a quarter only when all three constituent months exist; period-end stocks use the last month. The quality report must explicitly distinguish unavailable publications from parser failures. The eventual forecast must use operating drivers rather than arbitrary revenue growth percentages.

**Initial proof gates:** [2026 Q2](https://www.globenewswire.com/news-release/2026/07/29/3335576/0/en/robinhood-reports-second-quarter-2026-results.html) revenue $776m transaction + $389m net interest + $143m other = $1,308m, six expense lines = $734m, and company adjusted EBITDA = $741m. For 2025 Q4, SEC amended FY revenue $4,473m less Q3 nine-month revenue $3,190m = $1,283m, matching the Q4 release. Every populated quarter must tie revenue and expense categories and operating-income arithmetic to a ±$1m rounding tolerance; annual revenue totals must tie SEC tagged facts.

## Known limitations and later assumptions

- Product-level active customers, trading frequency, retention cohorts, acquisition-channel CAC, product contribution profit, internal budgets, and initiative returns are not consistently public. Later modeling may use defensible labeled proxies only where they answer a decision question.
- Quarter-end monthly operating releases may not be individually retrievable through the accessible release archive. A partial quarter's monthly flows cannot be summed into a reported quarter. Quarterly earnings releases may disclose quarterly KPI figures separately; preserve their original frequency.
- Bitstamp, TradePMR, and WonderFi affect scope and comparability. Cash-sweep treatment changed in February 2026; July 2026 Trump Accounts affect assets/deposits differently from funded customers. Mark breaks before interpreting growth.
- Interest-rate context from [FRED DFF](https://fred.stlouisfed.org/series/DFF) is external and is not Robinhood's realized yield. Later sensitivity cases require explicit balance, yield, and pass-through assumptions.
- A 14-quarter relationship is descriptive. Changes in market activity, acquisitions, and definitions prevent causal claims from simple correlations.

## Questions for the finished analysis

1. What part of historical revenue growth reflects customer scale, activity, realized monetization, and product mix?
2. Which revenue streams are most durable, and which depend on market activity or interest rates?
3. Are funded-customer, deposit, and asset gains improving aggregate monetization?
4. How do interest-bearing balances and rate changes affect net interest revenue?
5. How much incremental revenue has become operating profit after expense and credit-loss growth?
6. What must be true for each of the three approved strategic paths to outperform the others?

**Phase 2 stopping point:** validated inspectable historical CSVs, committed manifests and registry, tests, and `DATA_QUALITY_REPORT.md`. Forecast, workbook, dashboard, deck, scenarios, and recommendation remain later phases.
