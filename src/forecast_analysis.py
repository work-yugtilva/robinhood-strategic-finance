"""Summaries, exact bridges, and isolated shocks for the Phase 4 forecast."""
from __future__ import annotations

import math

from .forecast_model import PERIODS, SCENARIOS, project


FLOW_COLUMNS = ('revenue_m','transaction_revenue_m','net_interest_revenue_m','other_revenue_m',
                'options_revenue_m','crypto_revenue_m','equities_revenue_m','event_contracts_revenue_m',
                'operating_expense_m','operating_income_m','adjusted_ebitda_m','net_income_m',
                'market_activity_revenue_m','interest_balance_revenue_m',
                'disclosed_recurring_revenue_m','unclassified_revenue_m','net_deposits_b')


def annual(rows, label, periods):
    selected=[r for r in rows if r['period'] in periods]
    if len(selected)!=len(periods):
        raise ValueError(f'Incomplete annual window {label}')
    output={'scenario':selected[-1]['scenario'],'window':label,'actual_quarters':sum(r['status']=='ACTUAL' for r in selected),
            'forecast_quarters':sum(r['status']=='FORECAST' for r in selected)}
    for key in FLOW_COLUMNS:
        values=[r.get(key) for r in selected]
        output[key]=sum(values) if all(v is not None for v in values) else None
    for key in ('funded_customers_m','platform_assets_b','gold_subscribers_m'):
        output[key]=selected[-1].get(key)
    output['operating_margin_pct']=100*output['operating_income_m']/output['revenue_m']
    output['adjusted_ebitda_margin_pct']=100*output['adjusted_ebitda_m']/output['revenue_m']
    output['market_activity_pct']=100*output['market_activity_revenue_m']/output['revenue_m']
    output['interest_balance_pct']=100*output['interest_balance_revenue_m']/output['revenue_m']
    output['disclosed_recurring_pct']=100*output['disclosed_recurring_revenue_m']/output['revenue_m']
    output['unclassified_pct']=100*output['unclassified_revenue_m']/output['revenue_m']
    return output


def make_summaries(actual, scenarios):
    rows=[]
    for scenario in SCENARIOS:
        all_rows=actual+scenarios[scenario]
        for year in (2026,2027,2028):
            rows.append(annual(all_rows, str(year), [f'{year}Q{q}' for q in range(1,5)]))
        rows.append(annual(all_rows,'2029H1',['2029Q1','2029Q2']))
        run=annual(all_rows,'2029Q2_ANNUALIZED',['2029Q2'])
        for key in FLOW_COLUMNS:
            if run[key] is not None:
                run[key]*=4
        run['operating_margin_pct']=100*run['operating_income_m']/run['revenue_m']
        run['adjusted_ebitda_margin_pct']=100*run['adjusted_ebitda_m']/run['revenue_m']
        rows.append(run)
    return rows


def add_incremental(actual, forecasts):
    for scenario in SCENARIOS:
        timeline={r['period']:r for r in actual+forecasts[scenario]}
        for row in forecasts[scenario]:
            year=int(row['period'][:4]); q=row['period'][-2:]
            prior=timeline.get(f'{year-1}{q}')
            if prior is None:
                row['incremental_operating_margin_yoy_pct']=None
                row['incremental_adjusted_ebitda_margin_yoy_pct']=None
                continue
            delta=row['revenue_m']-prior['revenue_m']
            row['incremental_operating_margin_yoy_pct']=100*(row['operating_income_m']-prior['operating_income_m'])/delta if delta>50 else None
            row['incremental_adjusted_ebitda_margin_yoy_pct']=100*(row['adjusted_ebitda_m']-prior['adjusted_ebitda_m'])/delta if delta>50 else None
            row['incremental_margin_interpretation']='WEAK: revenue delta <= $50m or negative' if delta<=50 else 'MODELED: excludes certainty about future mix and charges'


