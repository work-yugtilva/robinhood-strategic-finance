# Forecast method — Phase 4

**Information cutoff:** September 28, 2026. Historical financial actuals end at 2026 Q2. July and August are only monthly operating observations; September and all Q3 financial results are forecast. Run `python -m src.phase4` after `python -m src.phase3`; Phase 4 reads but does not rewrite historical files. Units are in field names; USD financial flows are millions, assets and trading notional are billions.

## Calibrated operating equations

| Component | Equation and treatment | Forecast input source / limitation |
|---|---|---|
| Customers | End = beginning + net additions; quarterly average = mean of adjacent ends | 2025 Q3–2026 Q1 clean net-addition median. 2026 Q2 acquisition-era increase is not an organic run rate. |
| Platform assets | End = beginning + deposits + market/value change + acquired assets + other change | Market/value change is an analyst scenario. Acquired assets default to zero. July–August observed other/valuation residual is kept distinct. |
| Options | Average customers × contracts/customer × dollars/contract | Recent comparable contracts and realized dollars/contract; funded customers are not product active users. |
| Equities | Average customers × equity notional/customer × realized bps / 10 | Q3 volume uses actual July/August plus assumed September. |
| Crypto | (App volume + Bitstamp volume) × **blended** realized bps / 10 | Channel volumes are reported; channel revenue is not. Bitstamp and WonderFi make older bps unsuitable without a scope flag. |
| Event contracts | Contracts × realized dollars/contract | Only two recent matched quarterly revenue/unit observations; high uncertainty. |
| Other transaction | Average customers × explicit other transaction dollars/customer | Not buried in product revenue. |
| Net interest | Sum of average margin, cash/deposit, sweep and credit balances × their company realized annualized yields / 4, plus explicit remainder | Policy rate is context only. Cash sweep changed definition in February 2026. Remaining securities lending/financing is low confidence. |
| Gold / other | Average Gold subscribers × realized subscription dollars + quarterly proxy + other residual | Proxy retains reported seasonal pattern. Other residual is unclassified, not recurring. |
| GAAP expense | Six category equations; brokerage tied to a documented activity basket, operations to customers, credit provision to credit exposure, marketing to an explicit spend base and additions, technology and G&A to visible quarterly budgets | Expense behavior is an analyst classification, not a company-disclosed elasticity. |
| Profit | Operating income = revenue − six expenses; net income = pretax − assumed tax; adjusted EBITDA = net income + tax + SBC + D&A + debt-interest addback − forecast nonoperating income | Exceptional gains/charges assumed zero in forecast. Debt interest is already included in the NIR remainder, so its EBITDA addback is not additional revenue. |

