# Forecast driver framework — selection only

The historical analysis supports a future driver-based forecast. **No forecast values or strategic recommendation are produced in Phase 3.** Ranks are qualitative judgments based on source coverage, direct revenue linkage, and structural comparability, not numeric scores.

| Driver | Rank | Data quality | Later modeling method |
|---|---|---|---|
| Funded customers | PRIMARY DRIVER | Complete; naming transition in 2023 | Quarter-end customers and average customers for flows |
| Options contracts per funded customer | PRIMARY DRIVER | Complete | Activity per funded customer × realized dollars/contract |
| Options revenue per contract | PRIMARY DRIVER | Complete | Historical realized rate with explicit sensitivities |
| Equity notional per funded customer | PRIMARY DRIVER | Complete | Activity per funded customer × monetization bps |
| Crypto notional and realized bps | PRIMARY DRIVER | Scope break after Bitstamp; WonderFi later | Separate acquisition-era regimes and stress volume/bps |
| Event contracts and monetization | SECONDARY DRIVER | Short series and new product | Explicit scenario input only after baseline is established |
| Interest-earning balances and realized yields | PRIMARY DRIVER | Partial history; diverse balance mix | Model margin, cash/sweep and credit separately when sourced |
| Platform assets and net deposits | SECONDARY DRIVER | Acquisitions and AUC/platform definition break | Separate deposits, market moves and acquisitions |
| Gold subscribers and subscription revenue | SECONDARY DRIVER | Quarterly revenue complete; subscriber stock partial | Use disclosed subscription economics and adoption bounds |
| Operating expense categories | PRIMARY DRIVER | Credit-loss line partial; acquisition effects | Category-specific cost paths with explicit leverage assumptions |
| Federal funds rate | CONTEXT ONLY | Complete external series | Sensitivity context and reconciliation check |

The full [driver table](../data/analysis/forecast_driver_summary.csv) gives evidence, relationships, and limitations. The exact [revenue bridges](../data/analysis/revenue_growth_bridges.csv) support options and equity activity as observable transaction drivers. The [interest table](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000114/hood-20260630.htm) supports balance and realized-yield modeling, while [Gold disclosures](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000029/hood-20251231.htm) support a separately identified recurring line. Customer scale is a common denominator, not a substitute for product active users. Acquisition-period residuals must not be projected mechanically.
