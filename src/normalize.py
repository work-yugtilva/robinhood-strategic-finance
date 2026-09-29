"""Extract reported quarterly statements and monthly/quarterly operating data."""
import re
from lxml import html

FIN_LABELS = {
    'Transaction-based revenues':'transaction_revenue_m',
    'Net interest revenues':'net_interest_revenue_m',
    'Other revenues':'other_revenue_m',
    'Total net revenues':'revenue_m',
    'Brokerage and transaction':'brokerage_transaction_expense_m',
    'Technology and development':'technology_development_expense_m',
    'Operations':'operations_expense_m',
    'Provision for credit losses':'credit_loss_expense_m',
    'Marketing':'marketing_expense_m',
    'General and administrative':'general_administrative_expense_m',
    'Total operating expenses':'operating_expense_m',
    'Other income, net':'other_income_m',
    'Other income (loss), net':'other_income_m',
    'Other income (expense), net':'other_income_m',
    'Other (income) expense, net':'other_income_m',
    'Income before income taxes':'pretax_income_m',
    'Income (loss) before income taxes':'pretax_income_m',
    'Loss before income taxes':'pretax_income_m',
    'Provision for income taxes':'income_tax_expense_m',
    'Provision for (benefit from) income taxes':'income_tax_expense_m',
    'Net income':'net_income_m',
    'Net income (loss)':'net_income_m',
    'Net loss':'net_income_m',
}
EXPENSE_KEYS = [
    'brokerage_transaction_expense_m','technology_development_expense_m',
    'operations_expense_m','credit_loss_expense_m','marketing_expense_m',
    'general_administrative_expense_m',
]


def row_cells(row):
    return [' '.join(c.itertext()).replace('\xa0',' ').strip() for c in row.xpath('./th|./td')]


def numbers(cells):
    values = []
    for cell in cells:
        t = cell.strip().replace(',','').replace('$','')
        if t in ('','%','—','–','-','NM','N/M',')','('):
            continue
        m = re.fullmatch(r'\(?\s*[-+]?\d+(?:\.\d+)?\s*\)?', t)
        if m:
            values.append(-float(t.strip('() ')) if '(' in t else float(t))
    return values


def statement_amounts(cells):
    """Statement tables put prior/current amounts before the first percent column."""
    values=[]
    for cell in cells:
        t=cell.strip().replace(',','').replace('$','')
        if '%' in t or t in ('NM','N/M'):
            break
        if t in ('—','–','-'):
            values.append(0.0)
        elif re.fullmatch(r'\(?\s*[-+]?\d+(?:\.\d+)?\s*\)?',t):
            values.append(-float(t.strip('() ')) if '(' in t else float(t))
    return values


def parse_financial_release(raw, period):
    tree = html.fromstring(raw)
    table = next((t for t in tree.xpath('//table')
                  if 'Three Months Ended' in ' '.join(t.itertext())
                  and 'Total net revenues' in ' '.join(t.itertext())
                  and 'Transaction-based revenues' in ' '.join(t.itertext())),None)
    if table is None:
        raise ValueError(f'{period}: quarterly statement table missing')
    result = {'period':period}
    for row in table.xpath('.//tr'):
        cells = row_cells(row)
        if not cells:
            continue
        label = re.sub(r'\s+',' ',cells[0]).strip()
        if label in FIN_LABELS:
            vals = statement_amounts(cells[1:])
            if len(vals) >= 2:
                result[FIN_LABELS[label]] = -vals[1] if label=='Other (income) expense, net' else vals[1]
    recon = next((t for t in tree.xpath('//table')
                  if 'Three Months Ended' in ' '.join(t.itertext())
                  and 'Adjusted EBITDA' in ' '.join(t.itertext())
                  and ('Net income' in ' '.join(t.itertext()) or 'Net loss' in ' '.join(t.itertext()))),None)
    if recon is not None:
        between=False
        adjustments=[]
        for row in recon.xpath('.//tr'):
            cells = row_cells(row)
            if not cells:
                continue
            label = re.sub(r'\s+',' ',cells[0]).strip()
            vals = statement_amounts(cells[1:])
            if len(vals) < 2:
                continue
            if label == 'Adjusted EBITDA (non-GAAP)':
                result['adjusted_ebitda_m'] = vals[1]
            elif label == 'EBITDA (non-GAAP)':
                result['ebitda_non_gaap_m'] = vals[1]
                between=True
            elif label == 'SBC':
                result['sbc_adjustment_m'] = vals[1]
            elif label.startswith('Interest expenses related to'):
                result['interest_expense_adjustment_m'] = vals[1]
            elif label == 'Depreciation and amortization':
                result['depreciation_amortization_adjustment_m'] = vals[1]
            if between and label not in ('EBITDA (non-GAAP)','Adjusted EBITDA (non-GAAP)'):
                adjustments.append(vals[1])
            if label == 'Adjusted EBITDA (non-GAAP)' and result.get('ebitda_non_gaap_m') is not None:
                result['adjusted_ebitda_recomputed_m'] = result['ebitda_non_gaap_m']+sum(adjustments)
    if result.get('revenue_m') is not None and result.get('operating_expense_m') is not None:
        result['operating_income_m'] = result['revenue_m'] - result['operating_expense_m']
    extract_product_revenue(tree, result)
    return result