def product_effect(old, new, revenue_key, volume_key):
    if any(r.get(key) is None for r in (old,new) for key in (revenue_key,volume_key,'average_funded_customers_m')):
        return None
    c0=old['average_funded_customers_m']; c1=new['average_funded_customers_m']
    v0=old[volume_key]; v1=new[volume_key]
    r0=old[revenue_key]; r1=new[revenue_key]
    if min(c0,c1,v0,v1)<=0:
        return None
    a0=v0/c0; a1=v1/c1; m0=r0/v0; m1=r1/v1
    return ((c1-c0)*a0*m0, c1*(a1-a0)*m0, c1*a1*(m1-m0))


def bridge_window(rows, start_year, end_year, scenario):
    start=[r for r in rows if r['period'].startswith(str(start_year))]
    end=[r for r in rows if r['period'].startswith(str(end_year))]
    if len(start)!=4 or len(end)!=4:
        raise ValueError('Bridge needs complete four-quarter years')
    def aggregate(group):
        x={'average_funded_customers_m':sum(r['average_funded_customers_m'] for r in group)/4}
        for key in ('revenue_m','other_revenue_m','net_interest_revenue_m','options_revenue_m','options_contracts_m',
                    'equities_revenue_m','equity_notional_b','crypto_revenue_m','crypto_notional_b',
                    'event_contracts_revenue_m','event_contracts_b','interest_asset_revenue_m'):
            vals=[r.get(key) for r in group]
            x[key]=sum(vals) if all(v is not None for v in vals) else None
        balances=[r.get('interest_asset_avg_balance_m') for r in group]
        x['interest_asset_avg_balance_m']=sum(balances)/4 if all(v is not None for v in balances) else None
        return x
    old=aggregate(start); new=aggregate(end)
    customer=activity=monetization=0.
    included=[]
    for product, rev, volume in [('options','options_revenue_m','options_contracts_m'),
                                  ('equities','equities_revenue_m','equity_notional_b'),
                                  ('crypto','crypto_revenue_m','crypto_notional_b'),
                                  ('event','event_contracts_revenue_m','event_contracts_b')]:
        if product=='crypto' and end_year in (2026,2027):
            continue  # Bitstamp/WonderFi scope transition in comparison base.
        if product=='event' and end_year==2026:
            continue  # 2025 full-year matched event units/revenue unavailable.
        effects=product_effect(old,new,rev,volume)
        if effects is None:
            continue
        customer+=effects[0]; activity+=effects[1]; monetization+=effects[2]
        included.append(product)
    balance=yield_effect=0.
    if old['interest_asset_avg_balance_m'] and new['interest_asset_avg_balance_m'] and old['interest_asset_revenue_m'] is not None and new['interest_asset_revenue_m'] is not None:
        b0=old['interest_asset_avg_balance_m']; b1=new['interest_asset_avg_balance_m']
        y0=old['interest_asset_revenue_m']/b0; y1=new['interest_asset_revenue_m']/b1
        balance=(b1-b0)*y0
        yield_effect=b1*(y1-y0)
    other=new['other_revenue_m']-old['other_revenue_m']
    change=new['revenue_m']-old['revenue_m']
    structural=change-customer-activity-monetization-balance-yield_effect-other
    return {'scenario':scenario,'comparison':f'{end_year} vs {start_year}',
            'start_revenue_m':old['revenue_m'],'end_revenue_m':new['revenue_m'],'change_m':change,
            'customer_scale_m':customer,'trading_activity_m':activity,'monetization_m':monetization,
            'net_interest_balance_m':balance,'yield_rate_m':yield_effect,
            'subscription_other_m':other,'structural_product_mix_m':structural,
            'bridge_total_m':sum((customer,activity,monetization,balance,yield_effect,other,structural)),
            'comparable_products':'; '.join(included),
            'scope_note':'2026 is Q1/Q2 actual plus Q3/Q4 forecast; crypto acquisition transition retained in residual' if end_year==2026 else
                         ('2026 WonderFi transition means crypto stays in residual' if end_year==2027 else 'Fully modeled forecast periods')}


def make_bridges(actual, scenarios):
    result=[]
    for sc in SCENARIOS:
        rows=actual+scenarios[sc]
        for a,b in ((2025,2026),(2026,2027),(2027,2028)):
            result.append(bridge_window(rows,a,b,sc))
    return result


