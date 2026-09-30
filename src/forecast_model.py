"""Phase 4 operating forecast. All future numeric inputs are emitted as assumptions."""
from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path

from .config import ROOT

Q2 = 'https://www.sec.gov/Archives/edgar/data/1783879/000178387926000114/hood-20260630.htm'
Q2_RELEASE = 'https://investors.robinhood.com/news-releases/news-release-details/robinhood-reports-second-quarter-2026-results'
JULY = 'https://investors.robinhood.com/news-releases/news-release-details/robinhood-markets-inc-reports-july-2026-operating-data'
AUGUST = 'https://investors.robinhood.com/news-releases/news-release-details/robinhood-markets-inc-reports-august-2026-operating-data'
FED = 'https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm'
SCENARIOS = ('Base', 'Upside', 'Downside')
PERIODS = [f'{y}Q{q}' for y in range(2026, 2030) for q in range(1, 5) if (2026, 3) <= (y, q) <= (2029, 2)]
ASSUMPTION_FIELDS = ['driver', 'scenario', 'period', 'value', 'unit', 'classification', 'observation_status', 'historical_reference', 'methodology', 'source', 'notes']


def read_csv(path: Path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle))


def num(value):
    return None if value in (None, '') else float(value)


def median(values):
    return statistics.median(values)


def safe_div(a, b):
    return a / b if a is not None and b not in (None, 0) else None


def load_history():
    financial = read_csv(ROOT / 'data/processed/historical_financials_quarterly.csv')
    kpis = read_csv(ROOT / 'data/analysis/financial_kpis_quarterly.csv')
    monthly = {r['period']: r for r in read_csv(ROOT / 'data/processed/operating_kpis_monthly.csv')}
    components = {(r['period'], r['metric']): num(r['value']) for r in read_csv(ROOT / 'data/disclosed_components.csv')}
    if len(financial) != 14 or financial[-1]['period'] != '2026Q2' or len(kpis) != 14:
        raise ValueError('Phase 3 historical cutoff changed; inspect inputs before forecasting')
    if any(p not in monthly for p in ('2026-06', '2026-07', '2026-08')):
        raise ValueError('Missing June–August 2026 monthly operating observations')
    return financial, kpis, monthly, components


def observed_rows(monthly):
    """Monthly source facts live in the assumption audit, never in Q3 actuals."""
    rows = []
    channel = {'2026-07': (4.3, 6.6), '2026-08': (7.4, 10.1)}
    fields = ['funded_customers_m', 'platform_assets_b', 'net_deposits_b', 'options_contracts_m',
              'equity_notional_b', 'crypto_notional_b', 'event_contracts_b', 'margin_book_b',
              'cash_deposits_b', 'cash_sweep_b']
    for period in ('2026-07', '2026-08'):
        source = JULY if period.endswith('07') else AUGUST
        for field in fields:
            value = num(monthly[period][field])
            if value is None:
                raise ValueError(f'Missing nowcast source fact {period} {field}')
            rows.append(dict(driver=field, scenario='ALL', period=period, value=value,
                             unit='millions' if field in ('funded_customers_m', 'options_contracts_m') else 'billions',
                             classification='REPORTED', observation_status='PARTIAL-QUARTER OBSERVATION',
                             historical_reference=period, methodology='Company monthly operating release',
                             source=source, notes='Not a completed quarterly financial actual'))
        app, bitstamp = channel[period]
        if not math.isclose(app + bitstamp, num(monthly[period]['crypto_notional_b']), abs_tol=.01):
            raise ValueError(f'Crypto channel volumes do not tie for {period}')
        for field, value in (('crypto_app_notional_b', app), ('crypto_bitstamp_notional_b', bitstamp)):
            rows.append(dict(driver=field, scenario='ALL', period=period, value=value, unit='USD billions',
                             classification='REPORTED', observation_status='PARTIAL-QUARTER OBSERVATION',
                             historical_reference=period, methodology='Reported channel volume',
                             source=source, notes='Channel revenue is not disclosed'))
    return rows


def policy_path(period):
    """September 2026 SEP median year-end path, interpolated as analyst context."""
    year, quarter = int(period[:4]), int(period[-1])
    if period == '2026Q3':
        return 3.875  # September 16 target-range midpoint, external context only.
    anchors = {2026: 4.1, 2027: 3.9, 2028: 3.6, 2029: 3.2}
    return anchors[year - 1] + (anchors[year] - anchors[year - 1]) * quarter / 4 if year > 2026 else anchors[2026]