The [Q2 2026 filing](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000114/hood-20260630.htm) supplies the interest component and revenue baselines. The [Q2 earnings release](https://investors.robinhood.com/news-releases/news-release-details/robinhood-reports-second-quarter-2026-results) defines adjusted EBITDA and gives a **$2.675–$2.775b** 2026 Adjusted Operating Expenses and SBC range, excluding credit losses and specified items. The model uses this only as a check. [July](https://investors.robinhood.com/news-releases/news-release-details/robinhood-markets-inc-reports-july-2026-operating-data) and [August](https://investors.robinhood.com/news-releases/news-release-details/robinhood-markets-inc-reports-august-2026-operating-data) monthly metrics supply Q3 partial observations. The [September FOMC projections](https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm) are external policy context, not company yield guidance.

**Base calibration:** Net additions 0.3m per normal quarter (median 2025 Q3–2026 Q1); deposits $17.7b (median 2025 Q4–2026 Q2); options/equity activity from the median of 2025 Q4–2026 Q2 and the Q3 partial pace; post-Bitstamp crypto bps from 2025 Q4–2026 Q2; event dollars/contract from 2026 Q1–Q2; neutral asset-value change. Upside and Downside change these operating drivers coherently, with persistent cost commitments in the Downside. Every numerical scenario input, including scenario multipliers and the H2 2026 expense investment step, is in `data/forecast/forecast_assumptions.csv`.

| Major Base driver | Historical evidence | Base input and reason |
|---|---|---|
| Net funded-customer additions | 0.2–0.4m in 2025 Q3–2026 Q1, excluding 2026 Q2 acquisition-era step | 0.30m/quarter; comparable median |
| Net deposits | $15.9–$21.7b in 2025 Q4–2026 Q2 | $17.7b/quarter; recent median |
| Options contracts/customer | 21.6–27.7 quarterly in 2025 Q4–2026 Q2; Q3 partial pace higher | 26.1; median including Q3 partial pace |
| Options dollars/contract | $0.442–$0.476 in the same three quarters | $0.444; recent median |
| Equities notional/customer | $23.5–$34.3b per million average funded customers, same three quarters | $30.3b per million; median including Q3 partial pace |
| Blended crypto bps | 20.4–26.9 bps in 2025 Q4–2026 Q2 | 24.8 bps; post-Bitstamp median, with WonderFi uncertainty |
| Interest-asset realized yields | Q2 2026 margin 4.52%, cash/deposit 2.02%, sweep 0.59%, credit 11.88% | Each starts from its company-specific yield; explicit pass-through to external rate path |
| Gold subscribers | 4.2m at 2025 Q4; 4.3m Q1 and 4.8m Q2 2026 | 0.2m net additions/quarter; below Q2's 0.5m increase |
| Asset-value change | Historical residual includes acquisitions and definition changes | 0% quarterly Base; neutral rather than invented market return |

### Expense behavior and scenario equations

These labels are **analyst modeling assumptions**, informed by the Phase 3 [expense analysis](HISTORICAL_ANALYSIS.md), not measured product margins.

| Category | Behavior | Base equation and historical anchor | Scenario sensitivity |
|---|---|---|---|
| Brokerage / transaction | Semi-variable | $31m fixed-like + $31m × weighted Q2-normalized options, equity, crypto and event units; Q2 reported $62m | Trading units change variable part; activity weights are explicit assumptions |
| Technology / development | Fixed-like | Q2 $256m plus visible $25m H2 product-investment allowance, then $3m/quarter | Upside $5m/quarter later step; Downside $2m |
| Operations | Semi-variable | $62m starting budget × [60% + 40% × customers / Q2's 28.4m]; Q2 reported $57m | Changes with customers but retains a base |
| Provision for credit losses | Variable-like proxy | Average credit balance × 3.75% quarterly analyst provision rate; Q1/Q2 provisions $36m/$56m | Upside 3.3%; Downside 4.2%; not a reported card loss rate |
| Marketing | Semi-variable / discretionary | $129m starting budget × [80% + 20% × net additions / 0.3m]; Q2 reported $104m | Spend flexes less than revenue in Downside |
| General / administrative | Fixed-like | Q2 $199m less $23m restructuring, plus visible $15m H2 allowance; then $2m/quarter | Upside $3m/quarter later step; Downside $1.5m |

The H2 expense allowances were chosen **with the disclosed outlook in view**, so the outlook comparison below is a consistency check, not independent validation. Future significant charges and operating-classified debt interest are assumed zero unless separately shown.

**Q3 nowcast:** July + August reported flow + September assumption. September quarter-end stocks start at the reported August stock. July–August platform asset change less deposits = **$5.4b observed asset/other residual**, including market moves or definition effects that cannot be split publicly. Q3 is marked `FORECAST` and `nowcast=TRUE`, never financial actual. The 2026 Q2 event baseline uses the separately reported **13.6b** contracts rather than the rounded monthly sum.

**Revenue bridge:** For each comparable product, R=C×A×M. Ordered effects are customer `(C1−C0)A0M0`, activity `C1(A1−A0)M0`, and monetization `C1A1(M1−M0)`. Matched interest-asset revenue is split into `(B1−B0)Y0` and `B1(Y1−Y0)`. Other revenue change has its own line; structural/product mix is the exact remainder. Crypto stays in the residual for 2026/2025 and 2027/2026 because the base periods straddle acquisitions. This is accounting attribution, not causal identification.

**Sensitivity:** One-at-a-time shocks rerun Base from pristine assumptions. Two-variable tables rerun the same engine. Dollar effects are conditional on the stated shock sizes; qualitative impact ranks are based on those modeled effects, not a regression or numeric score. The 2029 Q2 run rate is four times that quarter, not a 2029 full-year forecast.

**Diagnostic:** A one-quarter pseudo-historical check holds 2024 Q2 product activity and monetization constant while projecting Q3 customers from Q2's net additions. It compares with 2024 Q3 reported product revenue; assumptions are not tuned to the answer.

| Product | Mechanical Q3 estimate | Q3 actual | Estimate minus actual |
|---|---:|---:|---:|
| Options | $184m | $202m | -$18m |
| Crypto | $82m | $61m | $21m |
| Equities | $40m | $37m | $3m |

This diagnostic shows why constant activity and monetization cannot be treated as a reliable forecast law, especially for crypto.
