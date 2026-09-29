"""Source-backed Phase 3 historical analysis; no forecasts or modeled facts."""
import csv
import hashlib
import math
import statistics
import subprocess
from datetime import date
from pathlib import Path

from .config import ROOT, RAW
from .validation import validate_financial

OUT = ROOT / 'data' / 'analysis'
FRED_URL = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF&cosd=2023-01-01&coed=2026-06-30'
FRED_CACHE = RAW / 'fred_dff_through_2026q2.csv'
FIELDS = {
    'financial_kpis_quarterly.csv': ['period','revenue_m','transaction_revenue_m','net_interest_revenue_m','other_revenue_m','options_revenue_m','crypto_revenue_m','equities_revenue_m','event_contracts_revenue_m','operating_expense_m','operating_income_m','net_income_m','adjusted_ebitda_m','funded_customers_m','investment_accounts_m','gold_subscribers_m','average_funded_customers_m','customer_assets_b','asset_definition','net_deposits_b','options_contracts_m','crypto_notional_b','equity_notional_b','event_contracts_b','margin_book_b','cash_deposits_b','cash_sweep_b','reported_arpu_usd_annualized','revenue_per_avg_customer_usd','transaction_revenue_per_avg_customer_usd','derived_arpu_usd_annualized','arpu_difference_usd','assets_per_customer_usd','net_deposits_per_avg_customer_usd','revenue_yoy_pct','transaction_revenue_yoy_pct','net_interest_revenue_yoy_pct','operating_expense_yoy_pct','operating_margin_pct','adjusted_ebitda_margin_pct','expense_to_revenue_pct','fed_funds_quarter_average_pct','interest_asset_avg_balance_m','interest_asset_revenue_m','margin_avg_balance_m','margin_interest_revenue_m','cash_deposit_avg_balance_m','cash_deposit_interest_revenue_m','cash_sweep_avg_balance_m','cash_sweep_interest_revenue_m','credit_card_avg_balance_m','credit_card_interest_revenue_m','interest_asset_implied_yield_pct','interest_asset_balance_effect_m','interest_asset_yield_effect_m','interest_remainder_change_m','comparability_flags'],
    'revenue_mix_quarterly.csv': ['period','total_revenue_m','market_activity_m','interest_balance_m','disclosed_recurring_m','unclassified_m','market_activity_pct','interest_balance_pct','disclosed_recurring_pct','unclassified_pct','market_activity_yoy_pct','interest_balance_yoy_pct','disclosed_recurring_yoy_pct','unclassified_yoy_pct','classification_note'],
    'monetization_metrics_quarterly.csv': ['period','funded_customers_m','average_funded_customers_m','customer_assets_b','net_deposits_b','revenue_per_avg_customer_usd','transaction_revenue_per_avg_customer_usd','assets_per_customer_usd','net_deposits_per_avg_customer_usd','reported_arpu_usd_annualized','derived_arpu_usd_annualized','options_contracts_m','options_revenue_per_contract_usd','crypto_notional_b','crypto_revenue_per_notional_bps','equity_notional_b','equity_revenue_per_notional_bps','event_contracts_b','event_revenue_per_contract_usd','crypto_scope_note','event_scope_note'],
    'operating_leverage_quarterly.csv': ['period','revenue_m','operating_expense_m','operating_income_m','adjusted_ebitda_m','revenue_yoy_pct','expense_yoy_pct','operating_income_yoy_pct','adjusted_ebitda_yoy_pct','incremental_operating_margin_yoy_pct','incremental_adjusted_ebitda_margin_yoy_pct','expense_to_revenue_pct','brokerage_transaction_to_revenue_pct','technology_development_to_revenue_pct','operations_to_revenue_pct','credit_loss_to_revenue_pct','marketing_to_revenue_pct','general_administrative_to_revenue_pct','interpretation_flag'],
    'revenue_growth_bridges.csv': ['comparison','start_periods','end_periods','product','start_revenue_m','end_revenue_m','change_m','customer_scale_effect_m','activity_effect_m','monetization_effect_m','mix_residual_effect_m','bridge_total_m','coverage_note'],
    'forecast_driver_summary.csv': ['driver','rank','historical_evidence','forecast_relationship','data_quality','recommended_method','key_limitation'],
}


def read_csv(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def number(value):
    if value is None or value == '':
        return None
    return float(value)


def safe_div(a, b):
    return a / b if a is not None and b not in (None, 0) else None


def pct_change(new, old):
    return 100 * (new / old - 1) if new is not None and old not in (None, 0) else None


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: '' if row.get(k) is None else row[k] for k in fields})


