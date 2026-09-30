"""Build Phase 5 audits, decision package, and executive artifacts."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from .config import ROOT
from .forecast_analysis import make_sensitivities, make_summaries
from .forecast_model import SCENARIOS, actual_rows, build_assumptions, load_history, project
from .phase4 import HISTORICAL_PATHS, run as run_phase4
from .strategic_analysis import (Q2_FILING, EXPENSES, audit_interest, audit_margin,
                                 decision_paths, selected_sensitivity, strategy_thresholds)

OUT = ROOT / 'data/strategy'
REPORTS = ROOT / 'reports'
Q2_RELEASE = 'https://investors.robinhood.com/news-releases/news-release-details/robinhood-reports-second-quarter-2026-results'
FY25 = 'https://www.sec.gov/Archives/edgar/data/1783879/000178387926000029/hood-20251231.htm'


def money(value, digits=0):
    return f'-${abs(value):,.{digits}f}m' if value < 0 else f'${value:,.{digits}f}m'


def billion(value):
    return f'${value/1000:,.2f}b'


def percent(value):
    return f'{value:.1f}%'


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict,list,tuple)) else v
                             for k,v in row.items()})


def normalize_workbook_archive(path):
    """Remove random artifact-tool relationship IDs and ZIP timestamps only."""
    pattern=re.compile(rb'R[0-9a-fA-F]{16}')
    mapping={}
    with zipfile.ZipFile(path) as archive:
        members={name:archive.read(name) for name in archive.namelist()}
    for name in sorted(members):
        if name.endswith(('.xml','.rels')):
            def replace(match):
                old=match.group()
                if old not in mapping:
                    mapping[old]=f'R{len(mapping)+1:016x}'.encode()
                return mapping[old]
            members[name]=pattern.sub(replace,members[name])
    temp=path.with_suffix('.stable.xlsx')
    with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name in sorted(members):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,members[name])
    temp.replace(path)


def build_workbook():
    modules=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
    node=shutil.which('node') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
    if not modules.exists() or not Path(node).exists():
        raise RuntimeError('Bundled artifact-tool Node runtime is required to rebuild the workbook')
    with tempfile.TemporaryDirectory(prefix='robinhood-phase5-') as directory:
        temp=Path(directory)
        shutil.copyfile(ROOT/'scripts/build_workbook.mjs',temp/'build_workbook.mjs')
        (temp/'node_modules').symlink_to(modules,target_is_directory=True)
        subprocess.run([node,str(temp/'build_workbook.mjs'),str(ROOT)],check=True)
    workbook=ROOT/'models/Robinhood_Strategic_Finance_Model.xlsx'
    normalize_workbook_archive(workbook)
    sidecar=workbook.with_suffix('.xlsx.inspect.ndjson')
    if sidecar.exists():sidecar.unlink()


def facts_pack(actual, forecasts, summaries, sensitivities, interest, margin, thresholds, paths):
    summary = {(r['scenario'],r['window']): r for r in summaries}
    q2 = actual[-1]
    by_period={r['period']:r for r in actual}
    shocks = {
        'policy_rate_down_50bp_m': selected_sensitivity(sensitivities,'policy_rate_with_pass_through','-50bp'),
        'policy_rate_down_100bp_m': selected_sensitivity(sensitivities,'policy_rate_with_pass_through','-100bp'),
        'uniform_yield_up_100bp_m': selected_sensitivity(sensitivities,'realized_yields','+100bp'),
        'transaction_monetization_down_20pct_m': selected_sensitivity(sensitivities,'transaction_monetization','-20%'),
        'transaction_monetization_up_20pct_m': selected_sensitivity(sensitivities,'transaction_monetization','+20%'),
        'options_activity_down_20pct_oi_m': selected_sensitivity(sensitivities,'options_activity','-20%','2027_operating_income_m'),
        'options_activity_down_20pct_revenue_m': selected_sensitivity(sensitivities,'options_activity','-20%'),
        'options_activity_up_20pct_m': selected_sensitivity(sensitivities,'options_activity','+20%'),
        'crypto_activity_down_20pct_m': selected_sensitivity(sensitivities,'crypto_activity','-20%'),
        'customer_additions_down_25pct_m': selected_sensitivity(sensitivities,'customer_additions','-25%'),
        'technology_up_10pct_oi_m': selected_sensitivity(sensitivities,'technology','+10%','2027_operating_income_m'),
    }
    facts = {
        'information_cutoff': '2026-09-28',
        'status': 'Independent analyst model; forecast is not company guidance',
        'sources': {'q2_2026_filing':Q2_FILING,'q2_2026_release':Q2_RELEASE,'fy2025':FY25},
        'reported': {'2026Q2_revenue_m':q2['revenue_m'], '2026Q2_funded_customers_m':q2['funded_customers_m'],
                     '2026Q2_platform_assets_b':q2['platform_assets_b'],
                     '2023_revenue_m':sum(r['revenue_m'] for r in actual if r['period'].startswith('2023')),
                     '2024_revenue_m':sum(r['revenue_m'] for r in actual if r['period'].startswith('2024')),
                     '2025_revenue_m':margin[0]['revenue_m'],
                     '2023Q4_funded_customers_m':by_period['2023Q4']['funded_customers_m'],
                     '2023Q4_platform_assets_b':by_period['2023Q4']['platform_assets_b'],
                     '2025Q4_funded_customers_m':by_period['2025Q4']['funded_customers_m'],
                     '2025Q4_platform_assets_b':by_period['2025Q4']['platform_assets_b'],
                     '2026Q2_100bp_company_sensitivity_m':350},
        'derived': {'2025_incremental_operating_margin_pct':68.3,
                    '2024_activity_bridge_m':620.8,'2024_transaction_growth_m':862.0,
                    '2026Q2_mix_pct':{k:q2[k] / q2['revenue_m'] * 100 for k in
                                      ('market_activity_revenue_m','interest_balance_revenue_m',
                                       'disclosed_recurring_revenue_m','unclassified_revenue_m')}},
        'model': {'annual':{s:{y:summary[(s,y)] for y in ('2026','2027','2028')} for s in SCENARIOS},
                  'q3_nowcast':{s:forecasts[s][0] for s in SCENARIOS},
                  'interest_audit':interest,'margin_audit':margin,'shocks':shocks,
                  'thresholds':thresholds,'paths':paths},
        'recommendation': {
            'priorities': [
                'Protect trading engagement and realized monetization, especially options, while planning for activity swings.',
                'Turn deposits into earning balances and deepen Gold relationships, with net spread and credit-loss discipline.',
                'Gate technology, marketing, and general spending against realized revenue and operating-profit conversion.'
            ],
            'risks': [
                'Transaction activity and blended crypto monetization can normalize faster than the Base Case.',
                'Lower realized interest yields or faster credit and fixed-cost growth can erase operating leverage.'
            ],
            'kpis': [
                'Funded-customer net additions',
                'Net deposits and interest-earning balance capture',
                'Options contracts per funded customer and dollars per contract',
                'Blended crypto revenue per notional dollar',
                'Realized net interest yield and six-category expense/revenue ratio'
            ]
        }
    }
    return facts


def write_reports(f):
    REPORTS.mkdir(parents=True, exist_ok=True)
    m = f['model']; ia = m['interest_audit']; ma = m['margin_audit']
    b27=m['annual']['Base']['2027']; b28=m['annual']['Base']['2028']; b26=m['annual']['Base']['2026']
    u27=m['annual']['Upside']['2027']; d27=m['annual']['Downside']['2027']
    comp=ia['components_m']
    interest=f'''# Interest sensitivity audit

**Verdict:** The Phase 4 +100 bp **uniform realized-yield** stress is arithmetically correct at {money(ia['uniform_yield_100bp_m'])}, but it is too broad to describe as a policy-rate shock. It applies to Cash Sweep and net credit-card yield as well as margin and cash/deposits. The executive rate-risk case now uses explicit policy pass-through and excludes Cash Sweep. [Q2 2026 10-Q, interest table and Item 3]({Q2_FILING}).

| 2027 modeled average balance | +100 bp gross yield effect | Treatment |
|---|---:|---|
| Margin book | {money(comp['margin'])} | Modeled average balance; 85% assumed policy pass-through |
| Cash/deposits | {money(comp['cash_deposit'])} | Reported category is net of customer sharing; 30% assumed pass-through |
| Cash Sweep | {money(comp['cash_sweep'])} | Off balance sheet net spread; **zero policy pass-through** |
| Credit card, net | {money(comp['credit_card'])} | Net card economics; zero assumed policy pass-through |
| **Uniform stress** | **{money(ia['uniform_yield_100bp_m'])}** | Hypothetical change to all four realized yields |

**Exact bridge:** For each 2027 quarter, `average balance × 0.01 × 1/4`; sum the four quarters. The four effects total {money(ia['uniform_yield_100bp_m'],1)}. The same revenue change flows dollar-for-dollar to GAAP operating income because this isolated stress does not change modeled expense. Securities lending, facility interest expense and other net-interest items sit in an explicit remainder and receive no shock. No rate effect is added elsewhere in the income statement; the debt-interest EBITDA addback does not add revenue.

**Policy case:** A +100 bp policy-rate shock passes through at 85% to modeled margin yield, 30% to net cash/deposit yield, and 0% to sweep/card yields. This produces {money(ia['policy_100bp_m'])} in 2027 revenue and operating income before tax. The 2027 average modeled balances are future assumptions, not June 2026 reported stocks. A -50 bp policy shock is {money(m['shocks']['policy_rate_down_50bp_m'])} in the Base engine.

**Company comparison:** Robinhood disclosed a {money(350)} effect from a 100 bp rate change at **June 30, 2026 period-end** asset and liability balances over the **following 12 months**, before tax. It includes relevant off-balance-sheet Coastal Bank amounts, excludes Cash Sweep, and holds balance-sheet structure and trading fixed. Our 2027 estimate uses projected quarterly average balances and analyst pass-through rates, omits separately modeled liability repricing, and cannot isolate every company exposure. The two figures are therefore not directly comparable or targets for mechanical calibration. Customer sharing is already embedded in the reported net realized cash/deposit and sweep yields; the uniform stress assumes those net yields move one-for-one and is deliberately broader than policy exposure. [Company disclosure]({Q2_FILING}).

**Control:** The Phase 4 sensitivity output must equal the component sum to model precision. Cash Sweep policy pass-through must remain zero in every forecast assumption row.
'''
    (REPORTS/'INTEREST_SENSITIVITY_AUDIT.md').write_text(interest)
    def margin_line(r, prior=None):
        growth='—' if prior is None else percent(100*(r['operating_expense_m']/prior['operating_expense_m']-1))
        return f"| {r['year']} | {money(r['revenue_m'])} | {money(r['operating_expense_m'])} | {money(r['operating_income_m'])} | {percent(r['operating_margin_pct'])} | {growth} |"
    margin_rows='\n'.join(margin_line(r,ma[i-1] if i else None) for i,r in enumerate(ma))
    expense_rows='\n'.join(f"| {key.replace('_expense_m','').replace('_',' ').title()} | {money(ma[1][key])} | {money(ma[2][key])} | {percent(ma[2][f'{key}_growth_pct'])} | {money(ma[3][key])} | {percent(ma[3][f'{key}_growth_pct'])} |" for key in EXPENSES)
    margin_report=f'''# Operating-margin audit

**Verdict:** The updated Base Case ties: 2027 revenue {money(b27['revenue_m'])} less six operating-expense categories {money(b27['operating_expense_m'])} equals {money(b27['operating_income_m'])}, or {percent(b27['operating_margin_pct'])}. The 2028 result is {percent(b28['operating_margin_pct'])}. These are analyst outputs, not guidance. [Quarterly engine](../data/forecast/forecast_quarterly.csv); [Q2 2026 release]({Q2_RELEASE}).

| Year | Revenue | Operating expense | Operating income | Margin | Expense growth |
|---|---:|---:|---:|---:|---:|
{margin_rows}

2026 combines two **ACTUAL** and two **FORECAST** quarters. Category totals below include the same basis. The expense/revenue ratio is {percent(ma[1]['expense_to_revenue_pct'])} in 2026, {percent(ma[2]['expense_to_revenue_pct'])} in 2027 and {percent(ma[3]['expense_to_revenue_pct'])} in 2028.

| Category | 2026 | 2027 | 2027 growth | 2028 | 2028 growth |
|---|---:|---:|---:|---:|---:|
{expense_rows}

**Mechanics:** Brokerage cost has a fixed base plus a weighted transaction-unit basket. Operations partly follows funded customers. Credit provision follows modeled card balances. Marketing partly follows net customer additions. Technology and G&A follow visible quarterly budget steps rather than revenue percentages. These fixed-like and semi-variable classifications are analyst assumptions; Robinhood does not disclose product-level cost elasticities. [Forecast method](FORECAST_METHOD.md).

**Leverage:** 2027 revenue grows {percent(100*(b27['revenue_m']/b26['revenue_m']-1))} and expense grows {percent(100*(b27['operating_expense_m']/b26['operating_expense_m']-1))}; incremental GAAP operating margin is {percent(ma[2]['incremental_operating_margin_pct'])}. 2028 incremental margin is {percent(ma[3]['incremental_operating_margin_pct'])}. The reported 2024–2025 incremental margin was **68.3%**; the forecast does not carry it forward. Credit provision is a material rising expense in this model, while the 2026 comparison embeds H2 spend assumptions calibrated with the adjusted-expense outlook in view. [Phase 3 history](HISTORICAL_ANALYSIS.md); [FY 2025 filing]({FY25}).

**Challenge:** A high forecast margin depends on transaction monetization, interest balance/yield paths and expense restraint occurring together. The model's 2026 adjusted expense comparison is a consistency check, not independent validation of 2027–2028 category budgets.
'''
    (REPORTS/'OPERATING_MARGIN_AUDIT.md').write_text(margin_report)
    t=m['thresholds']; p=m['paths']; sh=m['shocks']
    threshold_lines=[]
    for r in t:
        value='not attainable under the modeled cost response' if r['required_input'] is None else f"{r['required_input']:,.2f} {r['unit']}"
        outside='; outside recent range' if r['outside_recent_range'] else ''
        threshold_lines.append(f"| {r['threshold']} | {value}{outside} | {r['method']} |")
    path_lines='\n'.join(f"| {r['path']} | {r['defined_shock']} | {money(r['2027_revenue_delta_m'])} | {money(r['2027_operating_income_delta_m'])} | {r['controllability']} | {r['data_confidence']} |" for r in p)
    underwrite_lines='\n'.join(f"| {r['path']} | {r['historical_evidence']} | {r['primary_drivers']} | {r['execution_dependency']} |" for r in p)
    mix0=f['derived']['2026Q2_mix_pct']
    mix_lines=[f"| 2026 Q2 ACTUAL | {percent(mix0['market_activity_revenue_m'])} | {percent(mix0['interest_balance_revenue_m'])} | {percent(mix0['disclosed_recurring_revenue_m'])} | {percent(mix0['unclassified_revenue_m'])} |"]
    for scenario in SCENARIOS:
        x=m['annual'][scenario]['2027']
        mix_lines.append(f"| 2027 {scenario} FORECAST | {percent(x['market_activity_pct'])} | {percent(x['interest_balance_pct'])} | {percent(x['disclosed_recurring_pct'])} | {percent(x['unclassified_pct'])} |")
    risk_lines=[
        f"| Trading activity | Options units; revenue and brokerage cost | {money(sh['options_activity_down_20pct_oi_m'])} 2027 operating income at -20% | Partial | Medium |",
        f"| Transaction monetization | Options, crypto, equities, event revenue | {money(sh['transaction_monetization_down_20pct_m'])} 2027 revenue at -20% broad transaction pricing | Partial | Low post acquisition for crypto |",
        f"| Policy rates | Net interest revenue | {money(sh['policy_rate_down_100bp_m'])} 2027 revenue at -100 bp modeled policy | Low | Medium-low |",
        f"| Customer growth | Customers, revenue, marketing | {money(sh['customer_additions_down_25pct_m'])} 2027 revenue at -25% additions | Medium | Low for marginal profit |",
        f"| Technology spending | Operating expense | {money(sh['technology_up_10pct_oi_m'])} 2027 operating income at +10% spend | High | Medium |",
    ]
    decision=f'''# Strategic decision framework

**Decision:** Concentrate management attention on realized trading monetization, customer balance conversion, and expense conversion. The three paths are complementary sources of growth, not investment proposals with invented returns. Values are Base-relative **defined shocks** for 2027; they are not expected returns or probabilities. [Forecast sensitivities](../data/forecast/sensitivity_results.csv).

| Analytical path | Defined shock | 2027 revenue change | Operating-income change | Management control | Data confidence |
|---|---|---:|---:|---|---|
{path_lines}

| Path | Historical evidence | Primary financial drivers | Execution dependency |
|---|---|---|---|
{underwrite_lines}

**Customer and asset scale.** Reported 2025 Q4 platform assets of $322.1b and 27.0m funded customers were much larger than 2023 Q4's $102.6b and 23.4m, but acquisitions and market value changes affect assets. Net additions and deposits are observable. The model's marketing cost response means more additions alone do not offset a 20% crypto-volume/customer shock in 2027; that is a limitation of the consolidated expense proxy, not a claim that new customers lack long-term value. [Historical analysis](HISTORICAL_ANALYSIS.md); [2025 filing]({FY25}).

**Transaction engagement.** In the exact 2024 versus 2023 bridge, measured comparable-product activity contributed $621m of $862m transaction growth. The +20% options-activity case adds {money(sh['options_activity_up_20pct_m'])} revenue in 2027, while a 20% transaction-monetization decline removes {money(abs(sh['transaction_monetization_down_20pct_m']))}. These responses depend on market activity and pricing; funded customers are an aggregate denominator, not product active users. [Historical bridge](../data/analysis/revenue_growth_bridges.csv).

**Balance and recurring monetization.** The matched 2025 Q2–2026 Q2 disclosure had a +$90.5m interest balance effect and -$13.5m yield/mix effect. A defined +50% cash-capture shock adds {money(p[2]['2027_revenue_delta_m'])} in 2027; this is a model test, not a plan. In 2027 Base, interest/balance revenue is {percent(b27['interest_balance_pct'])} of total, whereas separately disclosed Gold is {percent(b27['disclosed_recurring_pct'])}. The -100 bp modeled policy case reduces revenue by {money(abs(sh['policy_rate_down_100bp_m']))}; Cash Sweep is excluded from that policy case. [Q2 filing]({Q2_FILING}); [interest audit](INTEREST_SENSITIVITY_AUDIT.md).

## What must be true — exact engine thresholds

The first three tests recover **2027 Base operating income**, holding all other selected inputs fixed. They solve the full consolidated model and include its specified variable costs. The final two are algebraic operating benchmarks, not company targets.

| Condition | Required input | Method |
|---|---|---|
{chr(10).join(threshold_lines)}

**Interpretation:** The options threshold lies above the 2025 Q4–2026 Q2 observed 21.6–27.7 quarterly contracts per average funded customer. The deposit threshold is well above the recent $15.9–$21.7b quarterly range. These tests expose how little of a deposit is assumed to become interest-earning cash immediately. They do not forecast management action.

## Revenue composition and downside

| Period / case | Market activity | Interest / balance | Disclosed Gold | Unclassified |
|---|---:|---:|---:|---:|
{chr(10).join(mix_lines)}

All buckets sum to total revenue. The forecast dollar amounts are in the [scenario summary](../data/forecast/scenario_summary.csv). Unclassified revenue is never called recurring. Neither activity nor interest revenue is inherently preferable: their market dependencies differ and product-level margins are unavailable. The Upside remains more activity-dependent than Base; the Downside's mix is also shaped by lower realized yields.

## Management risk map

The exposures below are isolated shocks with different sizes, not comparable probabilities or a risk score. Control and confidence are analyst judgments grounded in disclosed coverage. [Full sensitivity table](../data/forecast/sensitivity_results.csv).

| Risk | Variable affected | Defined exposure | Management control | Forecast confidence |
|---|---|---:|---|---|
{chr(10).join(risk_lines)}
'''
    (REPORTS/'STRATEGIC_DECISION.md').write_text(decision)
    challenge=f'''# CFO challenge

1. **What could reverse the recommendation?** If higher funded-customer additions generate materially more long-term balances or cross-product use than the consolidated model captures, the current near-term finding that additions alone do not recover a crypto shock would understate customer investment value. Cohort retention and product uptake are unavailable.
2. **Weakest forecast relationship:** Post-Bitstamp/WonderFi blended crypto bps combine App and acquired exchange volumes with undisclosed channel revenue. A change in mix could invalidate the {money(abs(sh['transaction_monetization_down_20pct_m']))} broad monetization stress as a description of product pricing. [Structural breaks](STRUCTURAL_BREAKS.md).
3. **Most assumption-dependent result:** The {percent(b27['operating_margin_pct'])} 2027 Base margin depends on analyst technology, marketing, G&A and credit-provision paths. 2026 H2 costs were calibrated with company adjusted expense outlook in view. It is not an independent company plan. [Margin audit](OPERATING_MARGIN_AUDIT.md).
4. **Largely outside management control:** Trading demand and policy rates. Management can influence experience, product mix, balance capture and spread sharing, but not guarantee trading units or rates. The policy -100 bp model effect is {money(sh['policy_rate_down_100bp_m'])}; the all-yield stress is a much broader hypothetical. [Rate audit](INTEREST_SENSITIVITY_AUDIT.md).
5. **Internal data needed:** Product-active customers, cohort deposits and retention, channel revenue and contribution margins, rate repricing contracts, credit vintages, staffing commitments, and marketing acquisition channel economics.

**Revision from challenge:** The final priorities emphasize monitoring and conditional resource gates. They do not assert that customer scale has low lifetime value or that higher balance-based revenue is automatically more stable. Management should re-underwrite the paths with internal cohort and product economics before allocating capital.
'''
    (REPORTS/'CFO_CHALLENGE.md').write_text(challenge)
    memo=f'''# Management memo — September 28, 2026 information cutoff

**To:** CFO, VP Finance, Head of Finance & Strategy<br>
**Subject:** Which drivers turn scale into operating profit?

## Executive conclusion

**RECOMMENDATION:** Focus on protecting trading engagement and realized monetization, converting net deposits into earning balances and deeper relationships, and gating technology, marketing, and G&A spend against realized operating-profit conversion. Treat trading demand and interest rates as scenario variables, not committed growth sources. This is an independent public-data analysis, not Robinhood guidance.

## What the historical data shows

**FACT:** Revenue rose from $2.95b in 2024 to $4.47b in 2025; funded customers and assets also expanded. **DERIVED:** Measured activity contributed $621m of $862m in the exact 2024 versus 2023 transaction-revenue bridge. Acquisitions and product launches make later bridges less directly comparable. Gold subscription was only 4.0% of 2025 revenue. [Historical analysis](HISTORICAL_ANALYSIS.md); [2025 10-K/A]({FY25}).

## What the forecast requires

**MODEL RESULT:** After the interest audit, Base reaches {billion(b27['revenue_m'])} of 2027 revenue and {percent(b27['operating_margin_pct'])} GAAP operating margin; 2028 reaches {billion(b28['revenue_m'])} and {percent(b28['operating_margin_pct'])}. The 2027 scenario revenue range is {billion(d27['revenue_m'])}–{billion(u27['revenue_m'])}. Base requires roughly 0.3m net customers and $17.7b net deposits per normal quarter, sustained product activity, and operating expenses growing more slowly than revenue. 2026 contains two actual and two forecast quarters; Q3 is a nowcast, not a reported financial result. [Forecast results](FORECAST_RESULTS.md); [margin audit](OPERATING_MARGIN_AUDIT.md).

## Largest financial sensitivities

**MODEL RESULT:** A 20% broad transaction-monetization decline removes {money(abs(sh['transaction_monetization_down_20pct_m']))} of 2027 revenue. A 20% options-activity decline cuts operating income by {money(abs(sh['options_activity_down_20pct_oi_m']))}. A 100 bp policy-rate decline with explicit analyst pass-through cuts revenue by {money(abs(sh['policy_rate_down_100bp_m']))}; Cash Sweep does not receive that policy shock. The separate {money(ia['uniform_yield_100bp_m'])} all-yield stress is wider than company rate exposure. [Sensitivities](SENSITIVITY_ANALYSIS.md); [rate audit](INTEREST_SENSITIVITY_AUDIT.md).

## Strategic priorities

1. Protect options engagement and watch realized revenue per contract and crypto bps. The activity-led historical bridge and transaction-pricing sensitivity make these earnings-critical, but market demand is not controllable.
2. Convert deposits into earning balances and Gold relationships while protecting net spread and credit quality. Balance growth offset weaker yield historically; Gold is growing but remains a modest disclosed share.
3. Gate product and growth spending to realized revenue. The modeled 2027 incremental operating margin is {percent(ma[2]['incremental_operating_margin_pct'])}, below 2025's 68.3% historical level, and credit provision increases materially. [Decision framework](STRATEGIC_DECISION.md).

## Key risks and KPIs

The two risks are trading/crypto normalization and lower realized yields combined with rising credit or fixed costs. Review funded-customer additions; deposits and earning-balance capture; options contracts/customer and revenue/contract; blended crypto bps; and net realized yield alongside expense/revenue by category each quarter. Internal cohort and product-margin data are needed before converting these priorities into capital commitments. [CFO challenge](CFO_CHALLENGE.md).
'''
    (REPORTS/'MANAGEMENT_MEMO.md').write_text(memo)
    interview=f'''# Interview guide

**Walk me through the project.** I reconciled 14 quarters of public financials, normalized operating metrics, built a 12-quarter product-and-balance driver forecast, audited rate and margin sensitivity, and compared three financial growth paths. The Base result is {billion(b27['revenue_m'])} revenue and {percent(b27['operating_margin_pct'])} operating margin in 2027.

**Why Robinhood?** Its product breadth, customer assets, trading activity, and net interest economics create a clear finance question: which parts of scale actually convert to profit?

**What did you discover?** Measured 2024 transaction growth was primarily activity-led. Balance growth offset yield pressure in the matched interest disclosure. Gold was only about 4% of 2025 revenue, so it cannot yet carry a recurring-revenue story alone.

**What drives revenue?** Options contracts times revenue/contract; crypto and equities notional times realized bps; event units times revenue/unit; earning balances times net yields; and Gold subscribers times revenue/subscriber. Funded customers normalize aggregate activity but are not product active users.

**Hardest modeling problem?** Bitstamp and WonderFi changed crypto scope, while channel revenue was not disclosed. I kept App/Bitstamp volume separate but used an explicitly blended, post-acquisition take rate with wide sensitivities.

**Why forecast this way?** Each revenue stream has observable volume or balance and monetization inputs. That makes scenario changes explainable and permits exact bridges instead of a single revenue growth plug.

**Why is 2027 margin reasonable?** It is conditional, not assured: {money(b27['revenue_m'])} revenue less {money(b27['operating_expense_m'])} six-category expense equals {money(b27['operating_income_m'])}. Expense grows less than revenue, but 2027 incremental conversion is {percent(ma[2]['incremental_operating_margin_pct'])}, below historical 2025's 68.3%.

**What if rates fall?** A modeled 100 bp policy-rate decline cuts 2027 revenue and operating income by about {money(abs(sh['policy_rate_down_100bp_m']))}. This differs from the {money(ia['uniform_yield_100bp_m'])} all-yield stress and Robinhood's {money(350)} static June 2026 disclosure. Cash Sweep is excluded from the policy test.

**What if trading activity drops?** A 20% options-activity shock reduces 2027 operating income by about {money(abs(sh['options_activity_down_20pct_oi_m']))}. Brokerage cost flexes only partly, so the earnings impact is large.

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
'''
    (REPORTS/'INTERVIEW_GUIDE.md').write_text(interview)
    resume=f'''# Resume bullets

- Built a 14-quarter public-company financial history and 12-quarter driver-based Robinhood operating forecast from SEC filings and company operating metrics, reconciling product revenue, net interest, six expense lines, and three scenarios.
- Modeled customer, trading, balance, and monetization sensitivities; identified a {money(abs(sh['transaction_monetization_down_20pct_m']))} 2027 revenue exposure to a defined 20% transaction-pricing shock and audited rate exposure against company disclosure.
- Identified three conditional growth priorities through exact break-even tests and delivered an executive workbook, eight-slide deck, and CFO memo with consistent forecast figures and explicit data limitations.
'''
    (REPORTS/'RESUME_BULLETS.md').write_text(resume)
    readme=f'''# Robinhood Strategic Finance & Operating Model

### “What Drives Robinhood's Next Phase of Profitable Growth?”

Built a **14-quarter historical financial model** and **12-quarter driver-based forecast** using Robinhood SEC filings, investor-relations releases, and operating metrics to analyze revenue drivers, operating leverage, scenario risk, and strategic growth priorities.

**Decision supported:** Which operating and financial drivers convert growing customers, assets, and product breadth into sustainable revenue and operating profit?

## Key questions and findings

- **What drove growth?** Measured activity accounted for $621m of the $862m 2024 versus 2023 transaction-revenue increase. Later acquisitions and new products require a disclosed residual. [Historical analysis](reports/HISTORICAL_ANALYSIS.md).
- **What does Base require?** {billion(b27['revenue_m'])} modeled 2027 revenue at {percent(b27['operating_margin_pct'])} GAAP operating margin; {billion(b28['revenue_m'])} at {percent(b28['operating_margin_pct'])} in 2028. The 2027 Downside–Upside range is {billion(d27['revenue_m'])}–{billion(u27['revenue_m'])}. These are **analyst scenarios, not company guidance**. [Forecast results](reports/FORECAST_RESULTS.md).
- **What matters most?** Trading engagement and monetization, earning-balance capture and net yield, and six-category expense conversion. The 2027 -100 bp policy-rate case is {money(sh['policy_rate_down_100bp_m'])}; the separate all-component realized-yield stress is broader. [Decision framework](reports/STRATEGIC_DECISION.md); [rate audit](reports/INTEREST_SENSITIVITY_AUDIT.md).

## Model outputs

| Deliverable | Decision use |
|---|---|
| [Excel operating model](models/Robinhood_Strategic_Finance_Model.xlsx) | Trace actuals, edit one selected case, compare reference scenarios and break-even conditions |
| [Executive deck](presentation/Robinhood_Strategic_Finance_Executive_Deck.pdf) | Eight-slide CFO narrative with conclusion headlines |
| [Management memo](reports/MANAGEMENT_MEMO.md) | Three priorities, two risks and monitoring KPIs |
| [Interview guide](reports/INTERVIEW_GUIDE.md) | Defend source choices, equations, limitations and recommendation |

## Screenshots

![Executive Dashboard](assets/screenshots/executive_dashboard.png)
![Historical Financials](assets/screenshots/historical_financials.png)
![Revenue Drivers](assets/screenshots/revenue_driver_analysis.png)
![Forecast](assets/screenshots/forecast.png)
![Sensitivity](assets/screenshots/sensitivity_analysis.png)
![Strategic Analysis](assets/screenshots/strategic_analysis.png)
![Executive Deck](assets/screenshots/executive_deck.png)

## Architecture and methods

SEC and company releases feed a source-registered historical pipeline (2023 Q1–2026 Q2). July/August 2026 are **partial-quarter operating observations**; Q3 2026 financials are **FORECAST/NOWCAST**. Options, crypto, equity and event revenue use product activity and realized monetization; net interest uses average earning balances and company-specific yields; Gold uses subscriber economics. Six operating-expense categories and GAAP-to-adjusted EBITDA reconciliation are explicit. [Forecast method](reports/FORECAST_METHOD.md) explains assumptions; [data quality](DATA_QUALITY_REPORT.md) and [structural breaks](reports/STRUCTURAL_BREAKS.md) explain coverage.

The workbook's selected case is live. Its Base/Upside/Downside comparison tables are **build-time reference snapshots** refreshed by `python -m src.phase5`; editing workbook assumptions does not revise those snapshots. Sensitivity and break-even results are conditional tests, not probabilities or initiative ROI.

## Run and verify

Install Python 3.11+ packages with `pip install -r requirements.txt`. The workbook builder also uses the bundled `@oai/artifact-tool` runtime supplied in Codex; deck export uses `python-pptx` and LibreOffice `soffice` on PATH. Then run:

```bash
python -m src.phase5
python -m unittest discover -s tests -v
```

Source publications are frozen at **September 28, 2026**. Historical values are REPORTED or DERIVED; future outputs are analyst ASSUMPTION or ESTIMATED calculations. Public data do not provide product-active users, product margins, cohort retention, internal budgets or initiative ROI. The [CFO challenge](reports/CFO_CHALLENGE.md) describes how these gaps could change the decision.

This is an independent portfolio project based solely on publicly available information and is not affiliated with Robinhood Markets, Inc.
'''
    (ROOT/'README.md').write_text(readme)


def run():
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in HISTORICAL_PATHS}
    run_phase4()
    history=load_history(); assumption_rows,values=build_assumptions(history)
    actual=actual_rows(history)
    forecasts={s:project(history,values,s) for s in SCENARIOS}
    summaries=make_summaries(actual,forecasts)
    sensitivities=make_sensitivities(history,values,forecasts['Base'])
    interest=audit_interest(forecasts['Base'],values)
    margin=audit_margin(actual,forecasts['Base'])
    thresholds=strategy_thresholds(history,values,forecasts['Base'],margin)
    paths=decision_paths(sensitivities)
    if not math.isclose(interest['uniform_yield_100bp_m'],selected_sensitivity(sensitivities,'realized_yields','+100bp'),abs_tol=1e-7):
        raise ValueError('All-yield audit does not reconcile')
    if not math.isclose(interest['policy_100bp_m'],selected_sensitivity(sensitivities,'policy_rate_with_pass_through','+100bp'),abs_tol=1e-7):
        raise ValueError('Policy-rate audit does not reconcile')
    if any(values[s][p]['cash_sweep_rate_pass_through'] != 0 for s in SCENARIOS for p in values[s] if p.startswith('202') and 'Q' in p):
        raise ValueError('Cash Sweep has policy-rate pass-through')
    f=facts_pack(actual,forecasts,summaries,sensitivities,interest,margin,thresholds,paths)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'headline_facts.json').write_text(json.dumps(f,sort_keys=True,indent=2)+'\n')
    (OUT/'workbook_inputs.json').write_text(json.dumps({
        'actual':actual,'assumptions':assumption_rows,'forecast':forecasts,
        'monthly':{p:history[2][p] for p in ('2026-07','2026-08')},
    },sort_keys=True,indent=2)+'\n')
    write_csv(OUT/'strategic_paths.csv',paths)
    write_csv(OUT/'break_even_thresholds.csv',thresholds)
    write_csv(OUT/'margin_bridge.csv',margin)
    write_csv(OUT/'source_addendum.csv',[
        {'variable':'2026Q2_100bp_company_rate_sensitivity_m','value':350,'period':'2026Q2',
         'classification':'REPORTED','source_name':'Robinhood 2026 Q2 10-Q Item 3',
         'source_url':Q2_FILING,'date_retrieved':'2026-09-29',
         'calculation':'Company hypothetical 100 bp change; period-end net exposed balances, following 12 months',
         'notes':'Cash Sweep excluded; pre-tax revenue, net income and cash flow effect'},
    ])
    write_reports(f)
    build_workbook()
    subprocess.run([sys.executable,'-m','src.build_deck'],cwd=ROOT,check=True)
    if {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in HISTORICAL_PATHS} != before:
        raise ValueError('Historical inputs changed during Phase 5')
    print('Phase 5 audited decision data and executive reports complete.')


if __name__ == '__main__':
    run()