SHOCKS = []
ACTIVITY_KEYS = {
    'options_activity': ('options_per_customer','sept_options_contracts_m'),
    'crypto_activity': ('crypto_app_per_customer_b','crypto_bitstamp_per_customer_b',
                        'sept_crypto_app_notional_b','sept_crypto_bitstamp_notional_b'),
    'equity_activity': ('equity_notional_per_customer_b','sept_equity_notional_b'),
    'event_activity': ('event_contracts_per_customer_b','sept_event_contracts_b'),
    'transaction_monetization': ('option_revenue_per_contract_usd','crypto_blended_bps',
                                 'equity_monetization_bps','event_revenue_per_contract_usd'),
}
for driver, keys in ACTIVITY_KEYS.items():
    for factor in (.8,.9,1.,1.1,1.2):
        label='Base' if factor==1 else f'{(factor-1)*100:+.0f}%'
        SHOCKS.append((driver,{key:factor for key in keys},label))
SHOCKS += [
    ('customer_additions', {'net_customer_additions_m':.75,'sept_net_customer_additions_m':.75}, '-25%'),
    ('customer_additions', {'net_customer_additions_m':1.25,'sept_net_customer_additions_m':1.25}, '+25%'),
    ('net_deposits', {'net_deposits_b':.75,'sept_net_deposits_b':.75}, '-25%'),
    ('net_deposits', {'net_deposits_b':1.25,'sept_net_deposits_b':1.25}, '+25%'),
    ('realized_yields', {'yield_shift_pct':-1.}, '-100bp'),
    ('realized_yields', {'yield_shift_pct':-.5}, '-50bp'),
    ('realized_yields', {'yield_shift_pct':.5}, '+50bp'),
    ('realized_yields', {'yield_shift_pct':1.}, '+100bp'),
    ('policy_rate_with_pass_through', {'policy_shift_pct':-1.}, '-100bp'),
    ('policy_rate_with_pass_through', {'policy_shift_pct':-.5}, '-50bp'),
    ('policy_rate_with_pass_through', {'policy_shift_pct':.5}, '+50bp'),
    ('policy_rate_with_pass_through', {'policy_shift_pct':1.}, '+100bp'),
    ('cash_capture', {'cash_capture_ratio':.5}, '-50%'),
    ('cash_capture', {'cash_capture_ratio':1.5}, '+50%'),
    ('margin_balance_intensity', {'margin_balance_per_customer_b':.8}, '-20%'),
    ('margin_balance_intensity', {'margin_balance_per_customer_b':1.2}, '+20%'),
    ('credit_balance_growth', {'credit_balance_growth_pct':.75}, '-25%'),
    ('credit_balance_growth', {'credit_balance_growth_pct':1.25}, '+25%'),
    ('credit_provision', {'credit_provision_pct':.8}, '-20%'),
    ('credit_provision', {'credit_provision_pct':1.2}, '+20%'),
    ('marketing', {'marketing_base_m':.9}, '-10%'),('marketing', {'marketing_base_m':1.1}, '+10%'),
    ('technology', {'technology_base_m':.9}, '-10%'),('technology', {'technology_base_m':1.1}, '+10%'),
    ('general_admin', {'general_base_m':.9}, '-10%'),('general_admin', {'general_base_m':1.1}, '+10%'),
]


def sensitivity_metrics(rows):
    y2027=[r for r in rows if r['period'].startswith('2027')]
    last=rows[-1]
    return {'2027_revenue_m':sum(r['revenue_m'] for r in y2027),
            '2027_operating_income_m':sum(r['operating_income_m'] for r in y2027),
            '2027_adjusted_ebitda_m':sum(r['adjusted_ebitda_m'] for r in y2027),
            '2029Q2_annualized_revenue_m':4*last['revenue_m']}