def build_assumptions(history):
    financial, kpis, monthly, components = history
    rows = observed_rows(monthly)
    values = {}
    recent = {r['period']: r for r in kpis}
    mon = {r['period']: r for r in read_csv(ROOT / 'data/analysis/monetization_metrics_quarterly.csv')}
    fin = {r['period']: r for r in financial}
    avg = lambda p: num(recent[p]['average_funded_customers_m'])
    options_recent = [num(recent[p]['options_contracts_m']) / avg(p) for p in ('2025Q4', '2026Q1', '2026Q2')]
    equity_recent = [num(recent[p]['equity_notional_b']) / avg(p) for p in ('2025Q4', '2026Q1', '2026Q2')]
    option_price = median([num(mon[p]['options_revenue_per_contract_usd']) for p in ('2025Q4', '2026Q1', '2026Q2')])
    equity_bps = median([num(mon[p]['equity_revenue_per_notional_bps']) for p in ('2025Q4', '2026Q1', '2026Q2')])
    crypto_bps = median([num(mon[p]['crypto_revenue_per_notional_bps']) for p in ('2025Q4', '2026Q1', '2026Q2')])
    event_price = median([num(mon[p]['event_revenue_per_contract_usd']) for p in ('2026Q1', '2026Q2')])
    gold_unit = median([50 / ((4.2 + 4.3) / 2), 54 / ((4.3 + 4.8) / 2)])
    other_txn_per_customer = median([43 / avg('2026Q1'), 49 / avg('2026Q2')])
    yields = {name: 4 * components[('2026Q2', f'{name}_interest_revenue_m')] /
              components[('2026Q2', f'{name}_avg_balance_m')] * 100
              for name in ('margin', 'cash_deposit', 'cash_sweep', 'credit_card')}
    if not math.isclose(sum(components[('2026Q2', f'{name}_interest_revenue_m')] for name in yields), 387):
        raise ValueError('Q2 interest component calibration no longer ties')
    # Full-year 2025 proxy disclosure ($63m) less Q1–Q3 (9, 36, 7).
    proxy = {1: 8.0, 2: 42.0, 3: 7.0, 4: 11.0}
    notes = {
        'net_customer_additions_m': ('2025Q3–2026Q1 net additions 0.3/0.2/0.4m; exclude WonderFi-era 2026Q2', 'Quarter-end roll-forward', Q2_RELEASE),
        'net_deposits_b': ('2025Q2–2026Q2 deposits; July/August 2026 partial', 'Quarterly flow, not asset appreciation', AUGUST),
        'asset_value_change_pct': ('Acquisition and Trump Account scope breaks prevent clean return inference', 'Quarterly assumption applied to beginning assets', AUGUST),
        'options_per_customer': ('2025Q4–2026Q2 contracts / average funded customers', 'Aggregate funded-customer activity proxy', 'data/analysis/monetization_metrics_quarterly.csv'),
        'option_revenue_per_contract_usd': ('2025Q4–2026Q2 reported options revenue/contracts', 'Realized product monetization', 'data/analysis/monetization_metrics_quarterly.csv'),
        'equity_notional_per_customer_b': ('2025Q4–2026Q2 volume / average funded customers', 'Aggregate funded-customer activity proxy', 'data/analysis/monetization_metrics_quarterly.csv'),
        'equity_monetization_bps': ('2025Q4–2026Q2 realized bps', 'Volume × bps / 10', 'data/analysis/monetization_metrics_quarterly.csv'),
        'crypto_app_per_customer_b': ('2026Q2 App volume $18b; July/August App monthly volumes', 'App volume / average funded customers; no channel revenue inference', AUGUST),
        'crypto_bitstamp_per_customer_b': ('2026Q2 Bitstamp volume $22b; July/August Bitstamp monthly volumes', 'Exchange volume / average funded customers; no channel revenue inference', AUGUST),
        'crypto_blended_bps': ('2025Q4–2026Q2 combined-scope realized bps', 'Blended App/Bitstamp/WonderFi monetization', 'data/analysis/monetization_metrics_quarterly.csv'),
        'event_contracts_per_customer_b': ('2026Q1–Q2 event units; July/August 2026 partial', 'Short-history aggregate proxy; not a mature product forecast', AUGUST),
        'event_revenue_per_contract_usd': ('2026Q1–Q2 matched event revenue/units', 'Contracts × realized dollars per contract', Q2),
        'other_transaction_per_customer_usd': ('2026Q1–Q2 separately disclosed other transaction revenue', 'Average customers × dollars/customer', Q2),
        'gold_net_subscriber_additions_m': ('2025Q4–2026Q2 quarter-end Gold subscribers 4.2/4.3/4.8m', 'Quarter-end subscriber roll-forward', Q2_RELEASE),
        'gold_revenue_per_avg_subscriber_usd': ('2026Q1–Q2 Gold revenue / average subscribers', 'Average subscribers × realized quarterly dollars', Q2),
        'proxy_revenue_m': ('2025 quarterly proxy 9/36/7/11m; 2026Q1/Q2 8/42m', 'Seasonal disclosed source; flat nominal base',
                            'https://www.sec.gov/Archives/edgar/data/1783879/000178387926000029/hood-20251231.htm; '
                            'https://www.sec.gov/Archives/edgar/data/1783879/000178387925000310/hood-20250930.htm; '+Q2),
        'residual_other_revenue_m': ('2025Q4 and 2026Q1 non-Gold/non-proxy 35/27m; 2026Q2 47m', 'Explicit nonrecurring/other analyst line', Q2),
        'policy_rate_context_pct': ('September 2026 FOMC SEP and target range', 'External rate path; not Robinhood realized yield', FED),
        'cash_capture_ratio': ('Cash/deposits + sweep versus recent net deposit growth; affected by internal transfers', 'Analyst share of deposits added to cash pool', AUGUST),
        'cash_deposit_share': ('August 2026 cash/deposits $19.6b and sweep $31.2b', 'Share of modeled cash pool in cash/deposits', AUGUST),
        'margin_balance_per_customer_b': ('August 2026 margin book $21.5b / 28.6m customers', 'Period-end margin stock proxy', AUGUST),
        'credit_balance_growth_pct': ('2026Q1–Q2 disclosed average credit balances $1.084b/$1.347b', 'Quarterly growth in modeled average credit balance', Q2),
        'interest_remainder_m': ('2026Q2 NIR $389m less disclosed interest-asset revenue $387m', 'Securities lending/financing/other net remainder', Q2),
        'credit_provision_pct': ('2026Q1/Q2 credit provision $36m/$56m vs credit balances', 'Proxy loss provision per average credit balance; not disclosed card loss rate', Q2),
    }
    def add(sc, period, key, value, unit, reference=None, method=None, source=None, note='',
            classification='ASSUMPTION', observation_status='FORECAST'):
        if value is None or not math.isfinite(value):
            raise ValueError(f'Invalid forecast assumption {sc} {period} {key}')
        values.setdefault(sc, {}).setdefault(period, {})[key] = value
        ref, meth, src = notes.get(key, ('Q2 2026 company disclosures and Phase 3 history', 'Explicit analyst operating assumption', Q2_RELEASE))
        rows.append(dict(driver=key, scenario=sc, period=period, value=value, unit=unit,
                         classification=classification, observation_status=observation_status,
                         historical_reference=reference or ref, methodology=method or meth,
                         source=source or src, notes=note))
    for sc in SCENARIOS:
        for i, period in enumerate(PERIODS):
            q = int(period[-1]); q3 = i == 0
            adds = {'Base': .3, 'Upside': .45, 'Downside': .2 if q3 else .15}[sc]
            deposits = {'Base': 17.7, 'Upside': 21.7, 'Downside': 13.8}[sc]
            market = {'Base': 0., 'Upside': .01, 'Downside': -.01}[sc]
            if not q3:
                add(sc, period, 'net_customer_additions_m', adds, 'millions')
                add(sc, period, 'net_deposits_b', deposits, 'USD billions')
                add(sc, period, 'asset_value_change_pct', market, 'fraction')
            add(sc, period, 'acquired_assets_b', 0., 'USD billions', note='No future acquisitions assumed')
            if not q3:
                add(sc, period, 'other_asset_change_b', 0., 'USD billions')
            # Q3 flow volumes and deposits use the separate September monthly assumptions below.
            if q3:
                add(sc, '2026-09', 'sept_net_customer_additions_m', adds - .2, 'millions',
                    reference='July/August each added approximately 0.1m; rounded reports',source=AUGUST)
                add(sc, '2026-09', 'sept_net_deposits_b', {'Base': 4.8, 'Upside': 5.6, 'Downside': 4.0}[sc], 'USD billions',
                    reference='July $5.6b, August $4.0b',source=AUGUST)
                add(sc, '2026-09', 'sept_asset_value_change_pct', market, 'fraction',source=AUGUST,
                    note='Analyst market/value scenario, not a September observation')
                for key, jul, aug in [('sept_options_contracts_m',324.2,292.5),('sept_equity_notional_b',332.8,335.4),
                                      ('sept_crypto_app_notional_b',4.3,7.4),('sept_crypto_bitstamp_notional_b',6.6,10.1),
                                      ('sept_event_contracts_b',6.1,4.7)]:
                    multiplier={'Base':1.,'Upside':1.1,'Downside':.9}[sc]
                    add(sc, '2026-09', key, (jul+aug)/2*multiplier,
                        'millions' if key.endswith('_m') else 'billions',
                        reference=f'July {jul}; August {aug}', method='Two-month mean × scenario factor', source=AUGUST)
                add(sc, '2026-09', 'sept_margin_balance_b', {'Base':21.5,'Upside':21.9,'Downside':21.1}[sc], 'USD billions',
                    reference='August reported $21.5b', source=AUGUST)
                add(sc,period,'net_customer_additions_m',adds,'millions',
                    reference='2026Q2 end 28.4m; August end 28.6m; September modeled',
                    method='July/August observed change + September assumption',source=AUGUST,
                    classification='DERIVED')
                add(sc,period,'net_deposits_b',9.6+{'Base':4.8,'Upside':5.6,'Downside':4.0}[sc], 'USD billions',
                    reference='July $5.6b + August $4.0b + September modeled',
                    method='Two observed monthly flows + September assumption',source=AUGUST,
                    classification='DERIVED')
                add(sc,period,'other_asset_change_b',5.4,'USD billions',
                    reference='August assets $383.7b − June assets $368.7b − July/August deposits $9.6b',
                    method='Observed asset/other residual; market and Trump Account effect inseparable',source=AUGUST,
                    classification='DERIVED',observation_status='PARTIAL-QUARTER OBSERVATION')
            # Later-quarter activity is calibrated to comparable Q4/Q1/Q2 and the Q3 partial pace.
            option_anchor=median(options_recent+[ (324.2+292.5+(324.2+292.5)/2)/28.55 ])
            equity_anchor=median(equity_recent+[ (332.8+335.4+(332.8+335.4)/2)/28.55 ])
            app_anchor=(4.3+7.4+(4.3+7.4)/2)/28.55
            bit_anchor=(6.6+10.1+(6.6+10.1)/2)/28.55
            event_anchor=(6.1+4.7+(6.1+4.7)/2)/28.55
            activity_mult={'Base':1.,'Upside':1.15,'Downside':.8}[sc]
            add(sc,period,'options_per_customer',option_anchor*activity_mult,'contracts per funded customer')
            add(sc,period,'option_revenue_per_contract_usd',option_price*({'Downside':.95}.get(sc,1.)),'USD per contract')
            add(sc,period,'equity_notional_per_customer_b',equity_anchor*activity_mult,'USD billions per million customers')
            add(sc,period,'equity_monetization_bps',equity_bps*({'Downside':.95}.get(sc,1.)),'basis points')
            add(sc,period,'crypto_app_per_customer_b',app_anchor*({'Base':1.,'Upside':1.25,'Downside':.75}[sc]),'USD billions per million customers')
            add(sc,period,'crypto_bitstamp_per_customer_b',bit_anchor*({'Base':1.,'Upside':1.25,'Downside':.75}[sc]),'USD billions per million customers')
            add(sc,period,'crypto_blended_bps',crypto_bps*({'Downside':.85}.get(sc,1.)),'basis points')
            add(sc,period,'event_contracts_per_customer_b',event_anchor*({'Base':1.,'Upside':1.15,'Downside':.8}[sc]),'billions of contracts per million customers')
            add(sc,period,'event_revenue_per_contract_usd',event_price*({'Downside':.95}.get(sc,1.)),'USD per contract')
            add(sc,period,'other_transaction_per_customer_usd',other_txn_per_customer,'USD per funded customer')
            add(sc,period,'gold_net_subscriber_additions_m',{'Base':.2,'Upside':.3,'Downside':.1}[sc],'millions')
            add(sc,period,'gold_revenue_per_avg_subscriber_usd',gold_unit*({'Downside':.95}.get(sc,1.)),'USD per subscriber per quarter')
            add(sc,period,'proxy_revenue_m',proxy[q]*({'Base':1.,'Upside':1.05,'Downside':.9}[sc]),'USD millions')
            add(sc,period,'residual_other_revenue_m',{'Base':35.,'Upside':40.,'Downside':27.}[sc],'USD millions')
            rate=policy_path(period)-({'Downside':min(1.,.25*(i+1))}.get(sc,0.))
            add(sc,period,'policy_rate_context_pct',rate,'percent',note='FOMC median is external policy context; not a realized company yield')
            add(sc,period,'cash_capture_ratio',{'Base':.25,'Upside':.3,'Downside':.15}[sc],'fraction')
            add(sc,period,'cash_deposit_share',19.6/(19.6+31.2),'fraction',note='Holds August post-transfer split; model risk')
            add(sc,period,'margin_balance_per_customer_b',(21.5/28.6)*({'Base':1.,'Upside':1.08,'Downside':.9}[sc]),'USD billions per million customers')
            credit_growth=max({'Base':.05,'Upside':.08,'Downside':.03}[sc],
                              {'Base':.15,'Upside':.20,'Downside':.08}[sc]-.01*i)
            add(sc,period,'credit_balance_growth_pct',credit_growth,'fraction')
            add(sc,period,'interest_remainder_m',{'Base':2.,'Upside':2.,'Downside':-10.}[sc],'USD millions',
                note='Low-confidence securities lending, debt financing and other net line')
            # The company excludes Cash Sweep from its short-term policy-rate
            # sensitivity because it can manage the spread paid to customers.
            for name, pass_through in [('margin',.85),('cash_deposit',.30),('cash_sweep',0.),('credit_card',0.)]:
                add(sc,period,f'{name}_rate_pass_through',pass_through,'fraction',
                    reference='2025Q2/2026Q2 matched balance/yield disclosures; cash-sweep definition break',
                    note='Analyst rate sensitivity; not a fitted causal coefficient')
                yield_pct=max(0., yields[name]+pass_through*(rate-num(recent['2026Q2']['fed_funds_quarter_average_pct'])))
                add(sc,period,f'{name}_realized_yield_pct',yield_pct,'percent',
                    reference=f'2026Q2 annualized realized {name} yield {yields[name]:.3f}%',
                    method='Q2 realized yield + explicit pass-through × external rate change')
            add(sc,period,'credit_provision_pct',{'Base':.0375,'Upside':.033,'Downside':.042}[sc],'fraction per quarter',
                note='Company does not disclose this as a pure card loss rate')
            # Category baselines include a visible H2 2026 investment step; guidance remains a check.
            add(sc,period,'brokerage_fixed_m',31.,'USD millions',reference='2026Q2 brokerage $62m',note='Half Q2 cost treated as fixed-like analyst assumption')
            add(sc,period,'brokerage_variable_m',31.,'USD millions',reference='2026Q2 brokerage $62m',note='Scaled by disclosed trading activity basket')
            for product, weight in [('options',.40),('equity',.25),('crypto',.20),('event',.15)]:
                add(sc,period,f'brokerage_{product}_weight',weight,'fraction',
                    reference='2026Q2 reported product volume, expense category not product-disaggregated',
                    note='Analyst activity-basket allocation; not a disclosed product cost split')
            add(sc,period,'technology_base_m',281.+max(i-1,0)*({'Base':3.,'Upside':5.,'Downside':2.}[sc]),'USD millions',
                reference='Q2 $256m; +$25m H2 investment allowance informed by 2026 adjusted expense outlook')
            add(sc,period,'operations_base_m',62.,'USD millions',reference='Q2 $57m; +$5m H2 operating investment allowance')
            add(sc,period,'operations_customer_variable_share',.4,'fraction',
                reference='2024–2025 operations expense grew 16% amid customer/account growth',
                note='Semi-variable analyst cost split, not a measured elasticity')
            add(sc,period,'marketing_base_m',129.,'USD millions',reference='Q2 $104m; +$25m H2 growth investment allowance')
            add(sc,period,'marketing_reference_additions_m',.3,'millions',
                reference='2025Q3–2026Q1 comparable net-addition median',
                note='Explicit denominator for the modeled marketing response')
            add(sc,period,'marketing_additions_variable_share',.2,'fraction',
                reference='2024–2025 marketing expense grew 47%; customer acquisition mix undisclosed',
                note='Management-controlled spend; deliberately flexes less than revenue')
            add(sc,period,'general_base_m',191.+max(i-1,0)*({'Base':2.,'Upside':3.,'Downside':1.5}[sc]),'USD millions',
                reference='Q2 $199m less $23m restructuring; +$15m H2 operating allowance')
            add(sc,period,'sbc_adjustment_m',80.+i*({'Base':1.,'Upside':2.,'Downside':1.}[sc]),'USD millions',
                reference='2025Q4 $76m; 2026Q1 $73m; Q2 $105m including unusual costs')
            add(sc,period,'depreciation_adjustment_m',23.+.5*i,'USD millions',reference='2026Q2 reported $23m')
            add(sc,period,'debt_interest_adjustment_m',10.,'USD millions',reference='2026Q2 reported $10m',
                note='Interest expense is also contained in forecast net-interest remainder; addback only for EBITDA')
            add(sc,period,'nonoperating_income_m',0.,'USD millions',reference='2026Q2 $129m unusual gains; 2026Q1 $0m')
            add(sc,period,'effective_tax_rate_pct',20.,'percent',reference='2026Q1/Q2 reported taxes and pretax income',
                note='Illustrative normalized rate; no tax benefit modeled on losses')
    return rows, values


