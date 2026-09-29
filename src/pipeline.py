"""Rebuild audited public Robinhood history and its provenance files."""
import argparse
import csv
import hashlib
import json
from datetime import datetime

from .config import ROOT, RAW, OUT, SEC_FACTS, IR_QUARTERS, IR_MONTHS, ARCHIVE, FILINGS
from .ingest import fetch, verify_cache, discover, release_period, month_range, sec_fact
from .normalize import parse_financial_release, parse_monthly_release, extract_quarterly_kpis, FIN_LABELS, EXPENSE_KEYS, MONTHLY_LABELS
from .validation import validate_financial

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def run(refresh=False):
    RAW.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    verify_cache(refresh)
    now=datetime.now().date().isoformat()
    manifest=[]; registry=[]; failures=[]
    facts_raw,status=fetch(SEC_FACTS,RAW/'sec_companyfacts.json',refresh)
    facts=json.loads(facts_raw)
    manifest.append({'source_id':'sec_companyfacts','source_type':'sec_api','period':'through_2026Q2',
        'canonical_url':SEC_FACTS,'retrieval_url':SEC_FACTS,'accession':'',
        'cache_filename':'sec_companyfacts.json','sha256':hashlib.sha256(facts_raw).hexdigest(),
        'status':status,'retrieved_at':now,'notes':'Standard taxonomy; amended 2025 FY retained.'})
    for period,accn in FILINGS:
        compact=accn.replace('-','')
        canonical=f'https://www.sec.gov/Archives/edgar/data/1783879/{compact}/{accn}-index.htm'
        manifest.append({'source_id':f'sec_{period}','source_type':'sec_filing','period':period,
            'canonical_url':canonical,'retrieval_url':SEC_FACTS,'accession':accn,
            'cache_filename':'sec_companyfacts.json','sha256':hashlib.sha256(facts_raw).hexdigest(),
            'status':'companyfacts_only','retrieved_at':now,
            'notes':'Filing HTML blocked (HTTP 403); standard GAAP facts available via SEC API.'})
    original_accn='0001783879-26-000023'
    manifest.append({'source_id':'sec_2025FY_original','source_type':'sec_filing','period':'2025FY',
        'canonical_url':f'https://www.sec.gov/Archives/edgar/data/1783879/{original_accn.replace("-", "")}/{original_accn}-index.htm',
        'retrieval_url':SEC_FACTS,'accession':original_accn,'cache_filename':'sec_companyfacts.json',
        'sha256':hashlib.sha256(facts_raw).hexdigest(),'status':'companyfacts_only','retrieved_at':now,
        'notes':'Original 10-K retained; amended 10-K/A is annual reference.'})
    links=discover(RAW,refresh)
    for path in sorted(RAW.glob('gnw_index_*.html')):
        page=int(path.stem.rsplit('_',1)[1])
        manifest.append({'source_id':f'gnw_index_{page}','source_type':'source_index','period':'through_2026-09-28',
            'canonical_url':ARCHIVE.format(page),'retrieval_url':ARCHIVE.format(page),'accession':'',
            'cache_filename':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'status':'cached','retrieved_at':now,'notes':'GlobeNewswire organization archive discovery page.'})
    financial={}; monthly={}; monthly_sources={}
    for url,title in sorted(links.items()):
        kind,period=release_period(title)
        if kind=='quarter' and period not in [f'{y}Q{q}' for y in range(2023,2027) for q in range(1,5) if (y,q)<=(2026,2)]:
            continue
        if kind=='month' and period not in month_range():
            continue
        if not period:
            continue
        name=f'gnw_{period}.html'
        try:
            raw,status=fetch(url,RAW/name,refresh)
            digest=hashlib.sha256(raw).hexdigest()
            manifest.append({'source_id':f'gnw_{period}','source_type':kind+'_release','period':period,
                'canonical_url':IR_QUARTERS if kind=='quarter' else IR_MONTHS,
                'retrieval_url':url,'accession':'','cache_filename':name,'sha256':digest,
                'status':status,'retrieved_at':now,'notes':'Robinhood-authored GlobeNewswire release; IR direct retrieval blocked.'})
            if kind=='quarter':
                financial[period]=parse_financial_release(raw,period)
            else:
                monthly[period]=parse_monthly_release(raw,period)
                monthly_sources[period]=url
                year,month=map(int,period.split('-'))
                prior=f'{year-1}-12' if month==1 else f'{year}-{month-1:02d}'
                if prior in month_range() and prior not in monthly:
                    monthly[prior]=parse_monthly_release(raw,prior,position=1)
                    monthly_sources[prior]=url
        except (RuntimeError,ValueError) as exc:
            failures.append(str(exc))
            check_metric='quarterly financial statement and earnings KPIs' if kind=='quarter' else 'monthly operating KPIs and quarterly aggregations'
            failures[-1]+=f' [affected: {check_metric}; period {period}]'
            manifest.append({'source_id':f'gnw_{period}','source_type':kind+'_release','period':period,
                'canonical_url':IR_QUARTERS if kind=='quarter' else IR_MONTHS,
                'retrieval_url':url,'accession':'','cache_filename':name,'sha256':'',
                'status':'failed','retrieved_at':now,'notes':str(exc)})
    periods=[f'{y}Q{q}' for y in range(2023,2027) for q in range(1,5) if (y,q)<=(2026,2)]
    fin_rows=[]; check_errors=[]
    for period in periods:
        row=financial.get(period,{'period':period})
        check_errors+=validate_financial(row)
        fin_rows.append(row)
    if len(financial)!=14:
        check_errors.append(f'Financial releases parsed: {len(financial)}/14')
    if failures:
        check_errors.append(f'{len(failures)} source retrieval/parse failure(s); see affected sources below')
    if financial.get('2026Q2',{}).get('revenue_m')!=1308 or financial.get('2026Q2',{}).get('operating_expense_m')!=734 or financial.get('2026Q2',{}).get('adjusted_ebitda_m')!=741:
        check_errors.append('2026 Q2 proof gate failed')
    q4_checks=[]
    for tag,key in [('Revenues','revenue_m'),('OperatingExpenses','operating_expense_m'),('NetIncomeLoss','net_income_m')]:
        fy=sec_fact(facts,tag,'2025-01-01','2025-12-31','0001783879-26-000029')
        nine=sec_fact(facts,tag,'2025-01-01','2025-09-30','0001783879-25-000310')
        release=financial.get('2025Q4',{}).get(key)
        derived=None if fy is None or nine is None else fy-nine
        q4_checks.append((key,fy,nine,derived,release))
        if derived is None or release is None or abs(derived-release)>1:
            check_errors.append(f'2025 Q4 SEC FY-minus-9M {key} tie failed: {fy}, {nine}, {release}')
    annual_checks=[]
    for year in (2023,2024,2025):
        accn=dict(FILINGS)[f'{year}FY']
        for tag,key in [('Revenues','revenue_m'),('OperatingExpenses','operating_expense_m'),('NetIncomeLoss','net_income_m')]:
            sec_total=sec_fact(facts,tag,f'{year}-01-01',f'{year}-12-31',accn)
            qvals=[financial.get(f'{year}Q{q}',{}).get(key) for q in range(1,5)]
            diff=None if sec_total is None or None in qvals else sum(qvals)-sec_total
            annual_checks.append((year,key,sec_total,diff))
            if diff is None or abs(diff)>1:
                check_errors.append(f'{year} annual {key} tie failed: {diff}')
    # Quarter-end monthly releases are not separate GNW publications. Preserve nulls.
    month_rows=[]
    for p in month_range():
        month_rows.append(monthly.get(p,{'period':p}))
    quarter_rows=[]
    for p in periods:
        y=int(p[:4]); q=int(p[-1]); months=[f'{y}-{m:02d}' for m in range(3*q-2,3*q+1)]
        items=[monthly.get(m,{}) for m in months]
        row={'period':p}
        for key in ('funded_customers_m','net_cumulative_funded_accounts_m','platform_assets_b','assets_under_custody_b','margin_book_b','cash_deposits_b','cash_sweep_b'):
            row[key]=items[-1].get(key)
        for key in ('net_deposits_b','equity_notional_b','options_contracts_m','crypto_notional_b','event_contracts_b'):
            vals=[x.get(key) for x in items]
            row[key]=sum(vals) if all(v is not None for v in vals) else None
        if p in financial:
            row.update(extract_quarterly_kpis((RAW/f'gnw_{p}.html').read_bytes()))
        quarter_rows.append(row)
    fin_fields=['period']+list(dict.fromkeys(list(FIN_LABELS.values())+['options_revenue_m','crypto_revenue_m','equities_revenue_m','event_contracts_revenue_m','other_transaction_revenue_m','unclassified_transaction_revenue_m','operating_income_m','adjusted_ebitda_m','adjusted_ebitda_recomputed_m','ebitda_non_gaap_m','sbc_adjustment_m','interest_expense_adjustment_m','depreciation_amortization_adjustment_m']))
    kpi_fields=['period']+list(dict.fromkeys(MONTHLY_LABELS.values()))
    quarterly_fields=kpi_fields+['investment_accounts_m','gold_subscribers_m','arpu_usd_annualized','platform_assets_earnings_b']
    write_csv(OUT/'historical_financials_quarterly.csv',fin_rows,fin_fields)
    write_csv(OUT/'operating_kpis_monthly.csv',month_rows,kpi_fields)
    write_csv(OUT/'operating_kpis_quarterly.csv',quarter_rows,quarterly_fields)
    manifest_fields=['source_id','source_type','period','canonical_url','retrieval_url','accession','cache_filename','sha256','status','retrieved_at','notes']
    write_csv(ROOT/'data/source_manifest.csv',manifest,manifest_fields)
    for rows,kind in [(fin_rows,'quarterly_financial'),(month_rows,'monthly_kpi'),(quarter_rows,'quarterly_kpi')]:
        for row in rows:
            for key,value in row.items():
                if key=='period' or value is None:
                    continue
                reported_quarter_kpis=('investment_accounts_m','gold_subscribers_m','arpu_usd_annualized','platform_assets_earnings_b')
                normalized_other_income=(kind=='quarterly_financial' and key=='other_income_m' and row['period'] in ('2023Q1','2023Q2','2023Q3','2023Q4','2024Q1'))
                derived=(key in ('operating_income_m','adjusted_ebitda_recomputed_m','unclassified_transaction_revenue_m') or normalized_other_income or (kind=='quarterly_kpi' and key not in reported_quarter_kpis))
                url=next((m['retrieval_url'] for m in manifest if m['source_id']==f'gnw_{row["period"]}'), '')
                if kind=='monthly_kpi':
                    url=monthly_sources.get(row['period'],'')
                elif kind=='quarterly_kpi':
                    if key in reported_quarter_kpis:
                        url=next((m['retrieval_url'] for m in manifest if m['source_id']==f'gnw_{row["period"]}'),'')
                    else:
                        y=int(row['period'][:4]); q=int(row['period'][-1])
                        sources=[monthly_sources.get(f'{y}-{m:02d}','') for m in range(3*q-2,3*q+1)]
                        url=monthly_sources.get(f'{y}-{3*q:02d}','') if key in ('funded_customers_m','net_cumulative_funded_accounts_m','platform_assets_b','assets_under_custody_b','margin_book_b','cash_deposits_b','cash_sweep_b') else ' | '.join(sources)
                registry.append({'variable':key,'value':value,'period':row['period'],
                    'classification':'DERIVED' if derived else 'REPORTED',
                    'source_name':'Robinhood earnings release' if kind=='quarterly_financial' or key in reported_quarter_kpis else 'Robinhood monthly operating release',
                    'source_url':url,'date_retrieved':now,
                    'calculation':'revenue less operating expenses' if key=='operating_income_m' else ('negative of reported Other (income) expense, net' if normalized_other_income else ('transaction revenue minus disclosed product components' if key=='unclassified_transaction_revenue_m' else ('sum monthly flows / quarter-end stock' if kind=='quarterly_kpi' and derived else ('EBITDA plus disclosed adjustments' if key=='adjusted_ebitda_recomputed_m' else '')))),
                    'notes':('Prior-month comparison in following release. ' if kind=='monthly_kpi' and f'gnw_{row["period"]}' not in [m['source_id'] for m in manifest] else '')+'Unit and definition in data_dictionary.csv.'})
    for year,key,total,_ in annual_checks:
        registry.append({'variable':key,'value':total,'period':f'{year}FY','classification':'REPORTED',
            'source_name':'SEC company-facts / annual filing','source_url':SEC_FACTS,
            'date_retrieved':now,'calculation':'','notes':f'Annual SEC fact; accession {dict(FILINGS)[f"{year}FY"]}; USD millions.'})
    for key,fy,nine,derived,_ in q4_checks:
        registry.append({'variable':key,'value':nine,'period':'2025M9','classification':'REPORTED',
            'source_name':'SEC company-facts / 2025 Q3 10-Q','source_url':SEC_FACTS,
            'date_retrieved':now,'calculation':'','notes':'Nine months ended 2025-09-30; accession 0001783879-25-000310; USD millions.'})
        registry.append({'variable':f'sec_derived_{key}','value':derived,'period':'2025Q4','classification':'DERIVED',
            'source_name':'SEC amended FY 2025 10-K/A and Q3 10-Q','source_url':SEC_FACTS,
            'date_retrieved':now,'calculation':f'2025 FY {fy} minus 2025 nine months {nine}',
            'notes':'Independent quarter-only cross-check against Robinhood Q4 release; USD millions.'})
    write_csv(ROOT/'data/source_registry.csv',registry,
              ['variable','value','period','classification','source_name','source_url','date_retrieved','calculation','notes'])
    make_dictionary(fin_fields,kpi_fields)
    make_report(fin_rows,month_rows,quarter_rows,manifest,check_errors,failures,annual_checks,q4_checks)
    if check_errors:
        raise SystemExit('VALIDATION FAILED: '+'; '.join(check_errors))
    print(f'Validated {len(fin_rows)} financial quarters; {len(month_rows)} monthly KPI rows; {len(quarter_rows)} quarterly KPI rows.')


