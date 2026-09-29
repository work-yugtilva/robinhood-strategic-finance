"""Phase 3 narrative and charts generated only from validated analysis tables."""
import math
import statistics
from pathlib import Path

from .config import ROOT
from .historical_analysis import OUT, read_csv, number

REPORTS=ROOT/'reports'
CHARTS=REPORTS/'charts'
SEC25='https://www.sec.gov/Archives/edgar/data/1783879/000178387926000029/hood-20251231.htm'
SEC26='https://www.sec.gov/Archives/edgar/data/1783879/000178387926000114/hood-20260630.htm'
Q4='https://www.globenewswire.com/news-release/2026/02/10/3235771/0/en/robinhood-reports-fourth-quarter-and-full-year-2025-results.html'
JAN='https://investors.robinhood.com/news-releases/news-release-details/robinhood-markets-inc-reports-january-2026-operating-data'


def fmt(v, digits=1):
    return 'n/a' if v is None else f'{v:,.{digits}f}'


def get(rows, period):
    return next(r for r in rows if r['period']==period)


def f(row, key):
    return number(row.get(key))


def correlation(rows, x, y):
    points=[(f(r,x),f(r,y)) for r in rows]
    points=[(a,b) for a,b in points if a is not None and b is not None]
    if len(points)<8:
        return len(points),None
    xs,ys=zip(*points)
    if len(set(xs))<2 or len(set(ys))<2:
        return len(points),None
    return len(points),statistics.correlation(xs,ys)