def extract_product_revenue(tree, result):
    narrative=' '.join(tree.text_content().replace('\xa0',' ').split())
    narrative=narrative.split('CONDENSED CONSOLIDATED')[0].split('CONSOLIDATED STATEMENTS OF OPERATIONS')[0]
    patterns={
        'options_revenue_m':[r'options revenue of \$([\d,]+) million',r'options (?:increased|decreased|was unchanged).*?(?:to|at) \$([\d,]+) million'],
        'crypto_revenue_m':[r'cryptocurrencies revenue of \$([\d,]+) million',r'cryptocurrencies (?:increased|decreased|was unchanged).*?(?:to|at) \$([\d,]+) million'],
        'equities_revenue_m':[r'equities revenue of \$([\d,]+) million',r'equities (?:increased|decreased|was unchanged).*?(?:to|at) \$([\d,]+) million'],
        'event_contracts_revenue_m':[r'event contracts revenue of \$([\d,]+) million'],
        'other_transaction_revenue_m':[r'other transaction revenue of \$([\d,]+) million'],
    }
    for key,options in patterns.items():
        for pattern in options:
            match=re.search(pattern,narrative,re.I)
            if match:
                result[key]=float(match.group(1).replace(',',''))
                break
    if all(result.get(k) is not None for k in ('transaction_revenue_m','options_revenue_m','crypto_revenue_m','equities_revenue_m')):
        known=sum(result[k] for k in ('options_revenue_m','crypto_revenue_m','equities_revenue_m'))
        known+=sum(result.get(k,0) for k in ('event_contracts_revenue_m','other_transaction_revenue_m'))
        result['unclassified_transaction_revenue_m']=result['transaction_revenue_m']-known


MONTHLY_LABELS = {
    'Funded Customers':'funded_customers_m',
    'Net Cumulative Funded Accounts (NCFA)':'net_cumulative_funded_accounts_m',
    'Total Platform Assets':'platform_assets_b',
    'Total AUC':'assets_under_custody_b',
    'Net Deposits':'net_deposits_b',
    'Equity ($B)':'equity_notional_b',
    'Options Contracts (M)':'options_contracts_m',
    'Crypto ($B)':'crypto_notional_b',
    'Event Contracts (B)':'event_contracts_b',
    'Margin Book':'margin_book_b',
    'Cash and Deposits':'cash_deposits_b',
    'Cash Sweep':'cash_sweep_b',
    'Total Cash Sweep':'cash_sweep_b',
}


def parse_monthly_release(raw, period, position=0):
    tree = html.fromstring(raw)
    result = {'period':period}
    tables = tree.xpath('//table')
    if not tables:
        return result
    section = ''
    for row in tables[0].xpath('.//tr'):
        cells = row_cells(row)
        if not cells:
            continue
        label = re.sub(r'\s+',' ',cells[0]).strip()
        if 'Total Trading Volumes' in label or 'Notional Trading Volumes' in label:
            section = 'volume'
        elif 'Average Daily Trading Volumes' in label or 'Daily Average Trades' in label:
            section = 'other'
        if len(cells) < 2 or (label.lower() in ('equity ($b)','options contracts (m)','crypto ($b)') and section != 'volume'):
            continue
        for prefix, key in MONTHLY_LABELS.items():
            if label.lower() == prefix.lower() or re.fullmatch(re.escape(prefix)+r'(?:\s+[\d,]+)?',label,re.I):
                vals = numbers(cells[1:])
                if len(vals)>position:
                    result[key] = vals[position]
                break
    return result


def extract_quarterly_kpis(raw):
    text=' '.join(html.fromstring(raw).text_content().replace('\xa0',' ').split())
    text=text.split('CONDENSED CONSOLIDATED')[0].split('CONSOLIDATED STATEMENTS OF OPERATIONS')[0]
    patterns={
        'investment_accounts_m':r'Investment Accounts.{0,120}?to ([\d.]+) million',
        'gold_subscribers_m':r'Gold Subscribers.{0,120}?(?:to|record|at) ([\d.]+) million',
        'arpu_usd_annualized':r'ARPU.{0,120}?to \$([\d,]+)',
        'platform_assets_earnings_b':r'Total Platform Assets.{0,120}?to \$([\d,.]+) billion',
    }
    result={}
    for key,pattern in patterns.items():
        m=re.search(pattern,text,re.I)
        if m:
            result[key]=float(m.group(1).replace(',',''))
    return result


