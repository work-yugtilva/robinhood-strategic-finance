import hashlib
import math
import unittest

from src.config import ROOT
from src.forecast_analysis import (add_incremental, make_bridges, make_sensitivities,
                                   make_summaries, pseudo_historical, sensitivity_metrics)
from src.forecast_model import (PERIODS, SCENARIOS, actual_rows, build_assumptions,
                                load_history, project, read_csv)
from src.phase4 import check, hashes, run


class ForecastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history=load_history()
        cls.assumption_rows,cls.values=build_assumptions(cls.history)
        cls.actual=actual_rows(cls.history)
        cls.forecasts={sc:project(cls.history,cls.values,sc) for sc in SCENARIOS}
        add_incremental(cls.actual,cls.forecasts)
        cls.summaries=make_summaries(cls.actual,cls.forecasts)
        cls.bridges=make_bridges(cls.actual,cls.forecasts)

    def test_source_baselines_and_no_historical_override(self):
        self.assertEqual(len(self.actual),14)
        self.assertTrue(all(row['scenario']=='ACTUAL' and row['status']=='ACTUAL' for row in self.actual))
        q2=self.actual[-1]
        self.assertEqual((q2['revenue_m'],q2['operating_expense_m'],q2['platform_assets_b']),(1308,734,368.7))
        self.assertEqual(q2['event_contracts_b'],13.6)
        self.assertIsNone(self.actual[0]['event_contracts_revenue_m'])
        self.assertIsNone(self.actual[0]['event_contracts_b'])
        self.assertIsNone(self.actual[1]['gold_subscribers_m'])
        self.assertTrue(all(row['classification'] in ('REPORTED','DERIVED') for row in read_csv(ROOT/'data/source_registry.csv')))

    def test_q3_partial_observations_are_not_financial_actuals(self):
        for sc in SCENARIOS:
            q3=self.forecasts[sc][0]
            self.assertEqual((q3['period'],q3['status'],q3['nowcast']),('2026Q3','FORECAST',True))
            self.assertAlmostEqual(q3['net_deposits_b'],9.6+self.values[sc]['2026-09']['sept_net_deposits_b'])
            self.assertAlmostEqual(q3['options_contracts_m'],616.7+self.values[sc]['2026-09']['sept_options_contracts_m'])
            self.assertAlmostEqual(q3['platform_assets_b'],368.7+q3['net_deposits_b']+q3['market_asset_value_change_b']+5.4)
            self.assertAlmostEqual(q3['other_asset_change_b'],5.4)
        observed=[r for r in self.assumption_rows if r['period'] in ('2026-07','2026-08')]
        self.assertTrue(observed)
        self.assertTrue(all(r['classification']=='REPORTED' and r['observation_status']=='PARTIAL-QUARTER OBSERVATION' for r in observed))

    def test_full_model_reconciles_and_denominators_are_positive(self):
        check(self.actual,self.forecasts,self.summaries,self.bridges)
        for sc in SCENARIOS:
            self.assertEqual([r['period'] for r in self.forecasts[sc]],PERIODS)
            for row in self.forecasts[sc]:
                self.assertAlmostEqual(row['crypto_notional_b'],row['crypto_app_notional_b']+row['crypto_bitstamp_notional_b'])
                self.assertAlmostEqual(row['options_revenue_m'],row['options_contracts_m']*row['option_revenue_per_contract_usd'])
                self.assertAlmostEqual(row['crypto_revenue_m'],row['crypto_notional_b']*row['crypto_monetization_bps']/10)
                self.assertAlmostEqual(row['revenue_per_avg_customer_usd'],row['revenue_m']/row['average_funded_customers_m'])
                self.assertTrue(all(math.isfinite(v) for v in row.values() if isinstance(v,float)))

    def test_scenario_and_annual_status(self):
        yr=lambda sc: next(r for r in self.summaries if r['scenario']==sc and r['window']=='2027')
        self.assertLess(yr('Downside')['revenue_m'],yr('Base')['revenue_m'])
        self.assertLess(yr('Base')['revenue_m'],yr('Upside')['revenue_m'])
        self.assertLess(yr('Downside')['operating_income_m'],yr('Base')['operating_income_m'])
        for sc in SCENARIOS:
            y2026=next(r for r in self.summaries if r['scenario']==sc and r['window']=='2026')
            self.assertEqual((y2026['actual_quarters'],y2026['forecast_quarters']),(2,2))
            y2027=next(r for r in self.summaries if r['scenario']==sc and r['window']=='2027')
            self.assertAlmostEqual(y2027['revenue_m'],sum(r['revenue_m'] for r in self.forecasts[sc] if r['period'].startswith('2027')))

    def test_bridge_ties_and_scope_residual(self):
        for row in self.bridges:
            self.assertAlmostEqual(row['bridge_total_m'],row['change_m'],places=7)
        first=next(r for r in self.bridges if r['scenario']=='Base' and r['comparison']=='2026 vs 2025')
        self.assertNotIn('crypto',first['comparable_products'])
        self.assertNotIn('event',first['comparable_products'])
        self.assertNotEqual(first['structural_product_mix_m'],0)

    def test_sensitivity_restarts_from_base(self):
        original=sensitivity_metrics(self.forecasts['Base'])
        shocks=make_sensitivities(self.history,self.values,self.forecasts['Base'])
        self.assertEqual(original,sensitivity_metrics(project(self.history,self.values,'Base')))
        for driver in ('options_activity','crypto_activity','transaction_monetization'):
            labels={r['shock'] for r in shocks if r['kind']=='ONE_WAY' and r['driver']==driver}
            self.assertEqual(labels,{'-20%','-10%','Base','+10%','+20%'})
        base_rows=[r for r in shocks if r['shock']=='Base' and r['kind']=='ONE_WAY']
        self.assertTrue(base_rows)
        self.assertTrue(all(abs(r['delta_m'])<1e-8 for r in base_rows))

    def test_pseudo_historical_is_diagnostic_not_fit(self):
        diagnostic=pseudo_historical(self.actual)
        self.assertEqual({r['product'] for r in diagnostic},{'options','crypto','equities'})
        self.assertTrue(any(abs(r['error_m'])>1 for r in diagnostic))

    def test_repeat_build_byte_identity_and_history_hash(self):
        before=hashes()
        run()
        outputs=(sorted((ROOT/'data/forecast').glob('*.csv'))+
                 sorted((ROOT/'reports').glob('FORECAST_*.md'))+
                 [ROOT/'reports/SENSITIVITY_ANALYSIS.md']+
                 sorted((ROOT/'reports/forecast_charts').glob('*.png'))+
                 sorted((ROOT/'notebooks').glob('forecast_*.ipynb')))
        first={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs}
        run()
        second={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs}
        self.assertEqual(first,second)
        self.assertEqual(before,hashes())


if __name__=='__main__':
    unittest.main()