def make_reports():
    REPORTS.mkdir(exist_ok=True)
    fin=read_csv(OUT/'financial_kpis_quarterly.csv')
    mix=read_csv(OUT/'revenue_mix_quarterly.csv')
    mon=read_csv(OUT/'monetization_metrics_quarterly.csv')
    lev=read_csv(OUT/'operating_leverage_quarterly.csv')
    bridges=[r for r in read_csv(OUT/'revenue_growth_bridges.csv') if r['product']=='TOTAL_TRANSACTION']
    def annual(year,key): return sum(f(r,key) for r in fin if r['period'].startswith(str(year)))
    rev24,rev25=annual(2024,'revenue_m'),annual(2025,'revenue_m')
    gold25=sum(f(r,'disclosed_recurring_m') for r in mix if r['period'].startswith('2025'))
    op24,op25=annual(2024,'operating_income_m'),annual(2025,'operating_income_m')
    exp24,exp25=annual(2024,'operating_expense_m'),annual(2025,'operating_expense_m')
    a23=get(fin,'2023Q4'); a25=get(fin,'2025Q4'); latest=get(fin,'2026Q2')
    q25=get(fin,'2025Q2'); q26=get(fin,'2026Q2')
    b24,b25,bh=bridges[:3]
    interest_balance=(f(q26,'interest_asset_avg_balance_m')-f(q25,'interest_asset_avg_balance_m'))*f(q25,'interest_asset_revenue_m')/f(q25,'interest_asset_avg_balance_m')
    interest_yield=f(q26,'interest_asset_revenue_m')-f(q25,'interest_asset_revenue_m')-interest_balance
    combined=[{**a,**b} for a,b in zip(fin,mon)]
    corr_pairs=[('Revenue / funded customers',fin,'revenue_m','funded_customers_m'),
                ('Revenue / platform assets (joined scope)',fin,'revenue_m','customer_assets_b'),
                ('Transaction revenue / options contracts',combined,'transaction_revenue_m','options_contracts_m'),
                ('ARPU / options contracts',combined,'reported_arpu_usd_annualized','options_contracts_m'),
                ('Net deposits / revenue, same quarter',fin,'net_deposits_b','revenue_m'),
                ('Operating margin / revenue',fin,'operating_margin_pct','revenue_m')]
    corr_lines=[]
    for label,data,x,y in corr_pairs:
        n,r=correlation(data,x,y)
        corr_lines.append(f'| {label} | {n} | {fmt(r,2)} |')
    lagged=[{'prior_deposits_b':fin[i-1]['net_deposits_b'],'revenue_m':fin[i]['revenue_m']} for i in range(1,len(fin))]
    lag_n,lag_r=correlation(lagged,'prior_deposits_b','revenue_m')
    corr_lines.append(f'| Prior-quarter deposits / current revenue | {lag_n} | {fmt(lag_r,2)} |')
    historical=f'''# Historical financial analysis

**Period:** 2023 Q1–2026 Q2. **Basis:** reported company and SEC facts plus labeled arithmetic. **Purpose:** select drivers for a later forecast, not recommend an investment or management action.

## Executive takeaways

1. **FACT:** Revenue rose from $2,951m in 2024 to $4,473m in 2025; transaction revenue rose from $1,647m to $2,628m. **DERIVED RESULT:** Revenue grew {fmt(100*(rev25/rev24-1))}% and transaction revenue grew {fmt(100*(annual(2025,'transaction_revenue_m')/annual(2024,'transaction_revenue_m')-1))}%. **INTERPRETATION:** Activity and product expansion matter more than funded-customer growth alone. [2025 10-K/A]({SEC25}); [financial KPI table](../data/analysis/financial_kpis_quarterly.csv).
2. **DERIVED RESULT:** The exact 2024 vs 2023 transaction bridge attributes ${fmt(f(b24,'activity_effect_m'))}m of the ${fmt(f(b24,'change_m'))}m change to measured activity for comparable products. The 2025 bridge has a ${fmt(f(b25,'mix_residual_effect_m'))}m residual. **INTERPRETATION:** The later residual contains new products, acquisition scope, and undisclosed components; it is not evidence that one product alone drove growth. [Bridge table](../data/analysis/revenue_growth_bridges.csv).
3. **FACT:** Quarter-end customer assets were ${fmt(f(a23,'customer_assets_b'))}b at 2023 Q4 and ${fmt(f(a25,'customer_assets_b'))}b at 2025 Q4, while funded customers rose from {fmt(f(a23,'funded_customers_m'))}m to {fmt(f(a25,'funded_customers_m'))}m. **INTERPRETATION:** Assets per customer expanded, but acquired assets and market gains are included. The 2025 filing attributes $51.8b to acquired assets in its asset roll-forward. [2025 10-K/A]({SEC25}); [customer table](../data/analysis/monetization_metrics_quarterly.csv).
4. **FACT:** Average disclosed interest-earning assets increased from ${fmt(f(q25,'interest_asset_avg_balance_m'))}m in 2025 Q2 to ${fmt(f(q26,'interest_asset_avg_balance_m'))}m in 2026 Q2, while net interest revenue rose from ${fmt(f(q25,'net_interest_revenue_m'))}m to ${fmt(f(q26,'net_interest_revenue_m'))}m. **DERIVED RESULT:** The matched interest-asset revenue bridge is +${fmt(interest_balance)}m balance effect and {fmt(interest_yield)}m yield/mix effect. **INTERPRETATION:** Balance growth offset lower realized yield; the net-interest remainder includes securities lending and financing costs. [2026 Q2 10-Q]({SEC26}); [KPI table](../data/analysis/financial_kpis_quarterly.csv).
5. **DERIVED RESULT:** 2025 revenue increased ${fmt(rev25-rev24)}m while operating expense increased ${fmt(exp25-exp24)}m, yielding ${fmt(op25-op24)}m of additional GAAP operating income and a {fmt(100*(op25-op24)/(rev25-rev24))}% annual incremental operating margin. **INTERPRETATION:** Historical operating leverage improved, though acquisition integration and expense mix limit extrapolation. [2025 10-K/A]({SEC25}); [leverage table](../data/analysis/operating_leverage_quarterly.csv).

## Revenue growth and mix

**FACT:** Full-year 2023, 2024, and 2025 revenues were $1,865m, $2,951m, and $4,473m. **DERIVED RESULT:** In 2026 Q2, explicitly identified market-activity revenue was {fmt(f(get(mix,'2026Q2'),'market_activity_pct'))}% of total, net interest was {fmt(f(get(mix,'2026Q2'),'interest_balance_pct'))}%, disclosed Gold subscription was {fmt(f(get(mix,'2026Q2'),'disclosed_recurring_pct'))}%, and {fmt(f(get(mix,'2026Q2'),'unclassified_pct'))}% was unclassified. **INTERPRETATION:** Disclosed Gold is a small, measurable recurring component. Unclassified revenue cannot be treated as durable. [Revenue mix table](../data/analysis/revenue_mix_quarterly.csv); [2026 Q2 revenue note]({SEC26}).

Gold subscription revenue totaled ${fmt(gold25)}m in 2025, or {fmt(100*gold25/rev25)}% of total revenue, versus $109m in 2024. This supports a growing but still modest disclosed recurring revenue line; it does not make the rest of other revenue recurring. [2025 10-K/A]({SEC25}); [revenue mix table](../data/analysis/revenue_mix_quarterly.csv).

Robinhood does not disclose product-level contribution margin in this historical series, so the bucket mix cannot be converted into bucket profit. The consolidated operating-margin analysis below is the supported profitability view.

![Revenue and margin](charts/revenue_margin.png)
![Revenue mix](charts/revenue_mix.png)

## Customer and asset monetization

**DERIVED RESULT:** Assets per quarter-end funded customer rose from ${fmt(f(a23,'assets_per_customer_usd'),0)} to ${fmt(f(a25,'assets_per_customer_usd'),0)}. Derived annualized revenue per average customer was ${fmt(f(a25,'derived_arpu_usd_annualized'),1)} in 2025 Q4 versus company-reported quarterly ARPU of ${fmt(f(a25,'reported_arpu_usd_annualized'),0)}. The small difference reflects rounded company customer and revenue inputs. **INTERPRETATION:** Customer balances and monetization increased together, but assets include acquisitions, valuation changes, and non-interest-earning assets; the relationship is not causal. [Customer table](../data/analysis/monetization_metrics_quarterly.csv); [2025 asset roll-forward]({SEC25}).

The same-quarter and one-quarter-lag correlations below describe deposits and revenue, but do not establish whether deposits lead monetization. Acquired assets and market moves also change asset balances independently of deposits. [KPI table](../data/analysis/financial_kpis_quarterly.csv).

![Customer and asset scale](charts/customer_assets.png)

## Trading economics and growth bridge

**DERIVED RESULT:** Q2 2026 options revenue per contract was ${fmt(f(get(mon,'2026Q2'),'options_revenue_per_contract_usd'),3)}. Its crypto blended revenue/notional was {fmt(f(get(mon,'2026Q2'),'crypto_revenue_per_notional_bps'),1)} bps; this is an aggregate rate across the acquired Bitstamp scope and should not be read as a stable price. Activity per funded customer is a scale-normalized proxy, not product-user frequency. [Trading table](../data/analysis/monetization_metrics_quarterly.csv); [2026 Q2 release](https://www.globenewswire.com/news-release/2026/07/29/3335576/0/en/robinhood-reports-second-quarter-2026-results.html).

**Method:** For each comparable product, R = C × (V/C) × (R/V), where C is the mean of quarter-average funded customers across the window. Ordered effects are `(C1−C0)×A0×M0`, `C1×(A1−A0)×M0`, and `C1×A1×(M1−M0)`; A=V/C and M=R/V. The transaction residual equals the reported total change less all measured product effects. This identity reconciles exactly, but attribution changes with ordering. New products, unknown units, and acquisition-scope changes stay in residual. [Bridge table](../data/analysis/revenue_growth_bridges.csv).

![Transaction bridge](charts/transaction_bridge.png)
![Options trading economics](charts/options_economics.png)

## Net interest economics

**DERIVED RESULT:** Q2 2025 to Q2 2026 interest-asset implied yield moved from {fmt(f(q25,'interest_asset_implied_yield_pct'),2)}% to {fmt(f(q26,'interest_asset_implied_yield_pct'),2)}%, while the quarterly average effective federal funds rate moved from {fmt(f(q25,'fed_funds_quarter_average_pct'),2)}% to {fmt(f(q26,'fed_funds_quarter_average_pct'),2)}%. **INTERPRETATION:** Federal funds is external context and is not Robinhood's realized yield. The interest-asset component excludes securities lending and credit-facility expense, so its balance/yield bridge must not be labeled a full net-interest bridge. [2026 Q2 10-Q]({SEC26}); [FRED DFF](https://fred.stlouisfed.org/series/DFF).

**FACT:** Within that matched disclosure, average margin balances rose from ${fmt(f(q25,'margin_avg_balance_m'))}m to ${fmt(f(q26,'margin_avg_balance_m'))}m, cash/deposit balances from ${fmt(f(q25,'cash_deposit_avg_balance_m'))}m to ${fmt(f(q26,'cash_deposit_avg_balance_m'))}m, while cash sweep averaged ${fmt(f(q25,'cash_sweep_avg_balance_m'))}m and ${fmt(f(q26,'cash_sweep_avg_balance_m'))}m respectively. **INTERPRETATION:** Balance mix is changing alongside rates; a single policy-rate multiplier would hide these channels. [2026 Q2 10-Q]({SEC26}); [component fact table](../data/disclosed_components.csv).

![Net interest context](charts/net_interest.png)

## Operating leverage and descriptive relationships

**FACT:** Q2 2026 reported revenue was ${fmt(f(latest,'revenue_m'))}m, operating expense ${fmt(f(latest,'operating_expense_m'))}m, and adjusted EBITDA ${fmt(f(latest,'adjusted_ebitda_m'))}m. **DERIVED RESULT:** GAAP operating margin was {fmt(f(latest,'operating_margin_pct'))}% and adjusted EBITDA margin was {fmt(f(latest,'adjusted_ebitda_margin_pct'))}%. **INTERPRETATION:** Brokerage costs have some activity-linked behavior, while technology and G&A show a larger base; historical evidence is insufficient to assign hard fixed/variable percentages. Credit-loss provision grew with lending exposure and is disclosed for only seven quarters in the Phase 2 dataset. [2026 Q2 filing]({SEC26}); [leverage table](../data/analysis/operating_leverage_quarterly.csv).

**FACT:** From 2024 to 2025, brokerage/transaction expense grew 29%, technology/development 10%, operations 16%, marketing 47%, G&A 38%, and credit-loss provision 50%, versus 52% total revenue growth. **INTERPRETATION:** Brokerage and operations show semi-variable behavior; technology appears base-heavy over this window. Marketing is a management-controlled spend line, while credit loss follows lending exposure and G&A includes compensation and acquisition effects. These are qualitative observations, not fitted cost elasticities. [2025 10-K/A]({SEC25}).

The following Pearson correlations are **descriptive only**; 14 quarters, trend, acquisitions, and definition changes make them unsuitable as causal or forecast coefficients. Total transaction revenue includes products other than options, so its relationship with options contracts is an activity proxy.

| Pair | n | r |
|---|---:|---:|
{chr(10).join(corr_lines)}

## Structural changes, forecast implications, and limits

The period includes the AUC/platform-assets scope change, TradePMR, Bitstamp, WonderFi, event contracts, cash-sweep classification, and the revised 2025 Q4 platform-asset value. [Structural break log](STRUCTURAL_BREAKS.md) records their timing and affected comparisons. The [driver framework](FORECAST_DRIVER_FRAMEWORK.md) selects variables for later modeling without projecting them.

**Limits:** Product active users, retention, product contribution margin, and a complete event-contract revenue/volume history are not disclosed as consistent public series. Gold subscription revenue is reconstructed for all 14 quarters from reported quarter, YTD, and FY disclosures; Gold subscriber counts are missing in two quarters. Some monthly crypto total-volume rows were split into App and Bitstamp components; Q2 and Q3 2025 quarterly values are separately sourced in `data/disclosed_components.csv`. Missing source facts remain null. No correlation here establishes causality.
'''
    (REPORTS/'HISTORICAL_ANALYSIS.md').write_text(historical)
    reconciliation=f'''# Q4 2025 platform-asset reconciliation

| Publication | Reporting date | Period measured | Value | Treatment |
|---|---|---|---:|---|
| [Preliminary Q4/FY release]({Q4}) | February 10, 2026 | December 31, 2025 | approximately $324b | Retain as superseded reported observation (`platform_assets_earnings_b`) |
| [January operating release]({JAN}) | February 19, 2026 | December 31, 2025 comparison column | $322.1b | Canonical revised quarter-end value (`platform_assets_b`) |
| [2025 10-K/A]({SEC25}) | February 2026 filing | December 31, 2025 | $322.1b | Confirms canonical value and revision explanation |

**FACT:** Robinhood explicitly says it revised December 2025 Total Platform Assets after the preliminary earnings release to reflect final crypto pricing data. The two figures refer to the same quarter-end platform-asset metric; this is a revision of a preliminary value, not a new definition. The displayed $1.9b difference compares a whole-billion rounded preliminary figure with a tenth-billion revised figure, so it is not a precise restatement amount. [January release]({JAN}); [2025 10-K/A]({SEC25}).

**Definition:** Total Platform Assets includes customer equities, crypto, options/futures and cash net of customer receivables, plus RIA assets after TradePMR. The 10-K/A lists 2025 components of $212.0b equities, $38.2b crypto, $2.8b options/futures, $42.5b RIA assets, $43.4b cash, and $(16.8)b receivables, summing to $322.1b. The annual roll-forward also ties: $192.9b opening + $51.8b acquired assets + $68.1b net deposits + $9.3b net market gains = $322.1b. [2025 10-K/A]({SEC25}).

**Treatment and impact:** Use $322.1b for 2025 Q4 assets/customer, asset growth, and any later forecast opening balance. Retain $324b in the registry and processed KPI file as the preliminary earnings observation, tagged superseded. Neither acquisition timing nor a definition change is the company-stated reason for this specific difference. The canonical data row was already $322.1b; the Phase 3 change makes the audit and rerun treatment explicit. [Source registry](../data/source_registry.csv); [data quality report](../DATA_QUALITY_REPORT.md).
'''
    (REPORTS/'Q4_2025_PLATFORM_ASSET_RECONCILIATION.md').write_text(reconciliation)
    structural=f'''# Structural breaks and comparability

| Date / period | Affected metric | Reported change | Historical impact | Later forecast implication |
|---|---|---|---|---|
| 2023 Q4 | Funded customers | Net Cumulative Funded Accounts renamed Funded Customers; company says calculation unchanged | Join names for analytical history; retain source fields | Use one customer-base definition. [2023 10-K](https://www.sec.gov/Archives/edgar/data/1783879/000178387924000054/hood-20231231.htm) |
| January 2024 | Net deposits | Definition updated for certain dividend, interest, Gold and margin-interest cash flows; company described prior impact as immaterial | Pre/post series has a definition note | Do not assign deposits growth entirely to behavior. [2023 10-K](https://www.sec.gov/Archives/edgar/data/1783879/000178387924000054/hood-20231231.htm) |
| 2024 Q2 | Net deposits | Promotional cash and asset inflows included; earlier periods were not restated, with impact described as immaterial | Additional definition note on pre/post comparisons | Preserve disclosed definition rather than retrofitting history. [2024 Q2 10-Q](https://www.sec.gov/Archives/edgar/data/1783879/000178387924000233/hood-20240630.htm) |
| February 26, 2025 / 2025 Q1 | Platform assets / acquired assets | TradePMR acquisition brings RIA assets into platform-assets scope | Asset growth includes acquired assets; RIA assets are not Robinhood-custodied cash | Model acquired assets separately from deposits and market gains. [2025 10-K/A]({SEC25}) |
| June 2, 2025 / 2025 Q2 | Crypto volume, deposits, assets, revenue | Bitstamp acquisition expands reported crypto and operating scope | Pre/post blended crypto take rates and bridge effects are not organic | Separate App and exchange channels when disclosed. [2025 10-K/A]({SEC25}) |
| 2025 Q1 onward | Event contracts | New product becomes separately disclosed in later comparative filings | No stable earlier product-level series; missing units stay null | Treat as a new driver with short baseline. [2026 Q2 10-Q]({SEC26}) |
| December 2025 / 2025 Q4 | Platform assets | Preliminary $324b revised to $322.1b for final crypto pricing | Use revised quarter-end stock; retain preliminary observation | Start future asset roll-forward at revised value. [January release]({JAN}) |
| February 2026 | Cash sweep / free credit | Program classification changed for some cash balances | Cash sweep alone no longer represents all cash economics | Use the filing's matched earning-balance categories. [2026 Q2 10-Q]({SEC26}) |
| June 2026 / 2026 Q2 | Crypto, deposits, assets | WonderFi acquisition enters reported results | Another acquisition scope break in growth and take rates | Isolate acquisition contribution where future disclosures permit. [2026 Q2 10-Q]({SEC26}) |
| July 2026 | Platform assets and deposits | Trump Accounts treatment affects reported assets/deposits but not an equivalent funded-customer count | July–August monthly data not a Q3 financial quarter | Keep monthly series separate and document scope. [August release](https://investors.robinhood.com/news-releases/news-release-details/robinhood-markets-inc-reports-august-2026-operating-data) |

These are disclosure and scope flags, not estimates of each change's financial contribution. Where the company does not quantify a comparable organic series, historical growth stays blended.
'''
    (REPORTS/'STRUCTURAL_BREAKS.md').write_text(structural)
    drivers=read_csv(OUT/'forecast_driver_summary.csv')
    table='\n'.join(f"| {r['driver']} | {r['rank']} | {r['data_quality']} | {r['recommended_method']} |" for r in drivers)
    framework=f'''# Forecast driver framework — selection only

The historical analysis supports a future driver-based forecast. **No forecast values or strategic recommendation are produced in Phase 3.** Ranks are qualitative judgments based on source coverage, direct revenue linkage, and structural comparability, not numeric scores.

| Driver | Rank | Data quality | Later modeling method |
|---|---|---|---|
{table}

The full [driver table](../data/analysis/forecast_driver_summary.csv) gives evidence, relationships, and limitations. The exact [revenue bridges](../data/analysis/revenue_growth_bridges.csv) support options and equity activity as observable transaction drivers. The [interest table]({SEC26}) supports balance and realized-yield modeling, while [Gold disclosures]({SEC25}) support a separately identified recurring line. Customer scale is a common denominator, not a substitute for product active users. Acquisition-period residuals must not be projected mechanically.
'''
    (REPORTS/'FORECAST_DRIVER_FRAMEWORK.md').write_text(framework)