def load_components():
    facts = {}
    for row in read_csv(ROOT / 'data/disclosed_components.csv'):
        if row['classification'] not in ('REPORTED', 'DERIVED'):
            raise ValueError(f"Historical component is not reported/derived: {row['metric']} {row['period']}")
        key = row['period'], row['metric']
        if key in facts:
            raise ValueError(f'Duplicate component: {key}')
        facts[key] = {**row, 'value': float(row['value'])}
    return facts


def component(facts, period, metric):
    record = facts.get((period, metric))
    return record['value'] if record else None


def get_fred():
    if not FRED_CACHE.exists():
        FRED_CACHE.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(['curl','-L','--fail','--silent','--show-error','--max-time','35',FRED_URL], capture_output=True)
        if result.returncode:
            raise RuntimeError(f'FRED DFF retrieval failed: {result.stderr.decode(errors="replace")}')
        FRED_CACHE.write_bytes(result.stdout)
    values = {}
    for row in read_csv(FRED_CACHE):
        day = date.fromisoformat(row['observation_date'])
        if day > date(2026,6,30) or not row['DFF'] or row['DFF'] == '.':
            continue
        period = f'{day.year}Q{(day.month-1)//3+1}'
        values.setdefault(period, []).append(float(row['DFF']))
    if len(values) != 14:
        raise ValueError(f'FRED DFF coverage: {len(values)}/14 quarters')
    return {period: statistics.mean(xs) for period, xs in values.items()}


def validate_components(fin, facts):
    by_period = {row['period']: row for row in fin}
    for (period, metric), record in facts.items():
        if period == '2022Q4':
            continue
        value = record['value']
        parent = by_period[period]
        if metric == 'gold_subscription_revenue_m' and value > number(parent['other_revenue_m']):
            raise ValueError(f'{period} Gold revenue exceeds other revenue')
        if metric in ('event_contracts_revenue_m','other_transaction_revenue_m'):
            known = sum(number(parent[k]) or 0 for k in ('options_revenue_m','crypto_revenue_m','equities_revenue_m'))
            known += sum(component(facts, period, k) or 0 for k in ('event_contracts_revenue_m','other_transaction_revenue_m'))
            if known > number(parent['transaction_revenue_m']) + 1:
                raise ValueError(f'{period} transaction components exceed reported total')
        if metric == 'interest_asset_revenue_m' and value > number(parent['net_interest_revenue_m']) + 60:
            raise ValueError(f'{period} interest asset component inconsistent with net interest total')
    required = {
        ('2025Q1','gold_subscription_revenue_m'):38,
        ('2025Q4','gold_subscription_revenue_m'):50,
        ('2026Q1','event_contracts_revenue_m'):104,
        ('2026Q2','interest_asset_avg_balance_m'):66383,
        ('2025Q2','crypto_notional_b'):35,
    }
    for key, expected in required.items():
        if component(facts, *key) != expected:
            raise ValueError(f'Changed source fact {key}; review disclosure before updating')
    for period in ('2025Q1','2025Q2','2026Q1','2026Q2'):
        row=by_period[period]
        transaction_parts=[number(row[k]) for k in ('options_revenue_m','crypto_revenue_m','equities_revenue_m')]
        transaction_parts += [component(facts,period,'event_contracts_revenue_m'),component(facts,period,'other_transaction_revenue_m')]
        if not math.isclose(sum(transaction_parts),number(row['transaction_revenue_m']),abs_tol=1):
            raise ValueError(f'{period} complete transaction note does not tie')
    for period in ('2025Q2','2026Q1','2026Q2'):
        balance=sum(component(facts,period,k+'_avg_balance_m') for k in ('margin','cash_deposit','cash_sweep','credit_card'))
        revenue=sum(component(facts,period,k+'_interest_revenue_m') for k in ('margin','cash_deposit','cash_sweep','credit_card'))
        if not math.isclose(balance,component(facts,period,'interest_asset_avg_balance_m'),abs_tol=1):
            raise ValueError(f'{period} interest-earning balance components do not tie')
        if not math.isclose(revenue,component(facts,period,'interest_asset_revenue_m'),abs_tol=1):
            raise ValueError(f'{period} interest-earning revenue components do not tie')
    for year,total in ((2023,75),(2024,109),(2025,179)):
        observed=sum(component(facts,f'{year}Q{q}','gold_subscription_revenue_m') for q in range(1,5))
        if not math.isclose(observed,total,abs_tol=1):
            raise ValueError(f'{year} quarterly Gold subscription revenue does not tie annual filing')