def actual_rows(history):
    financial, kpis, _, components = history
    by_kpi = {r['period']: r for r in kpis}
    rows = []
    for source in financial:
        p = source['period']; k = by_kpi[p]
        row = {'period': p, 'scenario': 'ACTUAL', 'status': 'ACTUAL', 'nowcast': False}
        for column, value in source.items():
            row[column] = value if column == 'period' else num(value)
        for column in ('funded_customers_m','average_funded_customers_m','customer_assets_b','net_deposits_b',
                       'options_contracts_m','crypto_notional_b','equity_notional_b','event_contracts_b',
                       'gold_subscribers_m','margin_book_b','cash_deposits_b','cash_sweep_b',
                       'reported_arpu_usd_annualized','fed_funds_quarter_average_pct','interest_asset_avg_balance_m',
                       'interest_asset_revenue_m','margin_avg_balance_m','cash_deposit_avg_balance_m',
                       'cash_sweep_avg_balance_m','credit_card_avg_balance_m'):
            row[column] = num(k[column])
        row['platform_assets_b'] = num(k['customer_assets_b'])
        row['event_contracts_revenue_m'] = components.get((p,'event_contracts_revenue_m')) or row['event_contracts_revenue_m']
        row['gold_subscription_revenue_m'] = components.get((p,'gold_subscription_revenue_m'))
        row['market_activity_revenue_m'] = sum(row[x] or 0 for x in ('options_revenue_m','crypto_revenue_m','equities_revenue_m','event_contracts_revenue_m'))
        row['interest_balance_revenue_m'] = row['net_interest_revenue_m']
        row['disclosed_recurring_revenue_m'] = row['gold_subscription_revenue_m']
        row['unclassified_revenue_m'] = row['revenue_m']-row['market_activity_revenue_m']-row['interest_balance_revenue_m']-(row['disclosed_recurring_revenue_m'] or 0)
        row['operating_margin_pct'] = 100*row['operating_income_m']/row['revenue_m']
        row['adjusted_ebitda_margin_pct'] = 100*row['adjusted_ebitda_m']/row['revenue_m']
        row['derived_arpu_usd_annualized'] = num(k['derived_arpu_usd_annualized'])
        row['revenue_per_avg_customer_usd'] = num(k['revenue_per_avg_customer_usd'])
        row['transaction_revenue_per_avg_customer_usd'] = num(k['transaction_revenue_per_avg_customer_usd'])
        row['assets_per_customer_usd'] = num(k['assets_per_customer_usd'])
        row['adjusted_opex_and_sbc_m'] = None
        rows.append(row)
    return rows