def make_dictionary(fin_fields,kpi_fields):
    rows=[]
    for group,fields in [('financial',fin_fields[1:]),('kpi',kpi_fields[1:])]:
        for key in fields:
            unit='billions of contracts' if key=='event_contracts_b' else ('USD billions' if key.endswith('_b') else ('millions of accounts/customers/contracts' if key.endswith('_m') and any(x in key for x in ('customers','accounts','contracts')) else 'USD millions'))
            kind='stock' if key in ('funded_customers_m','net_cumulative_funded_accounts_m','platform_assets_b','assets_under_custody_b','margin_book_b','cash_deposits_b','cash_sweep_b') else 'flow'
            rows.append({'metric':key,'description':key.replace('_',' '),'unit':unit,
                'frequency':'quarterly' if group=='financial' else 'monthly and quarterly',
                'stock_or_flow':kind,'quarterly_aggregation':'not applicable; reported quarter' if group=='financial' else ('last month' if kind=='stock' else 'sum complete three months'),
                'definition_changes':'Bitstamp/TradePMR/WonderFi acquisitions; cash sweep Feb 2026; Trump Accounts Jul 2026' if group=='kpi' else ('Earlier Other (income) expense presentation sign-normalized to positive other income.' if key=='other_income_m' else 'Revenue taxonomy evolves; event contracts reported separately in later periods.')})
    rows += [
        {'metric':'investment_accounts_m','description':'Investment accounts','unit':'millions of accounts','frequency':'quarterly','stock_or_flow':'stock','quarterly_aggregation':'reported quarter-end','definition_changes':'Coverage starts when disclosed in earnings release.'},
        {'metric':'gold_subscribers_m','description':'Robinhood Gold subscribers','unit':'millions of subscribers','frequency':'quarterly','stock_or_flow':'stock','quarterly_aggregation':'reported quarter-end','definition_changes':'Coverage varies by release.'},
        {'metric':'arpu_usd_annualized','description':'Company-reported annualized ARPU','unit':'USD per funded customer annualized','frequency':'quarterly','stock_or_flow':'ratio','quarterly_aggregation':'reported quarter','definition_changes':'Company definition and funded-customer base should be checked across periods.'},
        {'metric':'platform_assets_earnings_b','description':'Rounded platform assets in earnings release','unit':'USD billions','frequency':'quarterly','stock_or_flow':'stock','quarterly_aggregation':'reported quarter-end','definition_changes':'Compare with precise monthly period-end stock; Q4 2025 publications disagree.'},
    ]
    write_csv(ROOT/'data/data_dictionary.csv',rows,list(rows[0]))


