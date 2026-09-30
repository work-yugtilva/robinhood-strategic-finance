# Sensitivity analysis

Sensitivities rerun the Base operating model one input at a time or on compact 3×3 two-variable grids. They are **defined shocks**, not confidence intervals. The full table gives the 2027 revenue, operating income, adjusted EBITDA, operating margin where relevant, and 2029 Q2 annualized revenue response. [Results](../data/forecast/sensitivity_results.csv).

## Three largest 2027 revenue effects

- **realized_yields (+100bp):** $899m change in 2027 revenue.
- **transaction_monetization (+20%):** $613m change in 2027 revenue.
- **options_activity (+20%):** $274m change in 2027 revenue.

## Three largest 2027 operating-income effects

- **realized_yields (+100bp):** $899m change in 2027 operating income.
- **transaction_monetization (-20%):** -$613m change in 2027 operating income.
- **options_activity (-20%):** -$264m change in 2027 operating income.

The options grid crosses aggregate contracts/customer with dollars/contract. The crypto grid crosses App-plus-Bitstamp volume/customer with one blended realized bps assumption. The net-interest grid crosses modeled earning balances with company-specific realized yields. The profitability grid crosses trading activity with the explicit technology, marketing and G&A spend bases. A grid's revenue change is an engine result, never a total-revenue growth input.

The `realized_yields` shock moves all four company yields directly; `policy_rate_with_pass_through` moves the external rate using explicit **analyst-assumed** pass-through, with zero for Cash Sweep and credit card. These are distinct questions. The negative direct-yield stress is asymmetric at -100 bp because component yields are floored at zero, especially the low-yield cash-sweep component. Neither stress is a probability estimate. The [interest audit](INTEREST_SENSITIVITY_AUDIT.md) compares scope with Robinhood's disclosure.

| Qualitative impact | Drivers under the defined 2027 shocks | Reading |
|---|---|---|
| **HIGH** | Interest yields/rate transmission, transaction monetization, options activity | Largest distinct revenue and operating-income movements; policy and direct-yield shocks overlap |
| **MEDIUM** | Margin-balance intensity, event activity, technology expense (profit only), cash capture | Material to at least one output but smaller than the leading distinct shocks |
| **LOWER IN THIS TEST** | Quarterly customer additions, net deposits, credit-balance growth | Smaller 2027 effects for the stated shocks; longer-horizon importance may differ |

These are relative analyst labels for these shocks, not numerical scores or probabilities. [All modeled dollar effects](../data/forecast/sensitivity_results.csv) remain visible.

**Interpretation:** Shock sizes are not equally likely, and securities lending, tax, acquisition effects and event-contract take rates are incompletely observed. Absolute dollar sensitivity ranks depend on the defined shock size; the tables show the exact conditions.
