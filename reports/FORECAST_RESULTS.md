# Forecast results — operating conditions, not a recommendation

## Executive forecast summary

**MODEL RESULT:** Base revenue is approximately $5.87b in 2027 at a 43.5% GAAP operating margin, and $6.33b in 2028 at a 43.9% margin. These are scenario outputs rather than company guidance. The 2026 total of $5.19b combines **two reported quarters and two forecast quarters**. [Quarterly model](../data/forecast/forecast_quarterly.csv); [summary](../data/forecast/scenario_summary.csv).

## Base Case and revenue drivers

**FACT:** Q2 2026 reported 28.4m funded customers, $1,308m revenue, and $734m operating expense. **MODEL RESULT:** By 2029 Q2, Base reaches 32.0m customers, $6.77b annualized revenue, and a 44.9% modeled operating margin. The model holds aggregate activity per funded customer near the recent post-acquisition calibration instead of requiring perpetual activity acceleration. [Q2 release](https://investors.robinhood.com/news-releases/news-release-details/robinhood-reports-second-quarter-2026-results); [assumptions](../data/forecast/forecast_assumptions.csv).

## Q3 nowcast

**FACT:** July/August options contracts totaled 616.7m, crypto volume $28.4b, and net deposits $9.6b. **MODEL RESULT:** Base Q3 adds an assumed September and produces 925m options contracts, $42.6b crypto volume, and $14.4b deposits. Revenue of $1,432m is wholly a forecast. [August monthly release](https://investors.robinhood.com/news-releases/news-release-details/robinhood-markets-inc-reports-august-2026-operating-data); [assumptions](../data/forecast/forecast_assumptions.csv).

## Revenue mix and operating leverage

**MODEL RESULT:** Market-activity revenue is 52.3% of Base 2027 revenue; interest/balance revenue is 36.3%, disclosed Gold 4.5%, and unclassified 6.9%. The unclassified portion is not assumed recurring. Base 2027 adjusted EBITDA margin is 51.6%. [Summary](../data/forecast/scenario_summary.csv).

Base incremental GAAP operating margin is 49.0% for 2027 versus the mixed actual/forecast 2026 year and 49.2% for 2028 versus 2027. These are model results conditional on the revenue and six expense paths, not an extension of the historical 2025 conversion rate. [Summary](../data/forecast/scenario_summary.csv); [Phase 3 leverage analysis](../data/analysis/operating_leverage_quarterly.csv).

The modeled 2026 Adjusted Operating Expenses and SBC comparison is $2.73b, **within the disclosed range** of $2.675–$2.775b. This is a comparable **non-GAAP expense check**, not a forecast of company GAAP guidance. It excludes modeled credit provision and assumes no additional significant exclusions. [Q2 release](https://investors.robinhood.com/news-releases/news-release-details/robinhood-reports-second-quarter-2026-results); [model](../data/forecast/forecast_quarterly.csv).

## Upside and Downside

**MODEL RESULT:** 2027 revenue spans $4.41b to $6.74b, with operating margin from 28.4% to 48.8%. The 2028 range is $4.53b to $7.55b, with operating margin from 28.1% to 49.0%. These cases combine coherent operating inputs; they are not probabilities. [Summary](../data/forecast/scenario_summary.csv).

## Key sensitivities and Phase 5 implications

**MODEL RESULT — largest defined revenue shocks:**

- **realized_yields (+100bp):** $899m change in 2027 revenue.
- **transaction_monetization (+20%):** $613m change in 2027 revenue.
- **options_activity (+20%):** $274m change in 2027 revenue.

**MODEL RESULT — largest defined operating-profit shocks:**

- **realized_yields (+100bp):** $899m change in 2027 operating income.
- **transaction_monetization (-20%):** -$613m change in 2027 operating income.
- **options_activity (-20%):** -$264m change in 2027 operating income.

The top-three list includes the broad **all-component realized-yield** stress, which changes Cash Sweep and credit-card net yield and must not be read as policy-rate exposure. A -100 bp **external policy-rate** shock with the model's company-specific pass-through changes 2027 revenue by -$265m, versus $449m for a direct +50 bp all-component yield stress. The [Phase 5 audit](INTEREST_SENSITIVITY_AUDIT.md) reconciles the scopes.

**INTERPRETATION:** The least stable historical relationship is blended crypto volume-to-revenue monetization across Bitstamp and WonderFi. Interest yield/pass-through has the greatest modeled **dollar** uncertainty, while its company-specific pass-through is only partly observed. Event contracts have the shortest matched unit/revenue history. Base net customer additions (0.3m) and deposits ($17.7b) match recent comparable medians; sustained options activity (26.1 contracts/customer) is modestly above the 2025 Q4–2026 Q2 median, while Q3's July/August pace is stronger still. See [risk register](FORECAST_RISKS.md) and [sensitivity results](../data/forecast/sensitivity_results.csv). These observations do not select a management strategy.
