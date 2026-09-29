import csv
import math
import unittest
from pathlib import Path

from src.config import ROOT
from src.historical_analysis import build, bridge_product, get_fred, load_components, read_csv


class HistoricalAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fin=read_csv(ROOT/'data/processed/historical_financials_quarterly.csv')
        cls.kpi=read_csv(ROOT/'data/processed/operating_kpis_quarterly.csv')
        cls.facts=load_components()
        cls.outputs=build(cls.fin,cls.kpi,cls.facts,get_fred())

    def test_revenue_mix_and_gaap_ties_every_quarter(self):
        financial,mix,*_=self.outputs
        self.assertEqual(len(financial),14)
        for row,bucket in zip(financial,mix):
            self.assertAlmostEqual(row['revenue_m'],row['transaction_revenue_m']+row['net_interest_revenue_m']+row['other_revenue_m'],delta=1)
            self.assertAlmostEqual(row['operating_income_m'],row['revenue_m']-row['operating_expense_m'],delta=1)
            self.assertAlmostEqual(row['revenue_m'],sum(bucket[k] or 0 for k in ('market_activity_m','interest_balance_m','disclosed_recurring_m','unclassified_m')),places=8)
            self.assertAlmostEqual(100,sum(bucket[k] or 0 for k in ('market_activity_pct','interest_balance_pct','disclosed_recurring_pct','unclassified_pct')),places=8)

    def test_customer_average_and_arpu(self):
        row=self.outputs[0][0]
        self.assertAlmostEqual(row['average_funded_customers_m'],(23.0+23.1)/2)
        self.assertAlmostEqual(row['derived_arpu_usd_annualized'],4*441/row['average_funded_customers_m'])
        self.assertAlmostEqual(row['assets_per_customer_usd'],1000*78.4/23.1)
        q4=next(r for r in self.outputs[0] if r['period']=='2025Q4')
        self.assertEqual(q4['customer_assets_b'],322.1)
        self.assertNotEqual(q4['customer_assets_b'],324.0)

    def test_product_unit_conversion_and_no_silent_fill(self):
        mons=self.outputs[2]
        q2=next(r for r in mons if r['period']=='2026Q2')
        self.assertAlmostEqual(q2['options_revenue_per_contract_usd'],342/q2['options_contracts_m'])
        self.assertAlmostEqual(q2['crypto_revenue_per_notional_bps'],100/q2['crypto_notional_b']*10)
        self.assertAlmostEqual(q2['event_revenue_per_contract_usd'],156/(q2['event_contracts_b']*1000))
        self.assertEqual(q2['event_contracts_b'],13.6)
        quarterly=read_csv(ROOT/'data/processed/operating_kpis_quarterly.csv')
        self.assertEqual(next(r for r in quarterly if r['period']=='2026Q2')['event_contracts_b'],'13.5')
        self.assertIsNone(next(r for r in mons if r['period']=='2023Q1')['event_revenue_per_contract_usd'])
        monthly=read_csv(ROOT/'data/processed/operating_kpis_monthly.csv')
        self.assertEqual(next(r for r in monthly if r['period']=='2025-06')['crypto_notional_b'],'')
        self.assertEqual(next(r for r in mons if r['period']=='2025Q2')['crypto_notional_b'],35.0)

    def test_exact_bridges_and_scope_residual(self):
        bridges=self.outputs[4]
        for row in bridges:
            if row['product']=='TOTAL_TRANSACTION':
                parts=sum(row[k] for k in ('customer_scale_effect_m','activity_effect_m','monetization_effect_m','mix_residual_effect_m'))
                self.assertTrue(math.isclose(parts,row['change_m'],abs_tol=1e-8))
                self.assertTrue(math.isclose(row['bridge_total_m'],row['change_m'],abs_tol=1e-8))
        self.assertIsNone(bridge_product({'customers':1,'volume':0,'revenue':1},{'customers':2,'volume':2,'revenue':2},'options'))
        crypto=next(r for r in bridges if r['comparison']=='2025 vs 2024' and r['product']=='crypto')
        self.assertIsNone(crypto['customer_scale_effect_m'])
        self.assertIn('scope changed',crypto['coverage_note'])

    def test_incremental_margin_and_interest_component(self):
        fin=self.outputs[0]; lev=self.outputs[3]
        a=next(r for r in fin if r['period']=='2026Q1')
        b=next(r for r in fin if r['period']=='2026Q2')
        self.assertAlmostEqual(b['interest_asset_balance_effect_m']+b['interest_asset_yield_effect_m'],b['interest_asset_revenue_m']-a['interest_asset_revenue_m'])
        q2=next(r for r in lev if r['period']=='2026Q2')
        prior=next(r for r in lev if r['period']=='2025Q2')
        self.assertAlmostEqual(q2['incremental_operating_margin_yoy_pct'],100*(q2['operating_income_m']-prior['operating_income_m'])/(q2['revenue_m']-prior['revenue_m']))
        self.assertIsNone(next(r for r in lev if r['period']=='2023Q1')['incremental_operating_margin_yoy_pct'])

    def test_annual_ties_and_component_classification(self):
        fin=self.outputs[0]
        for year,total in ((2023,1865),(2024,2951),(2025,4473)):
            self.assertAlmostEqual(sum(r['revenue_m'] for r in fin if r['period'].startswith(str(year))),total,delta=1)
        for year,total in ((2023,75),(2024,109),(2025,179)):
            self.assertEqual(sum(self.facts[(f'{year}Q{q}','gold_subscription_revenue_m')]['value'] for q in range(1,5)),total)
        self.assertTrue(all(v['classification'] in ('REPORTED','DERIVED') for v in self.facts.values()))

    def test_repeat_build_is_deterministic(self):
        self.assertEqual(self.outputs,build(self.fin,self.kpi,self.facts,get_fred()))
        self.assertTrue(all(r['classification'] in ('REPORTED','DERIVED') for r in read_csv(ROOT/'data/source_registry.csv')))


if __name__=='__main__':
    unittest.main()
