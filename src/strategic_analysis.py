"""Audited Phase 5 decision calculations built on the Phase 4 operating engine."""
from __future__ import annotations

import copy
import csv
import math
from pathlib import Path

from .config import ROOT
from .forecast_analysis import ACTIVITY_KEYS
from .forecast_model import project


Q2_FILING = 'https://www.sec.gov/Archives/edgar/data/1783879/000178387926000114/hood-20260630.htm'
YEARS = (2026, 2027, 2028)
EXPENSES = ('brokerage_transaction_expense_m', 'technology_development_expense_m',
            'operations_expense_m', 'credit_loss_expense_m', 'marketing_expense_m',
            'general_administrative_expense_m')
BALANCES = ('margin', 'cash_deposit', 'cash_sweep', 'credit_card')


def annual(rows, year, key):
    return sum(float(r[key]) for r in rows if r['period'].startswith(str(year)))


def input_change(values, key, factor, year=2027):
    changed = copy.deepcopy(values)
    for q in range(1, 5):
        changed['Base'][f'{year}Q{q}'][key] *= factor
    return changed


def annual_oi(rows):
    return annual(rows, 2027, 'operating_income_m')


def solve_multiplier(history, values, shock, key, target, max_factor=1000):
    """Solve an exact engine threshold, returning null when not attainable."""
    def result(factor):
        return annual_oi(project(history, input_change(values, key, factor), 'Base', shock))
    low, high = 1., 2.
    if result(low) >= target:
        return 1., result(low)
    if result(high) <= result(low):
        # Additional volume with this expense equation cannot cure the shock.
        return None, result(high)
    while high < max_factor and result(high) < target:
        high *= 2
    if result(high) < target:
        return None, result(high)
    for _ in range(55):
        middle = (low + high) / 2
        if result(middle) < target:
            low = middle
        else:
            high = middle
    return high, result(high)


def audit_interest(base, assumptions):
    rows = [r for r in base if r['period'].startswith('2027')]
    parts = {name: sum(r[f'{name}_avg_balance_m'] for r in rows) / 4 * .01
             for name in BALANCES}
    total = sum(parts.values())
    policy = sum(sum(r[f'{name}_avg_balance_m'] for r in rows) / 4 * .01 *
                 assumptions['Base']['2027Q1'][f'{name}_rate_pass_through'] for name in BALANCES)
    return {'uniform_yield_100bp_m': total, 'components_m': parts,
            'policy_100bp_m': policy, 'company_disclosed_2026_100bp_m': 350,
            'company_source': Q2_FILING}


def audit_margin(actual, base):
    all_rows = actual + base
    table = []
    for year in (2025, *YEARS):
        row = {'year': year}
        for key in ('revenue_m', 'operating_expense_m', 'operating_income_m', *EXPENSES):
            row[key] = annual(all_rows, year, key)
        row['operating_margin_pct'] = 100 * row['operating_income_m'] / row['revenue_m']
        row['expense_to_revenue_pct'] = 100 * row['operating_expense_m'] / row['revenue_m']
        prior = table[-1] if table else None
        row['incremental_operating_margin_pct'] = (100 * (row['operating_income_m'] - prior['operating_income_m']) /
                                                   (row['revenue_m'] - prior['revenue_m'])) if prior else None
        for key in EXPENSES:
            row[f'{key}_growth_pct'] = (100 * (row[key] / prior[key] - 1)
                                             if prior and prior[key] else None)
        table.append(row)
    return table


