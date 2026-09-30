"""Deterministic Phase 4 CSVs, reports, notebooks and decision-useful charts."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .config import ROOT
from .forecast_analysis import largest_shocks, pseudo_historical
from .forecast_model import ASSUMPTION_FIELDS, PERIODS, SCENARIOS, Q2, Q2_RELEASE, JULY, AUGUST, FED

OUT = ROOT / 'data/forecast'
REPORTS = ROOT / 'reports'
CHARTS = REPORTS / 'forecast_charts'


def format_value(value):
    if value is None:
        return ''
    if isinstance(value, bool):
        return str(value).upper()
    if isinstance(value, float):
        return f'{value:.8f}'.rstrip('0').rstrip('.') if value else '0'
    return value


def write_csv(name, rows, fields=None):
    OUT.mkdir(parents=True, exist_ok=True)
    fields=fields or list(rows[0])
    with (OUT/name).open('w', newline='') as handle:
        writer=csv.DictWriter(handle,fields,extrasaction='ignore',lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({key:format_value(row.get(key)) for key in fields})


def output_fields(rows):
    prefix=['period','scenario','status','nowcast']
    return prefix+sorted({key for row in rows for key in row if key not in prefix})


def write_all(assumptions, actual, forecasts, summaries, sensitivities, bridges):
    write_csv('forecast_assumptions.csv',assumptions,ASSUMPTION_FIELDS)
    write_csv('forecast_quarterly.csv',actual+[r for sc in SCENARIOS for r in forecasts[sc]],
              output_fields(actual+[r for sc in SCENARIOS for r in forecasts[sc]]))
    write_csv('scenario_summary.csv',summaries)
    write_csv('sensitivity_results.csv',sensitivities)
    write_csv('forecast_bridges.csv',bridges)
    write_reports(assumptions,actual,forecasts,summaries,sensitivities,bridges)
    write_notebooks()
    write_charts(actual,forecasts,sensitivities)


def srow(rows,scenario,window):
    return next(r for r in rows if r['scenario']==scenario and r['window']==window)


def b(value):
    return f'${value/1000:,.2f}b'


def m(value):
    return f'-${abs(value):,.0f}m' if value<0 else f'${value:,.0f}m'


def write_reports(assumptions,actual,forecasts,summaries,sensitivities,bridges):
    REPORTS.mkdir(parents=True,exist_ok=True)
    base27=srow(summaries,'Base','2027'); base28=srow(summaries,'Base','2028')
    base26=srow(summaries,'Base','2026')
    up27=srow(summaries,'Upside','2027'); down27=srow(summaries,'Downside','2027')
    up28=srow(summaries,'Upside','2028'); down28=srow(summaries,'Downside','2028')
    end=forecasts['Base'][-1]
    q3=forecasts['Base'][0]
    revenue_top=largest_shocks(sensitivities,'2027_revenue_m')
    profit_top=largest_shocks(sensitivities,'2027_operating_income_m')
    revenue_lines='\n'.join(f"- **{r['driver']} ({r['shock']}):** {m(r['delta_m'])} change in 2027 revenue." for r in revenue_top)
    profit_lines='\n'.join(f"- **{r['driver']} ({r['shock']}):** {m(r['delta_m'])} change in 2027 operating income." for r in profit_top)
    h2_adj=sum(r['adjusted_opex_and_sbc_m'] for r in forecasts['Base'][:2])
    h1_adj=(actual[-2]['operating_expense_m']-actual[-2]['credit_loss_expense_m']+
            actual[-1]['operating_expense_m']-actual[-1]['credit_loss_expense_m']-23)
    full_adj=h1_adj+h2_adj
    guidance_gap=(full_adj-2675 if full_adj<2675 else full_adj-2775 if full_adj>2775 else 0)
    guide_position='within the disclosed range' if guidance_gap==0 else f'{m(abs(guidance_gap))} outside the disclosed range'
    inputs={(r['period'],r['driver']):float(r['value']) for r in assumptions if r['scenario']=='Base' and r['classification']=='ASSUMPTION'}
    opts=inputs[('2026Q4','options_per_customer')]
    opt_price=inputs[('2026Q4','option_revenue_per_contract_usd')]
    crypto_bps=inputs[('2026Q4','crypto_blended_bps')]
    equity_activity=inputs[('2026Q4','equity_notional_per_customer_b')]
    normal_adds=inputs[('2026Q4','net_customer_additions_m')]
    normal_deposits=inputs[('2026Q4','net_deposits_b')]
    interest_shock=next(r for r in sensitivities if r['kind']=='ONE_WAY' and r['driver']=='realized_yields' and r['shock']=='+50bp' and r['metric']=='2027_revenue_m')
    policy_shock=next(r for r in sensitivities if r['kind']=='ONE_WAY' and r['driver']=='policy_rate_with_pass_through' and r['shock']=='-100bp' and r['metric']=='2027_revenue_m')
    diagnostic=pseudo_historical(actual)
    diagnostic_rows='\n'.join(f"| {r['product'].title()} | {m(r['projected_revenue_m'])} | {m(r['actual_revenue_m'])} | {m(r['error_m'])} |" for r in diagnostic)
    incremental_2027=100*(base27['operating_income_m']-base26['operating_income_m'])/(base27['revenue_m']-base26['revenue_m'])
    incremental_2028=100*(base28['operating_income_m']-base27['operating_income_m'])/(base28['revenue_m']-base27['revenue_m'])
    method=f'''# Forecast method — Phase 4

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

The [Q2 2026 filing]({Q2}) supplies the interest component and revenue baselines. The [Q2 earnings release]({Q2_RELEASE}) defines adjusted EBITDA and gives a **$2.675–$2.775b** 2026 Adjusted Operating Expenses and SBC range, excluding credit losses and specified items. The model uses this only as a check. [July]({JULY}) and [August]({AUGUST}) monthly metrics supply Q3 partial observations. The [September FOMC projections]({FED}) are external policy context, not company yield guidance.

**Base calibration:** Net additions 0.3m per normal quarter (median 2025 Q3–2026 Q1); deposits $17.7b (median 2025 Q4–2026 Q2); options/equity activity from the median of 2025 Q4–2026 Q2 and the Q3 partial pace; post-Bitstamp crypto bps from 2025 Q4–2026 Q2; event dollars/contract from 2026 Q1–Q2; neutral asset-value change. Upside and Downside change these operating drivers coherently, with persistent cost commitments in the Downside. Every numerical scenario input, including scenario multipliers and the H2 2026 expense investment step, is in `data/forecast/forecast_assumptions.csv`.

| Major Base driver | Historical evidence | Base input and reason |
|---|---|---|
| Net funded-customer additions | 0.2–0.4m in 2025 Q3–2026 Q1, excluding 2026 Q2 acquisition-era step | {normal_adds:.2f}m/quarter; comparable median |
| Net deposits | $15.9–$21.7b in 2025 Q4–2026 Q2 | ${normal_deposits:.1f}b/quarter; recent median |
| Options contracts/customer | 21.6–27.7 quarterly in 2025 Q4–2026 Q2; Q3 partial pace higher | {opts:.1f}; median including Q3 partial pace |
| Options dollars/contract | $0.442–$0.476 in the same three quarters | ${opt_price:.3f}; recent median |
| Equities notional/customer | $23.5–$34.3b per million average funded customers, same three quarters | ${equity_activity:.1f}b per million; median including Q3 partial pace |
| Blended crypto bps | 20.4–26.9 bps in 2025 Q4–2026 Q2 | {crypto_bps:.1f} bps; post-Bitstamp median, with WonderFi uncertainty |
| Interest-asset realized yields | Q2 2026 margin 4.52%, cash/deposit 2.02%, sweep 0.59%, credit 11.88% | Each starts from its company-specific yield; assumed policy pass-through is zero for Cash Sweep and credit card |
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
{diagnostic_rows}

This diagnostic shows why constant activity and monetization cannot be treated as a reliable forecast law, especially for crypto.
'''
    (REPORTS/'FORECAST_METHOD.md').write_text(method)
    results=f'''# Forecast results — operating conditions, not a recommendation

## Executive forecast summary

**MODEL RESULT:** Base revenue is approximately {b(base27['revenue_m'])} in 2027 at a {base27['operating_margin_pct']:.1f}% GAAP operating margin, and {b(base28['revenue_m'])} in 2028 at a {base28['operating_margin_pct']:.1f}% margin. These are scenario outputs rather than company guidance. The 2026 total of {b(base26['revenue_m'])} combines **two reported quarters and two forecast quarters**. [Quarterly model](../data/forecast/forecast_quarterly.csv); [summary](../data/forecast/scenario_summary.csv).

## Base Case and revenue drivers

**FACT:** Q2 2026 reported 28.4m funded customers, $1,308m revenue, and $734m operating expense. **MODEL RESULT:** By 2029 Q2, Base reaches {end['funded_customers_m']:.1f}m customers, {b(end['revenue_m']*4)} annualized revenue, and a {end['operating_margin_pct']:.1f}% modeled operating margin. The model holds aggregate activity per funded customer near the recent post-acquisition calibration instead of requiring perpetual activity acceleration. [Q2 release]({Q2_RELEASE}); [assumptions](../data/forecast/forecast_assumptions.csv).

## Q3 nowcast

**FACT:** July/August options contracts totaled 616.7m, crypto volume $28.4b, and net deposits $9.6b. **MODEL RESULT:** Base Q3 adds an assumed September and produces {q3['options_contracts_m']:.0f}m options contracts, ${q3['crypto_notional_b']:.1f}b crypto volume, and ${q3['net_deposits_b']:.1f}b deposits. Revenue of {m(q3['revenue_m'])} is wholly a forecast. [August monthly release]({AUGUST}); [assumptions](../data/forecast/forecast_assumptions.csv).

## Revenue mix and operating leverage

**MODEL RESULT:** Market-activity revenue is {base27['market_activity_pct']:.1f}% of Base 2027 revenue; interest/balance revenue is {base27['interest_balance_pct']:.1f}%, disclosed Gold {base27['disclosed_recurring_pct']:.1f}%, and unclassified {base27['unclassified_pct']:.1f}%. The unclassified portion is not assumed recurring. Base 2027 adjusted EBITDA margin is {base27['adjusted_ebitda_margin_pct']:.1f}%. [Summary](../data/forecast/scenario_summary.csv).

Base incremental GAAP operating margin is {incremental_2027:.1f}% for 2027 versus the mixed actual/forecast 2026 year and {incremental_2028:.1f}% for 2028 versus 2027. These are model results conditional on the revenue and six expense paths, not an extension of the historical 2025 conversion rate. [Summary](../data/forecast/scenario_summary.csv); [Phase 3 leverage analysis](../data/analysis/operating_leverage_quarterly.csv).

The modeled 2026 Adjusted Operating Expenses and SBC comparison is {b(full_adj)}, **{guide_position}** of $2.675–$2.775b. This is a comparable **non-GAAP expense check**, not a forecast of company GAAP guidance. It excludes modeled credit provision and assumes no additional significant exclusions. [Q2 release]({Q2_RELEASE}); [model](../data/forecast/forecast_quarterly.csv).

## Upside and Downside

**MODEL RESULT:** 2027 revenue spans {b(down27['revenue_m'])} to {b(up27['revenue_m'])}, with operating margin from {down27['operating_margin_pct']:.1f}% to {up27['operating_margin_pct']:.1f}%. The 2028 range is {b(down28['revenue_m'])} to {b(up28['revenue_m'])}, with operating margin from {down28['operating_margin_pct']:.1f}% to {up28['operating_margin_pct']:.1f}%. These cases combine coherent operating inputs; they are not probabilities. [Summary](../data/forecast/scenario_summary.csv).

## Key sensitivities and Phase 5 implications

**MODEL RESULT — largest defined revenue shocks:**

{revenue_lines}

**MODEL RESULT — largest defined operating-profit shocks:**

{profit_lines}

The top-three list includes the broad **all-component realized-yield** stress, which changes Cash Sweep and credit-card net yield and must not be read as policy-rate exposure. A -100 bp **external policy-rate** shock with the model's company-specific pass-through changes 2027 revenue by {m(policy_shock['delta_m'])}, versus {m(interest_shock['delta_m'])} for a direct +50 bp all-component yield stress. The [Phase 5 audit](INTEREST_SENSITIVITY_AUDIT.md) reconciles the scopes.

**INTERPRETATION:** The least stable historical relationship is blended crypto volume-to-revenue monetization across Bitstamp and WonderFi. Interest yield/pass-through has the greatest modeled **dollar** uncertainty, while its company-specific pass-through is only partly observed. Event contracts have the shortest matched unit/revenue history. Base net customer additions ({normal_adds:.1f}m) and deposits (${normal_deposits:.1f}b) match recent comparable medians; sustained options activity ({opts:.1f} contracts/customer) is modestly above the 2025 Q4–2026 Q2 median, while Q3's July/August pace is stronger still. See [risk register](FORECAST_RISKS.md) and [sensitivity results](../data/forecast/sensitivity_results.csv). These observations do not select a management strategy.
'''
    (REPORTS/'FORECAST_RESULTS.md').write_text(results)
    sensitivity=f'''# Sensitivity analysis

Sensitivities rerun the Base operating model one input at a time or on compact 3×3 two-variable grids. They are **defined shocks**, not confidence intervals. The full table gives the 2027 revenue, operating income, adjusted EBITDA, operating margin where relevant, and 2029 Q2 annualized revenue response. [Results](../data/forecast/sensitivity_results.csv).

## Three largest 2027 revenue effects

{revenue_lines}

## Three largest 2027 operating-income effects

{profit_lines}

The options grid crosses aggregate contracts/customer with dollars/contract. The crypto grid crosses App-plus-Bitstamp volume/customer with one blended realized bps assumption. The net-interest grid crosses modeled earning balances with company-specific realized yields. The profitability grid crosses trading activity with the explicit technology, marketing and G&A spend bases. A grid's revenue change is an engine result, never a total-revenue growth input.

The `realized_yields` shock moves all four company yields directly; `policy_rate_with_pass_through` moves the external rate using explicit **analyst-assumed** pass-through, with zero for Cash Sweep and credit card. These are distinct questions. The negative direct-yield stress is asymmetric at -100 bp because component yields are floored at zero, especially the low-yield cash-sweep component. Neither stress is a probability estimate. The [interest audit](INTEREST_SENSITIVITY_AUDIT.md) compares scope with Robinhood's disclosure.

| Qualitative impact | Drivers under the defined 2027 shocks | Reading |
|---|---|---|
| **HIGH** | Interest yields/rate transmission, transaction monetization, options activity | Largest distinct revenue and operating-income movements; policy and direct-yield shocks overlap |
| **MEDIUM** | Margin-balance intensity, event activity, technology expense (profit only), cash capture | Material to at least one output but smaller than the leading distinct shocks |
| **LOWER IN THIS TEST** | Quarterly customer additions, net deposits, credit-balance growth | Smaller 2027 effects for the stated shocks; longer-horizon importance may differ |

These are relative analyst labels for these shocks, not numerical scores or probabilities. [All modeled dollar effects](../data/forecast/sensitivity_results.csv) remain visible.

**Interpretation:** Shock sizes are not equally likely, and securities lending, tax, acquisition effects and event-contract take rates are incompletely observed. Absolute dollar sensitivity ranks depend on the defined shock size; the tables show the exact conditions.
'''
    (REPORTS/'SENSITIVITY_ANALYSIS.md').write_text(sensitivity)
    risks=f'''# Forecast risks and bias directions

| Risk | Affected model component | Possible bias | Mitigation |
|---|---|---|---|
| Product active-user counts unavailable | Per-funded-customer trading intensity | Scale attribution can overstate user breadth | Label aggregate proxy and vary activity independently of customer adds |
| Bitstamp/WonderFi integration and undisclosed channel revenue | Crypto take rate and volume | Blended bps may misstate either channel | Post-acquisition calibration and wide volume/monetization shocks |
| Short event-contract revenue/unit history | Event revenue | Mature run-rate extrapolation can overstate durability | Hold per-customer activity near partial-quarter pace; scenario grid and explicit flag |
| Cash-sweep reclassification | Cash and sweep interest | Historical yield and balance shares may not persist | Separate balances/yields; August split; zero modeled policy-rate pass-through for Cash Sweep |
| Policy-to-company yield pass-through unobservable | Net interest revenue | Rate shocks may overstate or understate realized yield change | Disclose component pass-through and stress realized yields directly |
| Securities lending/financing remainder | Net interest revenue | Flat remainder misses activity or borrowing costs | Separate $2m Base remainder and downside stress |
| Credit exposure and provision proxy | Credit-loss expense | Provision may not scale with balances as assumed | Explicit exposure/provision inputs and downside provision rate |
| Platform assets include acquisitions, valuation and Trump Accounts | Asset roll-forward | Treating all asset gains as deposits would overstate organic inflow | Separate net deposits, observed residual, future market assumption, and zero future acquisitions |
| 2026 expense guidance is adjusted and excludes items | GAAP expense/operating margin | Direct comparison can mislead | Show excluded credit provision and a separate adjusted-expense check |
| No company product margins or retention cohorts | Expense allocation and operating leverage | Category-level cost behavior may differ from proxy | Keep six consolidated categories and avoid initiative ROI |
| Twelve-quarter horizon | Every modeled driver | Small annual input errors compound | Three operating scenarios plus one-/two-way shocks; no probability claims |

The [Phase 3 structural-break log](STRUCTURAL_BREAKS.md) documents dates and source links. Future acquisitions, unusual gains and significant exceptional charges are set to zero; they are not modeled recurring events.
'''
    (REPORTS/'FORECAST_RISKS.md').write_text(risks)


def write_notebooks():
    folder=ROOT/'notebooks'; folder.mkdir(parents=True,exist_ok=True)
    specs=[
        ('forecast_driver_model.ipynb','Driver model','forecast_quarterly.csv',
         "display(df.loc[(df.scenario == 'Base') & (df.status == 'FORECAST'), ['period','funded_customers_m','options_contracts_m','crypto_notional_b','net_interest_revenue_m','revenue_m']])"),
        ('forecast_scenarios.ipynb','Scenario comparison','scenario_summary.csv',
         "display(df.loc[df.window.isin(['2027','2028']), ['scenario','window','revenue_m','operating_margin_pct','adjusted_ebitda_margin_pct']])"),
        ('forecast_sensitivity.ipynb','Sensitivity','sensitivity_results.csv',
         "display(df.loc[(df.kind == 'ONE_WAY') & (df.metric == '2027_operating_income_m')].sort_values('delta_m'))"),
    ]
    for name,title,file,expression in specs:
        notebook={'cells':[{'cell_type':'markdown','metadata':{},'source':[f'# {title}\n','Phase 4 saved-output walkthrough. Run `python -m src.phase4` before opening.\n']},
                           {'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],
                            'source':['from pathlib import Path\n','import pandas as pd\n',
                                      f"df = pd.read_csv(Path('data/forecast/{file}'))\n",expression+'\n']}],
                  'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                              'language_info':{'name':'python'}},'nbformat':4,'nbformat_minor':5}
        (folder/name).write_text(json.dumps(notebook,indent=1,ensure_ascii=False)+'\n')


def write_charts(actual,forecasts,sensitivities):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    CHARTS.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,
                         'axes.spines.right':False,'figure.facecolor':'white','axes.facecolor':'white'})
    def save(fig,name):
        fig.tight_layout()
        fig.savefig(CHARTS/name,dpi=150,metadata={'Software':'Phase 4 strategic finance model'})
        plt.close(fig)
    quarters=[r['period'] for r in actual[-4:]]+PERIODS
    x=list(range(len(quarters)))
    fig,ax=plt.subplots(figsize=(10,4))
    for sc,color in [('Base','#245268'),('Upside','#438276'),('Downside','#bd7950')]:
        series=[r['revenue_m'] for r in actual[-4:]+forecasts[sc]]
        ax.plot(x,series,color=color,label=sc,linewidth=2)
    ax.axvline(3.5,color='#888',linestyle='--');ax.set_xticks(x[::2],quarters[::2],rotation=30)
    ax.set_ylabel('Revenue ($m)');ax.set_title('Quarterly revenue: actual through 2026 Q2, then scenarios',loc='left')
    ax.legend();ax.grid(axis='y',alpha=.2);save(fig,'revenue_scenarios.png')
    fig,ax=plt.subplots(figsize=(10,4))
    keys=[('market_activity_revenue_m','Market activity','#2b657a'),('interest_balance_revenue_m','Interest / balance','#7cabb4'),
          ('disclosed_recurring_revenue_m','Gold disclosed','#b48a50'),('unclassified_revenue_m','Unclassified','#bfc9cd')]
    bottom=[0.]*len(PERIODS)
    for key,label,color in keys:
        series=[r[key] for r in forecasts['Base']]
        ax.bar(range(len(PERIODS)),series,bottom=bottom,color=color,label=label)
        bottom=[a+b for a,b in zip(bottom,series)]
    ax.set_xticks(range(0,12,2),PERIODS[::2],rotation=30);ax.set_ylabel('Revenue ($m)')
    ax.set_title('Base mix: unclassified revenue remains visible',loc='left');ax.legend(ncol=4,fontsize=8)
    save(fig,'revenue_durability.png')
    fig,ax=plt.subplots(figsize=(10,4))
    for sc,color in [('Base','#245268'),('Upside','#438276'),('Downside','#bd7950')]:
        ax.plot(PERIODS,[r['operating_margin_pct'] for r in forecasts[sc]],color=color,label=sc,linewidth=2)
    ax.set_xticks(PERIODS[::2]);ax.tick_params(axis='x',labelrotation=30);ax.set_ylabel('GAAP operating margin (%)')
    ax.set_title('Expense commitments amplify scenario margin differences',loc='left');ax.legend();ax.grid(axis='y',alpha=.2)
    save(fig,'operating_margin_scenarios.png')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    base=forecasts['Base']
    axes[0].plot(PERIODS,[r['options_contracts_m'] for r in base],color='#245268')
    axes[0].set_title('Options volume drives revenue');axes[0].set_ylabel('Contracts (m)')
    axes[1].plot(PERIODS,[r['crypto_app_notional_b'] for r in base],label='App',color='#438276')
    axes[1].plot(PERIODS,[r['crypto_bitstamp_notional_b'] for r in base],label='Bitstamp',color='#bd7950')
    axes[1].set_title('Crypto channels share blended bps');axes[1].set_ylabel('Volume ($b)');axes[1].legend()
    for ax in axes:
        ax.set_xticks(PERIODS[::4]);ax.tick_params(axis='x',labelrotation=30);ax.grid(axis='y',alpha=.2)
    save(fig,'trading_drivers.png')
    top=largest_shocks(sensitivities,'2027_operating_income_m',8)
    fig,ax=plt.subplots(figsize=(8,4.5))
    labels=[f"{r['driver'].replace('_',' ')} ({r['shock']})" for r in reversed(top)]
    vals=[r['delta_m'] for r in reversed(top)]
    ax.barh(labels,vals,color=['#bd7950' if v<0 else '#438276' for v in vals]);ax.axvline(0,color='#333',linewidth=.8)
    ax.set_xlabel('Largest defined shock impact on 2027 operating income ($m)')
    ax.set_title('Driver importance depends on the stated shock',loc='left')
    save(fig,'operating_income_sensitivity.png')
