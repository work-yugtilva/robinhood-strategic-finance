# Strategic decision framework

**Decision:** Concentrate management attention on realized trading monetization, customer balance conversion, and expense conversion. The three paths are complementary sources of growth, not investment proposals with invented returns. Values are Base-relative **defined shocks** for 2027; they are not expected returns or probabilities. [Forecast sensitivities](../data/forecast/sensitivity_results.csv).

| Analytical path | Defined shock | 2027 revenue change | Operating-income change | Management control | Data confidence |
|---|---|---:|---:|---|---|
| Customer & asset scale | customer_additions +25% | $37m | $9m | Medium | High |
| Transaction engagement | options_activity +20% | $274m | $264m | Medium | Medium |
| Recurring / balance monetization | cash_capture +50% | $85m | $85m | Medium for balance capture; low for policy rates | Medium for balance capture; low for rate pass-through |

| Path | Historical evidence | Primary financial drivers | Execution dependency |
|---|---|---|---|
| Customer & asset scale | Funded customers and deposits grew, but asset scope includes acquisitions and market value changes. | Net additions, deposits, interest-bearing share, revenue/customer | Customers and deposits must earn revenue without proportionate spending. |
| Transaction engagement | Measured 2024 transaction growth was primarily activity-led; options monetization is directly observable. | Contracts/customer, crypto and equity notional/customer, realized product rates | Trading units and realized monetization must hold through weaker market periods. |
| Recurring / balance monetization | Balance growth offset lower realized yields in the matched 2025Q2–2026Q2 interest disclosure; Gold is modest. | Earning balances, net realized yields, Gold subscribers | Balances and net spreads must persist; Gold alone is too small to replace trading volatility. |

**Customer and asset scale.** Reported 2025 Q4 platform assets of $322.1b and 27.0m funded customers were much larger than 2023 Q4's $102.6b and 23.4m, but acquisitions and market value changes affect assets. Net additions and deposits are observable. The model's marketing cost response means more additions alone do not offset a 20% crypto-volume/customer shock in 2027; that is a limitation of the consolidated expense proxy, not a claim that new customers lack long-term value. [Historical analysis](HISTORICAL_ANALYSIS.md); [2025 filing](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000029/hood-20251231.htm).

**Transaction engagement.** In the exact 2024 versus 2023 bridge, measured comparable-product activity contributed $621m of $862m transaction growth. The +20% options-activity case adds $274m revenue in 2027, while a 20% transaction-monetization decline removes $613m. These responses depend on market activity and pricing; funded customers are an aggregate denominator, not product active users. [Historical bridge](../data/analysis/revenue_growth_bridges.csv).

**Balance and recurring monetization.** The matched 2025 Q2–2026 Q2 disclosure had a +$90.5m interest balance effect and -$13.5m yield/mix effect. A defined +50% cash-capture shock adds $85m in 2027; this is a model test, not a plan. In 2027 Base, interest/balance revenue is 36.3% of total, whereas separately disclosed Gold is 4.5%. The -100 bp modeled policy case reduces revenue by $265m; Cash Sweep is excluded from that policy case. [Q2 filing](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000114/hood-20260630.htm); [interest audit](INTEREST_SENSITIVITY_AUDIT.md).

## What must be true — exact engine thresholds

The first three tests recover **2027 Base operating income**, holding all other selected inputs fixed. They solve the full consolidated model and include its specified variable costs. The final two are algebraic operating benchmarks, not company targets.

| Condition | Required input | Method |
|---|---|---|
| Options activity offsets 50bp policy decline | 28.74 contracts per average funded customer per quarter; outside recent range | Increase each 2027 quarter options/customer; include variable brokerage cost |
| Customer additions offset 20% crypto activity decline | not attainable under the modeled cost response; outside recent range | Increase each 2027 quarter net additions; roll customers and interest balances |
| Deposits offset 10% transaction monetization decline | 69.86 USD billions net deposits per quarter; outside recent range | Increase each 2027 quarter deposits; cash capture and yields unchanged |
| 2027 expense eliminating operating-income growth | 3,644.46 USD millions annual | 2027 revenue minus 2026 Base operating income; expense ceiling, not guidance |
| 2027 revenue preserving 2026 Base margin at planned costs | 5,792.67 USD millions annual | 2027 expense plan / (1 - 2026 Base operating margin); holds expense plan fixed |

**Interpretation:** The options threshold lies above the 2025 Q4–2026 Q2 observed 21.6–27.7 quarterly contracts per average funded customer. The deposit threshold is well above the recent $15.9–$21.7b quarterly range. These tests expose how little of a deposit is assumed to become interest-earning cash immediately. They do not forecast management action.

## Revenue composition and downside

| Period / case | Market activity | Interest / balance | Disclosed Gold | Unclassified |
|---|---:|---:|---:|---:|
| 2026 Q2 ACTUAL | 55.6% | 29.7% | 4.1% | 10.6% |
| 2027 Base FORECAST | 52.3% | 36.3% | 4.5% | 6.9% |
| 2027 Upside FORECAST | 54.1% | 35.3% | 4.2% | 6.4% |
| 2027 Downside FORECAST | 50.7% | 35.7% | 5.3% | 8.2% |

All buckets sum to total revenue. The forecast dollar amounts are in the [scenario summary](../data/forecast/scenario_summary.csv). Unclassified revenue is never called recurring. Neither activity nor interest revenue is inherently preferable: their market dependencies differ and product-level margins are unavailable. The Upside remains more activity-dependent than Base; the Downside's mix is also shaped by lower realized yields.

## Management risk map

The exposures below are isolated shocks with different sizes, not comparable probabilities or a risk score. Control and confidence are analyst judgments grounded in disclosed coverage. [Full sensitivity table](../data/forecast/sensitivity_results.csv).

| Risk | Variable affected | Defined exposure | Management control | Forecast confidence |
|---|---|---:|---|---|
| Trading activity | Options units; revenue and brokerage cost | -$264m 2027 operating income at -20% | Partial | Medium |
| Transaction monetization | Options, crypto, equities, event revenue | -$613m 2027 revenue at -20% broad transaction pricing | Partial | Low post acquisition for crypto |
| Policy rates | Net interest revenue | -$265m 2027 revenue at -100 bp modeled policy | Low | Medium-low |
| Customer growth | Customers, revenue, marketing | -$37m 2027 revenue at -25% additions | Medium | Low for marginal profit |
| Technology spending | Operating expense | -$115m 2027 operating income at +10% spend | High | Medium |