def build(fin_raw, kpi_raw, facts, rates):
    fin = [{k: (v if k == 'period' else number(v)) for k,v in row.items()} for row in fin_raw]
    kpis = {row['period']: {k: (v if k == 'period' else number(v)) for k,v in row.items()} for row in kpi_raw}
    periods = [r['period'] for r in fin]
    if periods != [f'{y}Q{q}' for y in range(2023,2027) for q in range(1,5) if (y,q) <= (2026,2)]:
        raise ValueError('Historical financial periods changed')
    if any(validate_financial(r) for r in fin):
        raise ValueError('Phase 2 financial reconciliation failed')
    validate_components(fin, facts)
    frows=[]; mixes=[]; mons=[]; lever=[]
    opening = component(facts,'2022Q4','funded_customers_opening_m')
    for i, source in enumerate(fin):
        p=source['period']; k=kpis[p]; prior=fin[i-4] if i>=4 else None
        customers=k['funded_customers_m'] if k['funded_customers_m'] is not None else k['net_cumulative_funded_accounts_m']
        previous_customers=opening if i==0 else frows[-1]['funded_customers_m']
        avg=(customers+previous_customers)/2 if customers is not None and previous_customers is not None else None
        assets=k['platform_assets_b'] if k['platform_assets_b'] is not None else k['assets_under_custody_b']
        asset_def='Total Platform Assets' if k['platform_assets_b'] is not None else 'Total AUC'
        event=component(facts,p,'event_contracts_revenue_m')
        if event is None: event=source['event_contracts_revenue_m']
        gold=component(facts,p,'gold_subscription_revenue_m')
        avg_balance=component(facts,p,'interest_asset_avg_balance_m')
        interest_revenue=component(facts,p,'interest_asset_revenue_m')
        implied_yield=safe_div(400*interest_revenue,avg_balance) if interest_revenue is not None else None
        flags=[]
        if p in ('2023Q1','2025Q1'): flags.append('customer/asset definition transition')
        if p >= '2025Q2': flags.append('Bitstamp volume and assets')
        if p >= '2025Q1': flags.append('TradePMR RIA assets')
        if p >= '2026Q2': flags.append('WonderFi and credit growth')
        if p == '2025Q4': flags.append('platform assets revised after final crypto pricing')
        crypto_volume=k['crypto_notional_b'] if k['crypto_notional_b'] is not None else component(facts,p,'crypto_notional_b')
        event_volume=component(facts,p,'event_contracts_reported_quarterly_b')
        if event_volume is None: event_volume=k['event_contracts_b']
        row={**source,'event_contracts_revenue_m':event,'funded_customers_m':customers,
             'investment_accounts_m':k['investment_accounts_m'],'gold_subscribers_m':k['gold_subscribers_m'],
             'options_contracts_m':k['options_contracts_m'],'crypto_notional_b':crypto_volume,
             'equity_notional_b':k['equity_notional_b'],'event_contracts_b':event_volume,
             'margin_book_b':k['margin_book_b'],'cash_deposits_b':k['cash_deposits_b'],
             'cash_sweep_b':k['cash_sweep_b'],
             'average_funded_customers_m':avg,'customer_assets_b':assets,'asset_definition':asset_def,
             'net_deposits_b':k['net_deposits_b'],'reported_arpu_usd_annualized':k['arpu_usd_annualized'],
             'revenue_per_avg_customer_usd':safe_div(source['revenue_m'],avg),
             'transaction_revenue_per_avg_customer_usd':safe_div(source['transaction_revenue_m'],avg),
             'derived_arpu_usd_annualized':safe_div(4*source['revenue_m'],avg),
             'assets_per_customer_usd':safe_div(1000*assets,customers) if assets is not None else None,
             'net_deposits_per_avg_customer_usd':safe_div(1000*k['net_deposits_b'],avg) if k['net_deposits_b'] is not None else None,
             'operating_margin_pct':safe_div(100*source['operating_income_m'],source['revenue_m']),
             'adjusted_ebitda_margin_pct':safe_div(100*source['adjusted_ebitda_m'],source['revenue_m']),
             'expense_to_revenue_pct':safe_div(100*source['operating_expense_m'],source['revenue_m']),
             'fed_funds_quarter_average_pct':rates[p],
             'interest_asset_avg_balance_m':avg_balance,'interest_asset_revenue_m':interest_revenue,
             'interest_asset_implied_yield_pct':implied_yield,
             'comparability_flags':'; '.join(flags)}
        for prefix in ('margin','cash_deposit','cash_sweep','credit_card'):
            row[prefix+'_avg_balance_m']=component(facts,p,prefix+'_avg_balance_m')
            row[prefix+'_interest_revenue_m']=component(facts,p,prefix+'_interest_revenue_m')
        row['arpu_difference_usd']=row['derived_arpu_usd_annualized']-k['arpu_usd_annualized'] if row['derived_arpu_usd_annualized'] is not None and k['arpu_usd_annualized'] is not None else None
        for col in ('revenue_m','transaction_revenue_m','net_interest_revenue_m','operating_expense_m'):
            row[col.replace('_m','_yoy_pct')]=pct_change(source[col],prior[col]) if prior else None
        row['interest_asset_balance_effect_m']=None
        row['interest_asset_yield_effect_m']=None
        row['interest_remainder_change_m']=None
        if i and interest_revenue is not None and avg_balance is not None:
            previous=frows[-1]
            pb=previous['interest_asset_avg_balance_m']; pr=previous['interest_asset_revenue_m']
            if pb and pr is not None:
                row['interest_asset_balance_effect_m']=(avg_balance-pb)*(pr/pb)
                row['interest_asset_yield_effect_m']=avg_balance*((interest_revenue/avg_balance)-(pr/pb))
                row['interest_remainder_change_m']=(source['net_interest_revenue_m']-previous['net_interest_revenue_m'])-(interest_revenue-pr)
        frows.append(row)
        market=sum(source[x] for x in ('options_revenue_m','crypto_revenue_m','equities_revenue_m') if source[x] is not None)+(event or 0)
        unclassified=source['revenue_m']-market-source['net_interest_revenue_m']-(gold or 0)
        if unclassified < -1:
            raise ValueError(f'{p} revenue buckets exceed total')
        mix={'period':p,'total_revenue_m':source['revenue_m'],'market_activity_m':market,
             'interest_balance_m':source['net_interest_revenue_m'],'disclosed_recurring_m':gold,
             'unclassified_m':unclassified,
             'classification_note':'Gold not separately disclosed; recurring bucket null, all remaining other revenue unclassified' if gold is None else 'Gold subscription only; other transaction and other revenue unclassified'}
        for bucket in ('market_activity','interest_balance','disclosed_recurring','unclassified'):
            mix[bucket+'_pct']=safe_div(100*mix[bucket+'_m'],source['revenue_m']) if mix[bucket+'_m'] is not None else None
            mix[bucket+'_yoy_pct']=pct_change(mix[bucket+'_m'],mixes[i-4][bucket+'_m']) if i>=4 else None
        mixes.append(mix)
        crypto_comparable=crypto_volume is not None and p < '2025Q2'
        crypto_note='Combined acquisition scope; total volume/revenue ratio shown only as blended descriptive rate' if crypto_volume is not None and not crypto_comparable else ('Pre-Bitstamp scope' if crypto_volume is not None else 'Volume unavailable')
        mon={'period':p,'funded_customers_m':customers,'average_funded_customers_m':avg,'customer_assets_b':assets,
             'net_deposits_b':k['net_deposits_b'],'revenue_per_avg_customer_usd':row['revenue_per_avg_customer_usd'],
             'transaction_revenue_per_avg_customer_usd':row['transaction_revenue_per_avg_customer_usd'],
             'assets_per_customer_usd':row['assets_per_customer_usd'],
             'net_deposits_per_avg_customer_usd':row['net_deposits_per_avg_customer_usd'],
             'reported_arpu_usd_annualized':k['arpu_usd_annualized'],
             'derived_arpu_usd_annualized':row['derived_arpu_usd_annualized'],
             'options_contracts_m':k['options_contracts_m'],
             'options_revenue_per_contract_usd':safe_div(source['options_revenue_m'],k['options_contracts_m']),
             'crypto_notional_b':crypto_volume,
             'crypto_revenue_per_notional_bps':safe_div(10*source['crypto_revenue_m'],crypto_volume),
             'equity_notional_b':k['equity_notional_b'],
             'equity_revenue_per_notional_bps':safe_div(10*source['equities_revenue_m'],k['equity_notional_b']),
             'event_contracts_b':event_volume,
             'event_revenue_per_contract_usd':safe_div(event,event_volume*1000 if event_volume is not None else None),
             'crypto_scope_note':crypto_note,
             'event_scope_note':('Quarterly earnings volume 13.6B used; summed rounded monthly volume is 13.5B' if p=='2026Q2' else 'Quarterly volume/revenue matched') if event is not None and event_volume is not None else 'Numerator or denominator unavailable'}
        mons.append(mon)
        delta_revenue=source['revenue_m']-prior['revenue_m'] if prior else None
        interpretation=[]
        if p=='2023Q1': interpretation.append('large reported SBC/G&A; no YoY base')
        if p >= '2025Q1': interpretation.append('acquisition/product scope change')
        if delta_revenue is not None and delta_revenue <= 50: interpretation.append('small or negative revenue delta')
        lev={'period':p,'revenue_m':source['revenue_m'],'operating_expense_m':source['operating_expense_m'],
             'operating_income_m':source['operating_income_m'],'adjusted_ebitda_m':source['adjusted_ebitda_m'],
             'revenue_yoy_pct':row['revenue_yoy_pct'],'expense_yoy_pct':row['operating_expense_yoy_pct'],
             'operating_income_yoy_pct':pct_change(source['operating_income_m'],prior['operating_income_m']) if prior and prior['operating_income_m']>0 else None,
             'adjusted_ebitda_yoy_pct':pct_change(source['adjusted_ebitda_m'],prior['adjusted_ebitda_m']) if prior and prior['adjusted_ebitda_m']>0 else None,
             'incremental_operating_margin_yoy_pct':safe_div(100*(source['operating_income_m']-prior['operating_income_m']),delta_revenue) if prior and delta_revenue>50 else None,
             'incremental_adjusted_ebitda_margin_yoy_pct':safe_div(100*(source['adjusted_ebitda_m']-prior['adjusted_ebitda_m']),delta_revenue) if prior and delta_revenue>50 else None,
             'expense_to_revenue_pct':row['expense_to_revenue_pct'],'interpretation_flag':'; '.join(interpretation)}
        for exp in ('brokerage_transaction','technology_development','operations','credit_loss','marketing','general_administrative'):
            value=source.get(exp+'_expense_m')
            lev[exp+'_to_revenue_pct']=safe_div(100*value,source['revenue_m']) if value is not None else None
        lever.append(lev)
    bridges=build_bridges(fin,mons,facts)
    drivers=driver_summary(fin,mons,frows)
    return frows,mixes,mons,lever,bridges,drivers


