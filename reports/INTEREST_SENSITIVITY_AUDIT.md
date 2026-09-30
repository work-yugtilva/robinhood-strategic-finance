# Interest sensitivity audit

**Verdict:** The Phase 4 +100 bp **uniform realized-yield** stress is arithmetically correct at $899m, but it is too broad to describe as a policy-rate shock. It applies to Cash Sweep and net credit-card yield as well as margin and cash/deposits. The executive rate-risk case now uses explicit policy pass-through and excludes Cash Sweep. [Q2 2026 10-Q, interest table and Item 3](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000114/hood-20260630.htm).

| 2027 modeled average balance | +100 bp gross yield effect | Treatment |
|---|---:|---|
| Margin book | $223m | Modeled average balance; 85% assumed policy pass-through |
| Cash/deposits | $252m | Reported category is net of customer sharing; 30% assumed pass-through |
| Cash Sweep | $401m | Off balance sheet net spread; **zero policy pass-through** |
| Credit card, net | $24m | Net card economics; zero assumed policy pass-through |
| **Uniform stress** | **$899m** | Hypothetical change to all four realized yields |

**Exact bridge:** For each 2027 quarter, `average balance × 0.01 × 1/4`; sum the four quarters. The four effects total $898.9m. The same revenue change flows dollar-for-dollar to GAAP operating income because this isolated stress does not change modeled expense. Securities lending, facility interest expense and other net-interest items sit in an explicit remainder and receive no shock. No rate effect is added elsewhere in the income statement; the debt-interest EBITDA addback does not add revenue.

**Policy case:** A +100 bp policy-rate shock passes through at 85% to modeled margin yield, 30% to net cash/deposit yield, and 0% to sweep/card yields. This produces $265m in 2027 revenue and operating income before tax. The 2027 average modeled balances are future assumptions, not June 2026 reported stocks. A -50 bp policy shock is -$132m in the Base engine.

**Company comparison:** Robinhood disclosed a $350m effect from a 100 bp rate change at **June 30, 2026 period-end** asset and liability balances over the **following 12 months**, before tax. It includes relevant off-balance-sheet Coastal Bank amounts, excludes Cash Sweep, and holds balance-sheet structure and trading fixed. Our 2027 estimate uses projected quarterly average balances and analyst pass-through rates, omits separately modeled liability repricing, and cannot isolate every company exposure. The two figures are therefore not directly comparable or targets for mechanical calibration. Customer sharing is already embedded in the reported net realized cash/deposit and sweep yields; the uniform stress assumes those net yields move one-for-one and is deliberately broader than policy exposure. [Company disclosure](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000114/hood-20260630.htm).

**Control:** The Phase 4 sensitivity output must equal the component sum to model precision. Cash Sweep policy pass-through must remain zero in every forecast assumption row.
