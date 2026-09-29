import unittest

from src.pipeline import parse_financial_release, parse_monthly_release, extract_quarterly_kpis, validate_financial


class PipelineTests(unittest.TestCase):
    def test_financial_statement_and_reconciliation(self):
        html = '''<table><tr><td>CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS — Three Months Ended</td></tr>
        <tr><td>Transaction-based revenues</td><td>$</td><td>539</td><td>$</td><td>776</td></tr>
        <tr><td>Net interest revenues</td><td>357</td><td>389</td></tr>
        <tr><td>Other revenues</td><td>93</td><td>143</td></tr>
        <tr><td>Total net revenues</td><td>989</td><td>1,308</td></tr>
        <tr><td>Brokerage and transaction</td><td>48</td><td>62</td></tr>
        <tr><td>Technology and development</td><td>214</td><td>256</td></tr>
        <tr><td>Operations</td><td>29</td><td>57</td></tr>
        <tr><td>Provision for credit losses</td><td>28</td><td>56</td></tr>
        <tr><td>Marketing</td><td>99</td><td>104</td></tr>
        <tr><td>General and administrative</td><td>132</td><td>199</td></tr>
        <tr><td>Total operating expenses</td><td>550</td><td>734</td></tr>
        <tr><td>Net income</td><td>386</td><td>573</td></tr></table>
        <table><tr><td>Reconciliation of GAAP to Non-GAAP Results — Three Months Ended — Net income</td></tr>
        <tr><td>Adjusted EBITDA (non-GAAP)</td><td>549</td><td>741</td></tr></table>'''
        row = parse_financial_release(html, '2026Q2')
        self.assertEqual(row['revenue_m'], 1308)
        self.assertEqual(row['adjusted_ebitda_m'], 741)
        self.assertEqual(validate_financial(row), [])
        row['revenue_m'] = 1300
        self.assertIn('2026Q2: revenue categories do not tie', validate_financial(row))

    def test_monthly_stock_and_flow(self):
        html = '''<table><tr><td>August 2026</td><td>July 2026</td></tr>
        <tr><td>Funded Customers 1</td><td>28.6</td><td>28.5</td></tr>
        <tr><td>Total Platform Assets 1</td><td>$383.7</td><td>$355.0</td></tr>
        <tr><td>Net Deposits 1,2</td><td>$4.0</td><td>$5.6</td></tr></table>'''
        row = parse_monthly_release(html, '2026-08')
        self.assertEqual(row['funded_customers_m'], 28.6)
        self.assertEqual(row['net_deposits_b'], 4.0)
        self.assertEqual(parse_monthly_release(html, '2026-07', position=1)['net_deposits_b'], 5.6)

    def test_quarterly_disclosed_kpis(self):
        html = '''<body>Funded Customers increased to 28.4 million. Investment Accounts increased to 29.9 million.
        Gold Subscribers reached a record 4.8 million. ARPU increased 24% to $187.
        Total Platform Assets increased to $369 billion.</body>'''
        row = extract_quarterly_kpis(html)
        self.assertEqual(row['investment_accounts_m'], 29.9)
        self.assertEqual(row['arpu_usd_annualized'], 187)
        self.assertEqual(row['platform_assets_earnings_b'], 369)


if __name__ == '__main__':
    unittest.main()