def bridge_product(start, end, product):
    c0,c1=start['customers'],end['customers']; v0,v1=start['volume'],end['volume']; r0,r1=start['revenue'],end['revenue']
    if any(v is None for v in (c0,c1,v0,v1,r0,r1)) or min(c0,c1,v0,v1)<=0:
        return None
    a0=v0/c0; a1=v1/c1; m0=r0/v0; m1=r1/v1
    customer=(c1-c0)*a0*m0
    activity=c1*(a1-a0)*m0
    monetization=c1*a1*(m1-m0)
    if not math.isclose(customer+activity+monetization,r1-r0,abs_tol=1e-8):
        raise ValueError(f'{product} bridge does not reconcile')
    return customer,activity,monetization


def build_bridges(fin, mons, facts):
    by_fin={r['period']:r for r in fin}; by_mon={r['period']:r for r in mons}
    comparisons=[('2024 vs 2023',[f'2023Q{q}' for q in range(1,5)],[f'2024Q{q}' for q in range(1,5)]),
                 ('2025 vs 2024',[f'2024Q{q}' for q in range(1,5)],[f'2025Q{q}' for q in range(1,5)]),
                 ('2026 H1 vs 2025 H1',['2025Q1','2025Q2'],['2026Q1','2026Q2']),
                 ('2026 Q2 vs 2025 Q2',['2025Q2'],['2026Q2'])]
    rows=[]
    mapping={'options':('options_revenue_m','options_contracts_m'),
             'equities':('equities_revenue_m','equity_notional_b'),
             'crypto':('crypto_revenue_m','crypto_notional_b'),
             'event_contracts':('event_contracts_revenue_m','event_contracts_b')}
    def aggregate(ps, product):
        rev_key,vol_key=mapping[product]
        cs=[by_mon[p]['average_funded_customers_m'] for p in ps]
        revs=[by_fin[p][rev_key] if rev_key!='event_contracts_revenue_m' else (component(facts,p,rev_key) or by_fin[p][rev_key]) for p in ps]
        vols=[by_mon[p][vol_key] for p in ps]
        return {'customers':statistics.mean(cs) if all(x is not None for x in cs) else None,
                'revenue':sum(revs) if all(x is not None for x in revs) else None,
                'volume':sum(vols) if all(x is not None for x in vols) else None}
    for label,start_periods,end_periods in comparisons:
        total_start=sum(by_fin[p]['transaction_revenue_m'] for p in start_periods)
        total_end=sum(by_fin[p]['transaction_revenue_m'] for p in end_periods)
        effects=[0.0,0.0,0.0]
        for product in mapping:
            start=aggregate(start_periods,product); end=aggregate(end_periods,product)
            scope_break=product=='crypto' and (any(p>='2025Q2' for p in end_periods) != any(p>='2025Q2' for p in start_periods) or any(p>='2026Q2' for p in end_periods))
            decomposition=None if scope_break else bridge_product(start,end,product)
            note='Blended crypto volume scope changed; all growth in residual' if scope_break else ('Missing product revenue or volume; all growth in residual' if decomposition is None else 'Aggregate activity per funded customer is not product-user activity')
            change=end['revenue']-start['revenue'] if start['revenue'] is not None and end['revenue'] is not None else None
            if decomposition:
                customer=round(decomposition[0],3)
                activity=round(decomposition[1],3)
                decomposition=(customer,activity,round(change-customer-activity,3))
                effects=[a+b for a,b in zip(effects,decomposition)]
            rows.append({'comparison':label,'start_periods':'+'.join(start_periods),'end_periods':'+'.join(end_periods),
                         'product':product,'start_revenue_m':start['revenue'],'end_revenue_m':end['revenue'],
                         'change_m':change,'customer_scale_effect_m':decomposition[0] if decomposition else None,
                         'activity_effect_m':decomposition[1] if decomposition else None,
                         'monetization_effect_m':decomposition[2] if decomposition else None,
                         'mix_residual_effect_m':None,'bridge_total_m':sum(decomposition) if decomposition else None,
                         'coverage_note':note})
        effects=[round(x,3) for x in effects]
        residual=round((total_end-total_start)-sum(effects),3)
        total=effects+[residual]
        rows.append({'comparison':label,'start_periods':'+'.join(start_periods),'end_periods':'+'.join(end_periods),
                     'product':'TOTAL_TRANSACTION','start_revenue_m':total_start,'end_revenue_m':total_end,
                     'change_m':total_end-total_start,'customer_scale_effect_m':effects[0],
                     'activity_effect_m':effects[1],'monetization_effect_m':effects[2],
                     'mix_residual_effect_m':residual,'bridge_total_m':sum(total),
                     'coverage_note':'Residual includes new products, acquisition scope, unclassified transaction revenue and missing product units; not pure product mix'})
    return rows


