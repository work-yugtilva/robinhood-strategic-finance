# Interview guide

**Walk me through the project.** I reconciled 14 quarters of public financials, normalized operating metrics, built a 12-quarter product-and-balance driver forecast, audited rate and margin sensitivity, and compared three financial growth paths. The Base result is $5.87b revenue and 43.5% operating margin in 2027.

**Why Robinhood?** Its product breadth, customer assets, trading activity, and net interest economics create a clear finance question: which parts of scale actually convert to profit?

**What did you discover?** Measured 2024 transaction growth was primarily activity-led. Balance growth offset yield pressure in the matched interest disclosure. Gold was only about 4% of 2025 revenue, so it cannot yet carry a recurring-revenue story alone.

**What drives revenue?** Options contracts times revenue/contract; crypto and equities notional times realized bps; event units times revenue/unit; earning balances times net yields; and Gold subscribers times revenue/subscriber. Funded customers normalize aggregate activity but are not product active users.

**Hardest modeling problem?** Bitstamp and WonderFi changed crypto scope, while channel revenue was not disclosed. I kept App/Bitstamp volume separate but used an explicitly blended, post-acquisition take rate with wide sensitivities.

**Why forecast this way?** Each revenue stream has observable volume or balance and monetization inputs. That makes scenario changes explainable and permits exact bridges instead of a single revenue growth plug.

**Why is 2027 margin reasonable?** It is conditional, not assured: $5,866m revenue less $3,313m six-category expense equals $2,553m. Expense grows less than revenue, but 2027 incremental conversion is 49.0%, below historical 2025's 68.3%.

**What if rates fall?** A modeled 100 bp policy-rate decline cuts 2027 revenue and operating income by about $265m. This differs from the $899m all-yield stress and Robinhood's $350m static June 2026 disclosure. Cash Sweep is excluded from the policy test.

**What if trading activity drops?** A 20% options-activity shock reduces 2027 operating income by about $264m. Brokerage cost flexes only partly, so the earnings impact is large.

**How did you deal with acquisitions?** I flagged TradePMR, Bitstamp, WonderFi and the cash-sweep and Trump Account definition changes; I did not call acquired assets or customers organic. Crypto pricing uses a post-acquisition blended assumption.

**How did you handle unavailable data?** Product-active users, product margins, retention, and internal budgets remain unavailable. I used aggregate funded-customer activity proxies and explicit cost assumptions, with nulls for missing history.

**What internal data would change the work?** Cohort balance and product adoption, channel revenue, net spread contracts, credit loss vintages, and staffing commitments would replace the largest proxies.

**Recommendation?** Protect trading monetization, deepen earning-balance conversion, and gate spending to realized conversion. Re-underwrite the tradeoffs with internal unit economics before committing capital. [Management memo](MANAGEMENT_MEMO.md).

## Difficult technical questions

1. **Why is $899m not the policy-rate exposure?** It applies 100 bp to all four realized yields, including $401m from Cash Sweep. Company disclosure excludes sweep from short-term rate risk.
2. **How do you avoid double-counting net interest?** Four balance/yield terms sum to asset interest, then add the explicit remainder; policy and direct-yield shocks are separate reruns, never stacked.
3. **How are bridges exact?** Ordered customer, activity, and monetization effects are calculated for matched products; the disclosed residual is the difference to total reported/model revenue change.
4. **What is the stock/flow rule?** Deposits and revenue sum by period; funded customers and assets use period-end levels; interest uses quarterly average earning balances.
5. **Why can a customer-additions threshold be unavailable?** Under the modeled marketing response, more 2027 additions lower near-term operating income after the crypto shock. This flags expense-proxy risk, not negative lifetime customer value.

## Difficult strategic-finance questions

1. **Why prioritize trading if it is volatile?** It is a large measured profit sensitivity. The priority is monitoring engagement and unit monetization, with conservative budgets around activity swings.
2. **Can Gold replace transaction revenue?** Not at its disclosed historical scale; roughly 4% of 2025 revenue. Its role is relationship depth and incremental recurring revenue.
3. **Should Robinhood buy growth with marketing?** Public data do not reveal CAC, cohorts or payback. The model can set spend gates but cannot calculate initiative ROI.
4. **Is asset growth sufficient?** No. Assets include market value and acquisitions; only balances that earn a net spread or drive activity have a demonstrated revenue mechanism.
5. **What would change your recommendation?** Internal cohort data showing strong long-term cross-product value from additions, or different net spread and credit economics, could move capital toward customer scale.