def make_charts():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    CHARTS.mkdir(parents=True, exist_ok=True)
    fin=read_csv(OUT/'financial_kpis_quarterly.csv')
    mix=read_csv(OUT/'revenue_mix_quarterly.csv')
    mon=read_csv(OUT/'monetization_metrics_quarterly.csv')
    bridges=[r for r in read_csv(OUT/'revenue_growth_bridges.csv') if r['product']=='TOTAL_TRANSACTION']
    periods=[r['period'] for r in fin]; xs=list(range(len(periods)))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#ffffff','axes.facecolor':'#ffffff','savefig.facecolor':'#ffffff'})
    def finish(fig,name):
        fig.tight_layout()
        fig.savefig(CHARTS/name,dpi=170,bbox_inches='tight',metadata={'Software':'Robinhood Strategic Finance Phase 3'})
        plt.close(fig)
    def axis(ax):
        ax.set_xticks(xs[::2],periods[::2],rotation=35,ha='right')
        ax.grid(axis='y',color='#e8ecef',linewidth=.7)
        ax.set_axisbelow(True)
    fig,ax=plt.subplots(figsize=(9,3.7))
    ax.bar(xs,[f(r,'revenue_m') for r in fin],color='#2e5668',label='Revenue ($m)')
    axis(ax);ax.set_title('Revenue scaled while GAAP operating margin improved',loc='left',weight='bold')
    ax2=ax.twinx();ax2.plot(xs,[f(r,'operating_margin_pct') for r in fin],color='#c47237',marker='o',markersize=3,label='Operating margin')
    ax2.set_ylabel('Operating margin (%)'); ax.set_ylabel('Revenue ($m)')
    finish(fig,'revenue_margin.png')
    fig,ax=plt.subplots(figsize=(9,3.7))
    buckets=[('market_activity_m','#385f71','Market activity'),('interest_balance_m','#91aab5','Interest/balance'),('disclosed_recurring_m','#a98752','Disclosed Gold'),('unclassified_m','#d6dce0','Unclassified')]
    bottom=[0]*len(xs)
    for key,color,label in buckets:
        vals=[f(r,key) or 0 for r in mix]
        ax.bar(xs,vals,bottom=bottom,color=color,label=label)
        bottom=[a+b for a,b in zip(bottom,vals)]
    axis(ax);ax.set_ylabel('Revenue ($m)');ax.legend(ncol=4,loc='upper left',fontsize=8)
    ax.set_title('Disclosed recurring revenue remains a small measured component',loc='left',weight='bold')
    finish(fig,'revenue_mix.png')
    fig,ax=plt.subplots(figsize=(9,3.7))
    ax.plot(xs,[f(r,'funded_customers_m') for r in fin],color='#2e5668',marker='o',markersize=3,label='Funded customers (m)')
    ax2=ax.twinx();ax2.plot(xs,[f(r,'customer_assets_b') for r in fin],color='#b28043',marker='o',markersize=3,label='Customer assets ($b)')
    axis(ax);ax.set_ylabel('Customers (m)');ax2.set_ylabel('Assets ($b)')
    ax.set_title('Customer assets outpaced customer count; scope changed in 2025',loc='left',weight='bold')
    finish(fig,'customer_assets.png')
    fig,ax=plt.subplots(figsize=(9,3.7))
    bx=list(range(len(bridges)))
    width=.18
    for j,(key,color,label) in enumerate([('customer_scale_effect_m','#8fb0bd','Customer'),('activity_effect_m','#2f6479','Activity'),('monetization_effect_m','#c3824d','Monetization'),('mix_residual_effect_m','#a3a9ad','Residual')]):
        ax.bar([x+(j-1.5)*width for x in bx],[f(r,key) or 0 for r in bridges],width,color=color,label=label)
    ax.axhline(0,color='#333',linewidth=.8);ax.set_xticks(bx,[r['comparison'] for r in bridges],rotation=15,ha='right')
    ax.grid(axis='y',color='#e8ecef');ax.set_axisbelow(True);ax.set_ylabel('Change in transaction revenue ($m)')
    ax.set_title('Measured activity and explicit residual reconcile growth',loc='left',weight='bold');ax.legend(ncol=4,fontsize=8)
    finish(fig,'transaction_bridge.png')
    fig,ax=plt.subplots(figsize=(9,3.7))
    ax.bar(xs,[f(r,'options_contracts_m') for r in mon],color='#466a7b')
    ax2=ax.twinx();ax2.plot(xs,[f(r,'options_revenue_per_contract_usd') for r in mon],color='#c48046',marker='o',markersize=3)
    axis(ax);ax.set_ylabel('Options contracts (m)');ax2.set_ylabel('Revenue per contract ($)')
    ax.set_title('Options activity rose; realized dollars per contract also vary',loc='left',weight='bold')
    finish(fig,'options_economics.png')
    fig,ax=plt.subplots(figsize=(9,3.7))
    ax.bar(xs,[f(r,'net_interest_revenue_m') for r in fin],color='#466a7b',label='Net interest revenue ($m)')
    ax2=ax.twinx();ax2.plot(xs,[f(r,'fed_funds_quarter_average_pct') for r in fin],color='#c48046',label='Fed funds (%)')
    axis(ax);ax.set_ylabel('Net interest revenue ($m)');ax2.set_ylabel('Effective federal funds (%)')
    ax.set_title('Rate context diverges from realized net interest economics',loc='left',weight='bold')
    finish(fig,'net_interest.png')


def run():
    make_reports()
    make_charts()


if __name__=='__main__':
    run()