def strategy_thresholds(history, values, base, margin):
    target = annual_oi(base)
    out = []
    def add(name, shock, key, unit, recent_range, method):
        factor, achieved = solve_multiplier(history, values, shock, key, target)
        input_value = values['Base']['2027Q1'][key]
        out.append({'threshold': name, 'shock': shock, 'driver': key,
                    'base_input': input_value, 'required_input': input_value * factor if factor else None,
                    'multiplier': factor, 'unit': unit, 'target_2027_oi_m': target,
                    'result_2027_oi_m': achieved, 'recent_range': recent_range,
                    'outside_recent_range': factor is None or input_value * factor > recent_range[1],
                    'method': method})
    add('Options activity offsets 50bp policy decline', {'policy_shift_pct': -.5},
        'options_per_customer', 'contracts per average funded customer per quarter', (21.6, 27.7),
        'Increase each 2027 quarter options/customer; include variable brokerage cost')
    add('Customer additions offset 20% crypto activity decline',
        {key: .8 for key in ACTIVITY_KEYS['crypto_activity']},
        'net_customer_additions_m', 'million net additions per quarter', (.2, .4),
        'Increase each 2027 quarter net additions; roll customers and interest balances')
    add('Deposits offset 10% transaction monetization decline',
        {key: .9 for key in ACTIVITY_KEYS['transaction_monetization']},
        'net_deposits_b', 'USD billions net deposits per quarter', (15.9, 21.7),
        'Increase each 2027 quarter deposits; cash capture and yields unchanged')
    y26, y27 = margin[1], margin[2]
    expense_ceiling = y27['revenue_m'] - y26['operating_income_m']
    revenue_floor = y27['operating_expense_m'] / (1 - y26['operating_margin_pct'] / 100)
    out += [
        {'threshold': '2027 expense eliminating operating-income growth', 'shock': {},
         'driver': 'operating_expense_m', 'base_input': y27['operating_expense_m'],
         'required_input': expense_ceiling, 'multiplier': expense_ceiling / y27['operating_expense_m'],
         'unit': 'USD millions annual', 'target_2027_oi_m': y26['operating_income_m'],
         'result_2027_oi_m': y27['revenue_m'] - expense_ceiling,
         'recent_range': None, 'outside_recent_range': None,
         'method': '2027 revenue minus 2026 Base operating income; expense ceiling, not guidance'},
        {'threshold': '2027 revenue preserving 2026 Base margin at planned costs', 'shock': {},
         'driver': 'revenue_m', 'base_input': y27['revenue_m'],
         'required_input': revenue_floor, 'multiplier': revenue_floor / y27['revenue_m'],
         'unit': 'USD millions annual', 'target_2027_oi_m': revenue_floor - y27['operating_expense_m'],
         'result_2027_oi_m': revenue_floor - y27['operating_expense_m'],
         'recent_range': None, 'outside_recent_range': None,
         'method': '2027 expense plan / (1 - 2026 Base operating margin); holds expense plan fixed'},
    ]
    return out


def selected_sensitivity(sensitivities, driver, shock, metric='2027_revenue_m'):
    return next(float(r['delta_m']) for r in sensitivities
                if r['kind'] == 'ONE_WAY' and r['driver'] == driver and
                r['shock'] == shock and r['metric'] == metric)


def decision_paths(sensitivities):
    specifications = [
        ('Customer & asset scale', 'customer_additions', '+25%',
         'Funded customers and deposits grew, but asset scope includes acquisitions and market value changes.',
         'Net additions, deposits, interest-bearing share, revenue/customer', 'Medium', 'High',
         'Customers and deposits must earn revenue without proportionate spending.'),
        ('Transaction engagement', 'options_activity', '+20%',
         'Measured 2024 transaction growth was primarily activity-led; options monetization is directly observable.',
         'Contracts/customer, crypto and equity notional/customer, realized product rates', 'Medium', 'Medium',
         'Trading units and realized monetization must hold through weaker market periods.'),
        ('Recurring / balance monetization', 'cash_capture', '+50%',
         'Balance growth offset lower realized yields in the matched 2025Q2–2026Q2 interest disclosure; Gold is modest.',
         'Earning balances, net realized yields, Gold subscribers', 'Medium for balance capture; low for policy rates',
         'Medium for balance capture; low for rate pass-through',
         'Balances and net spreads must persist; Gold alone is too small to replace trading volatility.'),
    ]
    rows=[]
    for name, driver, shock, evidence, drivers, controllability, confidence, dependency in specifications:
        rows.append({'path':name,'historical_evidence':evidence,'primary_drivers':drivers,
                     'defined_shock':f'{driver} {shock}',
                     '2027_revenue_delta_m':selected_sensitivity(sensitivities,driver,shock),
                     '2027_operating_income_delta_m':selected_sensitivity(sensitivities,driver,shock,'2027_operating_income_m'),
                     'controllability':controllability,'data_confidence':confidence,
                     'execution_dependency':dependency})
    return rows