def make_sensitivities(history, assumptions, base):
    baseline=sensitivity_metrics(base)
    rows=[]
    def record(kind, driver, shock_label, shocks, axis_x='', axis_y=''):
        forecast=project(history,assumptions,'Base',shocks)
        outcome=sensitivity_metrics(forecast)
        y2027=[r for r in forecast if r['period'].startswith('2027')]
        for metric,value in outcome.items():
            rows.append({'kind':kind,'driver':driver,'shock':shock_label,'axis_x':axis_x,'axis_y':axis_y,
                         'metric':metric,'value_m':value,'base_value_m':baseline[metric],
                         'delta_m':value-baseline[metric]})
        # The two-variable tables also carry the margin response.
        if kind=='TWO_WAY':
            rev=outcome['2027_revenue_m']; oi=outcome['2027_operating_income_m']
            rows.append({'kind':kind,'driver':driver,'shock':shock_label,'axis_x':axis_x,'axis_y':axis_y,
                         'metric':'2027_operating_margin_pct','value_m':100*oi/rev,
                         'base_value_m':100*baseline['2027_operating_income_m']/baseline['2027_revenue_m'],
                         'delta_m':100*oi/rev-100*baseline['2027_operating_income_m']/baseline['2027_revenue_m']})
    for driver,shock,label in SHOCKS:
        record('ONE_WAY',driver,label,shock)
    for activity in (.8,1.,1.2):
        for price in (.9,1.,1.1):
            record('TWO_WAY','options_activity_x_price',f'{activity:.0%} x {price:.0%}',
                   {'options_per_customer':activity,'option_revenue_per_contract_usd':price},
                   f'{activity:.0%}',f'{price:.0%}')
            record('TWO_WAY','crypto_activity_x_bps',f'{activity:.0%} x {price:.0%}',
                   {'crypto_app_per_customer_b':activity,'crypto_bitstamp_per_customer_b':activity,
                    'crypto_blended_bps':price},f'{activity:.0%}',f'{price:.0%}')
            yield_shift=(price-1)*5  # Percentage points: -0.5/0/+0.5.
            bp=round(yield_shift*100)
            record('TWO_WAY','balances_x_yield',f'{activity:.0%} balances x {bp:+d}bp',
                   {'interest_balance_multiplier':activity,'yield_shift_pct':yield_shift},
                   f'{activity:.0%}',f'{bp:+d}bp')
            record('TWO_WAY','trading_activity_x_opex',f'{activity:.0%} x {price:.0%}',
                   {'options_per_customer':activity,'crypto_app_per_customer_b':activity,
                    'crypto_bitstamp_per_customer_b':activity,'equity_notional_per_customer_b':activity,
                    'technology_base_m':price,'marketing_base_m':price,'general_base_m':price},
                   f'{activity:.0%}',f'{price:.0%}')
    if sensitivity_metrics(project(history,assumptions,'Base'))!=baseline:
        raise ValueError('Sensitivity failed to reset to base')
    return rows


def largest_shocks(sensitivities, metric, count=3):
    # Policy-rate and direct realized-yield shocks overlap economically. Rank
    # the larger direct-yield diagnostic once, then show pass-through separately.
    selected=[r for r in sensitivities if r['kind']=='ONE_WAY' and r['metric']==metric
              and r['driver']!='policy_rate_with_pass_through']
    by_driver={}
    for row in selected:
        if row['driver'] not in by_driver or abs(row['delta_m'])>abs(by_driver[row['driver']]['delta_m']):
            by_driver[row['driver']]=row
    return sorted(by_driver.values(),key=lambda r:abs(r['delta_m']),reverse=True)[:count]


def pseudo_historical(actual):
    """One-quarter mechanical diagnostic, calibrated only on 2024Q1/Q2."""
    by={r['period']:r for r in actual}
    prior=by['2024Q1']; base=by['2024Q2']; observed=by['2024Q3']
    projected_customers=base['funded_customers_m']+(base['funded_customers_m']-prior['funded_customers_m'])
    projected_average=(base['funded_customers_m']+projected_customers)/2
    result=[]
    for product, revenue, units in [('options','options_revenue_m','options_contracts_m'),
                                     ('crypto','crypto_revenue_m','crypto_notional_b'),
                                     ('equities','equities_revenue_m','equity_notional_b')]:
        activity=base[units]/base['average_funded_customers_m']
        monetization=base[revenue]/base[units]
        projection=projected_average*activity*monetization
        result.append({'product':product,'projected_revenue_m':projection,
                       'actual_revenue_m':observed[revenue],
                       'error_m':projection-observed[revenue]})
    return result