def project(history, assumptions, scenario, shocks=None):
    """Run one isolated scenario; shocks never change stored base assumptions."""
    _, kpis, monthly, components = history
    shocks = shocks or {}
    vals = assumptions[scenario]
    previous = {'funded_customers_m':28.4,'platform_assets_b':368.7,'gold_subscribers_m':4.8,
                'margin_book_b':21.6,'cash_deposits_b':18.7,'cash_sweep_b':29.7,
                'credit_card_avg_balance_b':1.347}
    results = []
    def a(period, name):
        value = vals[period][name]
        # A sensitivity is a multiplicative model-input shock, never a historical edit.
        return value*shocks.get(name,1.)
    for i, p in enumerate(PERIODS):
        q3 = i == 0
        start = previous
        if q3:
            sep='2026-09'
            customers = num(monthly['2026-08']['funded_customers_m']) + a(sep,'sept_net_customer_additions_m')
            net_adds = customers-start['funded_customers_m']
            deposits = sum(num(monthly[m]['net_deposits_b']) for m in ('2026-07','2026-08')) + a(sep,'sept_net_deposits_b')
            observed_residual = (num(monthly['2026-08']['platform_assets_b'])-start['platform_assets_b']
                                 -sum(num(monthly[m]['net_deposits_b']) for m in ('2026-07','2026-08')))
            market_change = num(monthly['2026-08']['platform_assets_b'])*a(sep,'sept_asset_value_change_pct')
            other_asset_change = observed_residual
            assets = start['platform_assets_b']+deposits+market_change+other_asset_change
            options = sum(num(monthly[m]['options_contracts_m']) for m in ('2026-07','2026-08'))+a(sep,'sept_options_contracts_m')
            equities = sum(num(monthly[m]['equity_notional_b']) for m in ('2026-07','2026-08'))+a(sep,'sept_equity_notional_b')
            app = 4.3+7.4+a(sep,'sept_crypto_app_notional_b')
            bitstamp = 6.6+10.1+a(sep,'sept_crypto_bitstamp_notional_b')
            events = sum(num(monthly[m]['event_contracts_b']) for m in ('2026-07','2026-08'))+a(sep,'sept_event_contracts_b')
            margin_end=a(sep,'sept_margin_balance_b')
            cash_pool=19.6+31.2+a(sep,'sept_net_deposits_b')*a(p,'cash_capture_ratio')
            cash_end=cash_pool*a(p,'cash_deposit_share')
            sweep_end=cash_pool-cash_end
            avg_balance={
                'margin':statistics.mean([20.7,21.5,margin_end]),
                'cash_deposit':statistics.mean([19.5,19.6,cash_end]),
                'cash_sweep':statistics.mean([29.2,31.2,sweep_end]),
            }
        else:
            net_adds=a(p,'net_customer_additions_m')
            customers=start['funded_customers_m']+net_adds
            deposits=a(p,'net_deposits_b')
            market_change=start['platform_assets_b']*a(p,'asset_value_change_pct')
            other_asset_change=a(p,'other_asset_change_b')
            assets=start['platform_assets_b']+deposits+market_change+a(p,'acquired_assets_b')+other_asset_change
            avg_customers=(start['funded_customers_m']+customers)/2
            options=avg_customers*a(p,'options_per_customer')
            equities=avg_customers*a(p,'equity_notional_per_customer_b')
            app=avg_customers*a(p,'crypto_app_per_customer_b')
            bitstamp=avg_customers*a(p,'crypto_bitstamp_per_customer_b')
            events=avg_customers*a(p,'event_contracts_per_customer_b')
            margin_end=customers*a(p,'margin_balance_per_customer_b')
            cash_pool=start['cash_deposits_b']+start['cash_sweep_b']+deposits*a(p,'cash_capture_ratio')
            cash_end=cash_pool*a(p,'cash_deposit_share')
            sweep_end=cash_pool-cash_end
            avg_balance={
                'margin':(start['margin_book_b']+margin_end)/2,
                'cash_deposit':(start['cash_deposits_b']+cash_end)/2,
                'cash_sweep':(start['cash_sweep_b']+sweep_end)/2,
            }
        avg_customers=(start['funded_customers_m']+customers)/2
        credit_avg=start['credit_card_avg_balance_b']*(1+a(p,'credit_balance_growth_pct'))
        avg_balance['credit_card']=credit_avg
        if 'interest_balance_multiplier' in shocks:
            avg_balance={name:balance*shocks['interest_balance_multiplier'] for name,balance in avg_balance.items()}
        gold_end=start['gold_subscribers_m']+a(p,'gold_net_subscriber_additions_m')
        avg_gold=(start['gold_subscribers_m']+gold_end)/2
        crypto=app+bitstamp
        options_rev=options*a(p,'option_revenue_per_contract_usd')
        crypto_rev=crypto*a(p,'crypto_blended_bps')/10
        equity_rev=equities*a(p,'equity_monetization_bps')/10
        event_rev=events*1000*a(p,'event_revenue_per_contract_usd')
        other_txn=avg_customers*a(p,'other_transaction_per_customer_usd')
        txn=options_rev+crypto_rev+equity_rev+event_rev+other_txn
        interest_revs={name:avg_balance[name]*1000*max(0,a(p,f'{name}_realized_yield_pct')+
                         shocks.get('yield_shift_pct',0.)+
                         shocks.get('policy_shift_pct',0.)*a(p,f'{name}_rate_pass_through'))/100/4
                       for name in avg_balance}
        interest_assets=sum(interest_revs.values())
        nir=interest_assets+a(p,'interest_remainder_m')
        gold_rev=avg_gold*a(p,'gold_revenue_per_avg_subscriber_usd')
        proxy=a(p,'proxy_revenue_m')
        residual_other=a(p,'residual_other_revenue_m')
        other=gold_rev+proxy+residual_other
        revenue=txn+nir+other
        ratios={'options':options/773.9,'equity':equities/955.8,'crypto':crypto/40.4,'event':events/13.6}
        activity_index=sum(a(p,f'brokerage_{product}_weight')*ratio for product,ratio in ratios.items())
        brokerage=a(p,'brokerage_fixed_m')+a(p,'brokerage_variable_m')*activity_index
        tech=a(p,'technology_base_m')
        operations=a(p,'operations_base_m')*((1-a(p,'operations_customer_variable_share'))+
                                            a(p,'operations_customer_variable_share')*customers/28.4)
        provision=credit_avg*1000*a(p,'credit_provision_pct')
        marketing=a(p,'marketing_base_m')*((1-a(p,'marketing_additions_variable_share'))+
                                           a(p,'marketing_additions_variable_share')*net_adds/a(p,'marketing_reference_additions_m'))
        general=a(p,'general_base_m')
        expense=brokerage+tech+operations+provision+marketing+general
        operating_income=revenue-expense
        other_income=a(p,'nonoperating_income_m')
        pretax=operating_income+other_income
        tax=max(0,pretax)*a(p,'effective_tax_rate_pct')/100
        net_income=pretax-tax
        sbc=a(p,'sbc_adjustment_m'); depreciation=a(p,'depreciation_adjustment_m')
        debt_interest=a(p,'debt_interest_adjustment_m')
        adjusted_ebitda=net_income+tax+sbc+depreciation+debt_interest-other_income
        row=dict(period=p,scenario=scenario,status='FORECAST',nowcast=q3,
                 funded_customers_m=customers,net_customer_additions_m=net_adds,
                 average_funded_customers_m=avg_customers,platform_assets_b=assets,
                 net_deposits_b=deposits,market_asset_value_change_b=market_change,
                 acquired_assets_b=a(p,'acquired_assets_b'),other_asset_change_b=other_asset_change,
                 options_contracts_m=options,equity_notional_b=equities,crypto_app_notional_b=app,
                 crypto_bitstamp_notional_b=bitstamp,crypto_notional_b=crypto,event_contracts_b=events,
                 gold_subscribers_m=gold_end,margin_book_b=margin_end,cash_deposits_b=cash_end,
                 cash_sweep_b=sweep_end,credit_card_avg_balance_b=credit_avg,
                 options_revenue_m=options_rev,crypto_revenue_m=crypto_rev,equities_revenue_m=equity_rev,
                 event_contracts_revenue_m=event_rev,other_transaction_revenue_m=other_txn,
                 transaction_revenue_m=txn,margin_interest_revenue_m=interest_revs['margin'],
                 cash_deposit_interest_revenue_m=interest_revs['cash_deposit'],
                 cash_sweep_interest_revenue_m=interest_revs['cash_sweep'],
                 credit_card_interest_revenue_m=interest_revs['credit_card'],
                 interest_asset_revenue_m=interest_assets,interest_remainder_m=a(p,'interest_remainder_m'),
                 net_interest_revenue_m=nir,gold_subscription_revenue_m=gold_rev,proxy_revenue_m=proxy,
                 residual_other_revenue_m=residual_other,other_revenue_m=other,revenue_m=revenue,
                 market_activity_revenue_m=options_rev+crypto_rev+equity_rev+event_rev,
                 interest_balance_revenue_m=nir,disclosed_recurring_revenue_m=gold_rev,
                 unclassified_revenue_m=other_txn+proxy+residual_other,
                 brokerage_transaction_expense_m=brokerage,technology_development_expense_m=tech,
                 operations_expense_m=operations,credit_loss_expense_m=provision,
                 marketing_expense_m=marketing,general_administrative_expense_m=general,
                 operating_expense_m=expense,operating_income_m=operating_income,
                 other_income_m=other_income,pretax_income_m=pretax,income_tax_expense_m=tax,
                 net_income_m=net_income,sbc_adjustment_m=sbc,
                 depreciation_amortization_adjustment_m=depreciation,
                 interest_expense_adjustment_m=debt_interest,adjusted_ebitda_m=adjusted_ebitda,
                 adjusted_opex_and_sbc_m=expense-provision,
                 operating_margin_pct=100*operating_income/revenue,
                 adjusted_ebitda_margin_pct=100*adjusted_ebitda/revenue,
                 derived_arpu_usd_annualized=4*revenue/avg_customers,
                 revenue_per_avg_customer_usd=revenue/avg_customers,
                 transaction_revenue_per_avg_customer_usd=txn/avg_customers,
                 assets_per_customer_usd=1000*assets/customers,
                 policy_rate_context_pct=a(p,'policy_rate_context_pct')+shocks.get('policy_shift_pct',0.),
                 margin_avg_balance_m=avg_balance['margin']*1000,
                 cash_deposit_avg_balance_m=avg_balance['cash_deposit']*1000,
                 cash_sweep_avg_balance_m=avg_balance['cash_sweep']*1000,
                 credit_card_avg_balance_m=credit_avg*1000,
                 interest_asset_avg_balance_m=sum(avg_balance.values())*1000,
                 options_per_customer=options/avg_customers,
                 crypto_notional_per_customer_b=crypto/avg_customers,
                 equity_notional_per_customer_b=equities/avg_customers,
                 event_contracts_per_customer_b=events/avg_customers,
                 option_revenue_per_contract_usd=options_rev/options,
                 crypto_monetization_bps=crypto_rev/crypto*10,
                 equity_monetization_bps=equity_rev/equities*10,
                 event_revenue_per_contract_usd=event_rev/(events*1000))
        # The guidance comparison intentionally excludes credit provision but is not a GAAP plug.
        results.append(row)
        previous={'funded_customers_m':customers,'platform_assets_b':assets,'gold_subscribers_m':gold_end,
                  'margin_book_b':margin_end,'cash_deposits_b':cash_end,'cash_sweep_b':sweep_end,
                  'credit_card_avg_balance_b':credit_avg}
    return results
