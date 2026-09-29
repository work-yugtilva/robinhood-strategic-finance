"""Build the 12-quarter operating forecast from the frozen Phase 3 history."""
from __future__ import annotations

import hashlib

from .config import ROOT
from .forecast_analysis import add_incremental, make_bridges, make_sensitivities, make_summaries
from .forecast_artifacts import write_all
from .forecast_model import SCENARIOS, actual_rows, build_assumptions, load_history, project


HISTORICAL_PATHS = [
    ROOT / 'data/processed/historical_financials_quarterly.csv',
    ROOT / 'data/processed/operating_kpis_quarterly.csv',
    ROOT / 'data/processed/operating_kpis_monthly.csv',
    ROOT / 'data/analysis/financial_kpis_quarterly.csv',
    ROOT / 'data/disclosed_components.csv',
]


def hashes():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in HISTORICAL_PATHS}


def check(actual, forecasts, summaries, bridges):
    if len(actual)!=14 or actual[-1]['period']!='2026Q2':
        raise ValueError('Historical actual cutoff changed')
    for scenario in SCENARIOS:
        rows=forecasts[scenario]
        if len(rows)!=12 or rows[0]['period']!='2026Q3' or rows[-1]['period']!='2029Q2':
            raise ValueError(f'{scenario}: 12-quarter coverage failed')
        for index,row in enumerate(rows):
            p=row['period']
            if row['status']!='FORECAST' or bool(row['nowcast'])!=(p=='2026Q3'):
                raise ValueError(f'{scenario} {p}: forecast/nowcast status wrong')
            if abs(row['revenue_m']-sum(row[k] for k in ('transaction_revenue_m','net_interest_revenue_m','other_revenue_m')))>1e-8:
                raise ValueError(f'{scenario} {p}: revenue reconciliation')
            if abs(row['transaction_revenue_m']-sum(row[k] for k in ('options_revenue_m','crypto_revenue_m','equities_revenue_m',
                                                                     'event_contracts_revenue_m','other_transaction_revenue_m')))>1e-8:
                raise ValueError(f'{scenario} {p}: transaction reconciliation')
            if abs(row['other_revenue_m']-sum(row[k] for k in ('gold_subscription_revenue_m','proxy_revenue_m','residual_other_revenue_m')))>1e-8:
                raise ValueError(f'{scenario} {p}: other revenue reconciliation')
            if abs(row['net_interest_revenue_m']-row['interest_asset_revenue_m']-row['interest_remainder_m'])>1e-8:
                raise ValueError(f'{scenario} {p}: net-interest reconciliation')
            interest_components=('margin_interest_revenue_m','cash_deposit_interest_revenue_m',
                                 'cash_sweep_interest_revenue_m','credit_card_interest_revenue_m')
            if abs(row['interest_asset_revenue_m']-sum(row[k] for k in interest_components))>1e-8:
                raise ValueError(f'{scenario} {p}: interest-asset component reconciliation')
            if abs(row['revenue_m']-sum(row[k] for k in ('market_activity_revenue_m','interest_balance_revenue_m',
                                                       'disclosed_recurring_revenue_m','unclassified_revenue_m')))>1e-8:
                raise ValueError(f'{scenario} {p}: durability mix reconciliation')
            expenses=('brokerage_transaction_expense_m','technology_development_expense_m','operations_expense_m',
                      'credit_loss_expense_m','marketing_expense_m','general_administrative_expense_m')
            if abs(row['operating_expense_m']-sum(row[k] for k in expenses))>1e-8:
                raise ValueError(f'{scenario} {p}: expense reconciliation')
            if abs(row['operating_income_m']-(row['revenue_m']-row['operating_expense_m']))>1e-8:
                raise ValueError(f'{scenario} {p}: operating-income reconciliation')
            ebitda=(row['net_income_m']+row['income_tax_expense_m']+row['sbc_adjustment_m']+
                    row['depreciation_amortization_adjustment_m']+row['interest_expense_adjustment_m']-row['other_income_m'])
            if abs(row['adjusted_ebitda_m']-ebitda)>1e-8:
                raise ValueError(f'{scenario} {p}: adjusted EBITDA reconciliation')
            prior_customers=28.4 if index==0 else rows[index-1]['funded_customers_m']
            if abs(row['funded_customers_m']-prior_customers-row['net_customer_additions_m'])>1e-8:
                raise ValueError(f'{scenario} {p}: funded-customer roll-forward')
            if abs(row['adjusted_opex_and_sbc_m']-row['operating_expense_m']+row['credit_loss_expense_m'])>1e-8:
                raise ValueError(f'{scenario} {p}: adjusted expense comparison')
            if abs(row['platform_assets_b']-(row['net_deposits_b']+row['market_asset_value_change_b']+
                                              row['acquired_assets_b']+row['other_asset_change_b']+
                                              (368.7 if index==0 else rows[index-1]['platform_assets_b'])))>1e-8:
                raise ValueError(f'{scenario} {p}: asset roll-forward')
            if row['acquired_assets_b']!=0 or any(row[key]<=0 for key in ('funded_customers_m','average_funded_customers_m',
                                                                           'options_contracts_m','crypto_notional_b',
                                                                           'equity_notional_b','event_contracts_b','revenue_m')):
                raise ValueError(f'{scenario} {p}: invalid acquired assets or denominator')
    for bridge in bridges:
        if abs(bridge['change_m']-bridge['bridge_total_m'])>1e-8:
            raise ValueError(f"Bridge failure {bridge['scenario']} {bridge['comparison']}")
    if len(summaries)!=15 or len(bridges)!=9:
        raise ValueError('Annual summary/bridge coverage changed')
    for summary in summaries:
        if abs(sum(summary[k] for k in ('market_activity_pct','interest_balance_pct',
                                        'disclosed_recurring_pct','unclassified_pct'))-100)>1e-8:
            raise ValueError(f"{summary['scenario']} {summary['window']}: revenue mix percentage tie")


def run():
    before=hashes()
    history=load_history()
    assumptions,values=build_assumptions(history)
    actual=actual_rows(history)
    forecasts={scenario:project(history,values,scenario) for scenario in SCENARIOS}
    add_incremental(actual,forecasts)
    summaries=make_summaries(actual,forecasts)
    bridges=make_bridges(actual,forecasts)
    sensitivities=make_sensitivities(history,values,forecasts['Base'])
    check(actual,forecasts,summaries,bridges)
    write_all(assumptions,actual,forecasts,summaries,sensitivities,bridges)
    if hashes()!=before:
        raise ValueError('Phase 4 changed a historical input file')
    print('Phase 4 forecast, scenario, sensitivity and bridge outputs complete.')


if __name__=='__main__':
    run()