def driver_summary(fin, mons, frows):
    spec=[
      ('Funded customers','PRIMARY DRIVER','14 quarter-end observations after NCFA name normalization','Scale in aggregate activity identity','Complete; naming transition in 2023','Quarter-end customers and average customers for flows','Not product-level active users'),
      ('Options contracts per funded customer','PRIMARY DRIVER','14 quarters of options contracts and revenue','Options contracts = average customers × aggregate contracts/customer','Complete','Activity per funded customer × realized dollars/contract','Proxy includes inactive customers'),
      ('Options revenue per contract','PRIMARY DRIVER','14 matched quarterly pairs','Options revenue = contracts × realized dollars/contract','Complete','Historical realized rate with explicit sensitivities','Product/ticker mix affects rate'),
      ('Equity notional per funded customer','PRIMARY DRIVER','14 matched quarterly volume/revenue pairs','Equity notional = customers × notional/customer','Complete','Activity per funded customer × monetization bps','Notional mix and market prices matter'),
      ('Crypto notional and realized bps','PRIMARY DRIVER','Quarterly revenue complete; volumes supplemented from Q2/Q3 2025 releases','Crypto revenue = notional × realized bps','Scope break after Bitstamp; WonderFi later','Separate acquisition-era regimes and stress volume/bps','Do not infer organic change across acquisitions'),
      ('Event contracts and monetization','SECONDARY DRIVER','Revenue disclosed separately in 2025 H1 and 2026 H1; volume only later','Event revenue = contracts × realized dollars/contract','Short series and new product','Explicit scenario input only after baseline is established','Missing earlier comparable units'),
      ('Interest-earning balances and realized yields','PRIMARY DRIVER','Matched balance/revenue table for 2025Q2 and 2026 H1','Interest-asset revenue = average balance × realized quarterly yield','Partial history; diverse balance mix','Model margin, cash/sweep and credit separately when sourced','Net interest includes securities lending and credit facility expense'),
      ('Platform assets and net deposits','SECONDARY DRIVER','Assets and deposits present quarterly, with major scope changes','Customer asset roll-forward and balance context','Acquisitions and AUC/platform definition break','Separate deposits, market moves and acquisitions','Assets are not all interest earning'),
      ('Gold subscribers and subscription revenue','SECONDARY DRIVER','Subscriber stock 12/14 quarters; Gold revenue 14/14 via reported and FY/YTD-derived facts','Gold revenue = average subscribers × realized fee revenue/subscriber','Quarterly revenue complete; subscriber stock partial','Use disclosed subscription economics and adoption bounds','Other revenue is not all recurring'),
      ('Operating expense categories','PRIMARY DRIVER','14 quarters of reported operating expense and revenue','Expense build by observed category behavior','Credit-loss line partial; acquisition effects','Category-specific cost paths with explicit leverage assumptions','Historical co-movement is not causation'),
      ('Federal funds rate','CONTEXT ONLY','Daily FRED series aggregated to 14 quarters','External rate context, not realized yield','Complete external series','Sensitivity context and reconciliation check','Do not use as Robinhood yield'),
    ]
    return [dict(zip(FIELDS['forecast_driver_summary.csv'],x)) for x in spec]