def make_report(fin,monthly,quarterly,manifest,errors,failures,annual,q4_checks):
    f=lambda p:next((x for x in fin if x['period']==p),{})
    q=f('2026Q2')
    missing_fin={key:sum(x.get(key) is None for x in fin) for key in set().union(*(x.keys() for x in fin)) if key!='period'}
    missing_month={key:sum(x.get(key) is None for x in monthly) for key in set().union(*(x.keys() for x in monthly)) if key!='period'}
    missing_quarter={key:sum(x.get(key) is None for x in quarterly) for key in ('investment_accounts_m','gold_subscribers_m','arpu_usd_annualized','platform_assets_earnings_b')}
    asset_mismatches=[(r['period'],r['platform_assets_b'],r['platform_assets_earnings_b']) for r in quarterly if r.get('platform_assets_b') is not None and r.get('platform_assets_earnings_b') is not None and abs(r['platform_assets_b']-r['platform_assets_earnings_b'])>1]
    lines=['# Data quality report','','**Cutoff:** 2026-09-28. **Status:** '+('VALIDATED FINANCIALS; DOCUMENTED KPI SOURCE EXCEPTION' if not errors else 'NOT VALIDATED'),
        '',f'Financial rows: {len(fin)} (2023 Q1–2026 Q2). Monthly KPI rows: {len(monthly)} (Jan 2023–Aug 2026). Quarterly KPI rows: {len(quarterly)} (through 2026 Q2).',
        '', 'Sources for proof gates: [Robinhood Q2 2026 release](https://www.globenewswire.com/news-release/2026/07/29/3335576/0/en/robinhood-reports-second-quarter-2026-results.html); [SEC company-facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0001783879.json); [2025 amended 10-K/A](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000029/0001783879-26-000029-index.htm); [2025 Q3 10-Q](https://www.sec.gov/Archives/edgar/data/1783879/000178387925000310/0001783879-25-000310-index.html); [Robinhood Q4 2025 release](https://www.globenewswire.com/news-release/2026/02/10/3235771/0/en/robinhood-reports-fourth-quarter-and-full-year-2025-results.html).',
        '', '## Proof gates',
        f'- 2026 Q2 revenue: {q.get("transaction_revenue_m")} + {q.get("net_interest_revenue_m")} + {q.get("other_revenue_m")} = {q.get("revenue_m")} USD million.',
        f'- 2026 Q2 operating expenses: six categories sum to {sum(q.get(k,0) for k in EXPENSE_KEYS)} vs {q.get("operating_expense_m")} USD million.',
        f'- 2026 Q2 adjusted EBITDA: {q.get("ebitda_non_gaap_m")} EBITDA + 105 SBC + 23 restructuring − 106 deconsolidation gain − 23 equity gains = {q.get("adjusted_ebitda_recomputed_m")}, matching reported {q.get("adjusted_ebitda_m")} USD million.',
        '- 2025 Q4 FY-minus-nine-month checks (amended 10-K/A, Q3 10-Q, company Q4 release; USD million):',
        '', '## Annual SEC statement ties (USD million; tolerance ±1)',
    ]
    lines[lines.index('## Annual SEC statement ties (USD million; tolerance ±1)'):lines.index('## Annual SEC statement ties (USD million; tolerance ±1)')]=[
        f'  - {key}: {fy} − {nine} = {derived}; Q4 release {release}.' for key,fy,nine,derived,release in q4_checks
    ]+['']
    lines += [f'- {y} {key}: SEC annual {total}; sum of four release quarters less SEC annual {diff}.' for y,key,total,diff in annual]
    lines += ['', '## Reconciliation and extraction exceptions']
    lines += [f'- {e}' for e in errors] if errors else ['- All populated quarterly revenue/expense category sums, pretax/net income, operating-income arithmetic, and adjusted EBITDA adjustment rows tie within ±1 USD million.']
    lines += [f'- {e}' for e in failures] if failures else ['- No release retrieval or parse failures.']
    lines += ['', '## Coverage gaps and source differences',
        '- SEC filing HTML and Robinhood IR downloads returned HTTP 403 in this environment. SEC company-facts supplies standard tagged GAAP revenue cross-checks; Robinhood-authored GlobeNewswire releases supply statements, non-GAAP reconciliations, and accessible monthly KPI tables. Filing-specific product revenue note details and some operating metrics remain unavailable from this cache.',
        '- Quarter-end months (March, June, September, December) lack standalone releases in this archive, but the following month’s company release reports their values in its prior-month comparison column. Those values are backfilled with that release as provenance. Values absent from both columns remain null.',
        '- Monthly KPI headings and fields change over time; blanks in the processed files are undisclosed or unavailable, never inferred zero.',
        '- Adjusted EBITDA is company-reported and separately recomputed from the adjustment rows in all 14 accessible quarterly releases. The reconciliation is non-GAAP and should not be conflated with operating income.',
        '- Material difference threshold for rounded earnings-release assets versus monthly period-end assets: USD 1 billion. Both values are preserved; the monthly value is the quarter-end aggregation input. Do not treat the pair as a reconciled stock series until the definition/revision difference is resolved.',
        '', '### Missing financial fields (quarters of 14)',
    ]
    lines += [f'- {k}: {v}' for k,v in sorted(missing_fin.items())]
    lines += ['', '### Missing monthly KPI fields (months of 44)']
    lines += [f'- {k}: {v}' for k,v in sorted(missing_month.items())]
    lines += ['', '### Missing quarterly-only operating fields (quarters of 14)']
    lines += [f'- {k}: {v}' for k,v in sorted(missing_quarter.items())]
    lines += ['', '### Material platform-asset source differences']
    lines += [f'- {p}: precise month-end {monthly_value} USD billion; rounded earnings release {earnings_value} USD billion; difference {round(earnings_value-monthly_value,1)} USD billion.' for p,monthly_value,earnings_value in asset_mismatches] if asset_mismatches else ['- None above USD 1 billion.']
    if any(p=='2025Q4' for p,_,_ in asset_mismatches):
        lines += ['- The 2025 Q4 comparison uses the [Q4 earnings release](https://www.globenewswire.com/news-release/2026/02/10/3235771/0/en/robinhood-reports-fourth-quarter-and-full-year-2025-results.html) and December 2025 value in the [January 2026 operating release](https://www.globenewswire.com/news-release/2026/02/19/3241521/0/en/robinhood-markets-inc-reports-january-2026-operating-data.html). The reason for the difference is not established by this pipeline; later asset monetization analysis must choose and document a consistent series.']
    lines += ['', '## Comparability and modeling limits',
        '- Bitstamp (2025), TradePMR (2026), and WonderFi (2026) change the scope of customers, assets, and/or volume. Historical growth spanning those dates is not a clean organic measure.',
        '- February 2026 cash-sweep program changes moved balances to free credit; July 2026 Trump Accounts affected platform assets and deposits without an equivalent funded-customer change. Treat both as definition breaks.',
        '- Product-level active users, retention, CAC, and contribution margin are not a consistent public series. Later work may calculate labeled aggregate proxies; none are reported here.',
        '- Historical outputs are source facts and arithmetic only. No 2026 Q3 financial result, forecast, initiative ROI, or strategic recommendation is included.',
        '', '## Rebuild',
        '`python3 -m src.pipeline` uses local `data/raw/` cache and fetches missing releases; `--refresh` re-downloads sources. Network failures name the source. Raw HTML/JSON is ignored by Git; checksums and retrieval URLs are in `data/source_manifest.csv`.',
        '']
    (ROOT/'DATA_QUALITY_REPORT.md').write_text('\n'.join(lines))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true')
    run(parser.parse_args().refresh)