def run():
    fin=read_csv(ROOT/'data/processed/historical_financials_quarterly.csv')
    kpis=read_csv(ROOT/'data/processed/operating_kpis_quarterly.csv')
    registry=read_csv(ROOT/'data/source_registry.csv')
    if any(r['classification'] in ('ESTIMATED','ASSUMPTION') for r in registry):
        raise ValueError('Estimated/assumed fact entered historical registry')
    facts=load_components(); rates=get_fred()
    outputs=build(fin,kpis,facts,rates)
    for (filename,fields),rows in zip(FIELDS.items(),outputs):
        write_csv(OUT/filename,rows,fields)
    update_provenance(facts, outputs, registry)
    return outputs


def update_provenance(facts, outputs, existing):
    """Keep source facts and calculated cells visible in the approved registry."""
    current={(r['variable'],r['period']):r for r in existing if not r['notes'].startswith('Phase 3 ')}
    prior={(r['variable'],r['period']):r for r in existing}
    first_date='2026-09-29'
    calculations={
        'average_funded_customers_m':'(prior quarter-end + current quarter-end funded customers) / 2',
        'customer_assets_b':'coalesce reported Total AUC / Total Platform Assets with scope flag',
        'revenue_per_avg_customer_usd':'revenue_m / average_funded_customers_m',
        'transaction_revenue_per_avg_customer_usd':'transaction_revenue_m / average_funded_customers_m',
        'derived_arpu_usd_annualized':'4 × quarterly revenue_m / average_funded_customers_m',
        'arpu_difference_usd':'derived annualized ARPU less reported quarterly annualized ARPU',
        'assets_per_customer_usd':'1000 × customer_assets_b / funded_customers_m',
        'net_deposits_per_avg_customer_usd':'1000 × net_deposits_b / average_funded_customers_m',
        'options_revenue_per_contract_usd':'options_revenue_m / options_contracts_m',
        'crypto_revenue_per_notional_bps':'10 × crypto_revenue_m / crypto_notional_b',
        'equity_revenue_per_notional_bps':'10 × equities_revenue_m / equity_notional_b',
        'event_revenue_per_contract_usd':'event_contracts_revenue_m / (1000 × event_contracts_b)',
        'operating_margin_pct':'100 × operating_income_m / revenue_m',
        'adjusted_ebitda_margin_pct':'100 × adjusted_ebitda_m / revenue_m',
        'interest_asset_implied_yield_pct':'400 × quarterly interest_asset_revenue_m / interest_asset_avg_balance_m',
        'interest_asset_balance_effect_m':'change in average interest assets × prior period revenue / prior average assets',
        'interest_asset_yield_effect_m':'current average assets × change in quarterly realized revenue yield',
        'fed_funds_quarter_average_pct':'arithmetic average of daily FRED DFF observations in quarter',
        'market_activity_m':'options + crypto + equities + separately disclosed event-contract revenue',
        'interest_balance_m':'reported net interest revenue',
        'disclosed_recurring_m':'separately disclosed Gold subscription revenue only',
        'unclassified_m':'total revenue less market, interest and disclosed Gold',
        'incremental_operating_margin_yoy_pct':'100 × YoY change in GAAP operating income / YoY change in revenue',
        'incremental_adjusted_ebitda_margin_yoy_pct':'100 × YoY change in adjusted EBITDA / YoY change in revenue',
        'customer_scale_effect_m':'(C1−C0) × A0 × M0 for comparable products',
        'activity_effect_m':'C1 × (A1−A0) × M0 for comparable products',
        'monetization_effect_m':'C1 × A1 × (M1−M0) for comparable products',
        'mix_residual_effect_m':'reported transaction change less comparable customer/activity/monetization effects',
    }
    for (period, metric), fact in sorted(facts.items()):
        key=(metric,period)
        current[key]={'variable':metric,'value':fact['value'],'period':period,
                      'classification':fact['classification'],'source_name':fact['table_reference'],
                      'source_url':fact['source_url'],
                      'date_retrieved':prior.get(key,{}).get('date_retrieved',first_date),
                      'calculation':fact['calculation'],
                      'notes':('Phase 3 component fact; '+fact['notes']+' '+('accession '+fact['accession'] if fact['accession'] else '')).strip()}
    for filename,rows in zip(FIELDS,outputs):
        if filename=='forecast_driver_summary.csv':
            continue
        for row in rows:
            period=row.get('period') or row.get('comparison')
            for metric,value in row.items():
                if metric in ('period','comparison') or value in ('',None):
                    continue
                if (metric,period) in current and not metric.startswith('analysis.'):
                    continue
                try:
                    float(value)
                except (ValueError,TypeError):
                    continue
                variable='analysis.'+filename[:-4]+'.'+metric
                key=(variable,period)
                url=(FRED_URL if metric=='fed_funds_quarter_average_pct' else
                     'https://www.sec.gov/Archives/edgar/data/1783879/000178387926000114/hood-20260630.htm' if metric.startswith(('interest_asset_','margin_avg_','margin_interest_','cash_deposit_','cash_sweep_avg_','cash_sweep_interest_','credit_card_')) else
                     'https://investors.robinhood.com/financials/quarterly-results')
                current[key]={'variable':variable,'value':value,'period':period,
                              'classification':'DERIVED',
                              'source_name':'Phase 3 calculation from Robinhood historical data',
                              'source_url':url,
                              'date_retrieved':prior.get(key,{}).get('date_retrieved',first_date),
                              'calculation':calculations.get(metric,'See HISTORICAL_ANALYSIS.md methodology and source component facts'),
                              'notes':'Phase 3 derived analysis cell; source table '+filename+'.'}
    fields=['variable','value','period','classification','source_name','source_url','date_retrieved','calculation','notes']
    write_csv(ROOT/'data/source_registry.csv',list(current.values()),fields)
    dictionary=read_csv(ROOT/'data/data_dictionary.csv')
    dictionary=[r for r in dictionary if not r['description'].startswith('Phase 3 ')]
    known={r['metric'] for r in dictionary}
    for filename,columns in FIELDS.items():
        for metric in columns:
            if metric in known or metric in ('period','comparison'):
                continue
            unit=('millions of customers' if metric=='average_funded_customers_m' else
                  'USD per funded customer annualized' if metric=='derived_arpu_usd_annualized' else
                  'USD millions' if metric.endswith('_m') else 'USD billions' if metric.endswith('_b') else
                  'percent' if metric.endswith('_pct') else 'USD per customer/contract' if metric.endswith('_usd') else
                  'basis points' if metric.endswith('_bps') else 'text or ratio')
            stock_or_flow=('stock' if metric=='customer_assets_b' else
                           'average stock' if metric=='average_funded_customers_m' else
                           'ratio' if metric.endswith(('_pct','_bps','_usd','_annualized')) else
                           'flow' if metric.endswith('_m') else 'analytical label')
            dictionary.append({'metric':metric,'description':'Phase 3 '+metric.replace('_',' '),
                               'unit':unit,'frequency':'quarterly or comparison','stock_or_flow':stock_or_flow,
                               'quarterly_aggregation':'see HISTORICAL_ANALYSIS.md',
                               'definition_changes':'See STRUCTURAL_BREAKS.md; null when source or comparable denominator is absent.'})
            known.add(metric)
    for (_,metric),fact in facts.items():
        if metric in known:
            continue
        kind=('average stock' if metric.endswith('_avg_balance_m') else
              'stock' if metric=='funded_customers_opening_m' else 'flow')
        dictionary.append({'metric':metric,'description':'Phase 3 disclosed '+metric.replace('_',' '),
                           'unit':fact['unit'],'frequency':'quarterly','stock_or_flow':kind,
                           'quarterly_aggregation':'reported quarter or disclosed YTD/FY subtraction',
                           'definition_changes':'See source fact notes and STRUCTURAL_BREAKS.md.'})
        known.add(metric)
    write_csv(ROOT/'data/data_dictionary.csv',dictionary,list(dictionary[0]))
    manifest_path=ROOT/'data/source_manifest.csv'
    manifest=[r for r in read_csv(manifest_path) if r['source_id'] not in ('phase3_disclosed_components','fred_dff')]
    component_path=ROOT/'data/disclosed_components.csv'
    for source_id,source_type,period,url,path,notes in [
        ('phase3_disclosed_components','curated_primary_filing_facts','through_2026Q2',
         '',component_path,
         'Each row has its exact company source URL and filing/table reference.'),
        ('fred_dff','external_rate_context','2023Q1-2026Q2',FRED_URL,FRED_CACHE,
         'Daily effective federal funds rate; quarterly arithmetic average; not Robinhood realized yield.')]:
        previous=next((r for r in read_csv(manifest_path) if r['source_id']==source_id),None)
        manifest.append({'source_id':source_id,'source_type':source_type,'period':period,
                         'canonical_url':url,'retrieval_url':url,'accession':'',
                         'cache_filename':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                         'status':'committed' if source_id=='phase3_disclosed_components' else 'cached',
                         'retrieved_at':previous['retrieved_at'] if previous else first_date,'notes':notes})
    write_csv(manifest_path,manifest,list(manifest[0]))


if __name__=='__main__':
    run()
