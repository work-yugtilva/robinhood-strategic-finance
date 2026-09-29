"""Material historical statement reconciliation checks."""
from .normalize import EXPENSE_KEYS

def validate_financial(row, tol=1.0):
    errors = []
    revenue_parts=['transaction_revenue_m','net_interest_revenue_m','other_revenue_m']
    if all(row.get(k) is not None for k in ['revenue_m']+revenue_parts):
        if abs(row['revenue_m']-sum(row[k] for k in revenue_parts))>tol:
            errors.append(f'{row["period"]}: revenue categories do not tie')
    disclosed_expenses=[row[k] for k in EXPENSE_KEYS if row.get(k) is not None]
    if row.get('operating_expense_m') is not None and len(disclosed_expenses)>=5:
        if abs(row['operating_expense_m']-sum(disclosed_expenses))>tol:
            errors.append(f'{row["period"]}: disclosed expense categories do not tie')
    if all(row.get(k) is not None for k in ['revenue_m','operating_expense_m','operating_income_m']):
        if abs(row['operating_income_m']-(row['revenue_m']-row['operating_expense_m'])) > tol:
            errors.append(f'{row["period"]}: operating income does not tie')
    if row.get('adjusted_ebitda_recomputed_m') is not None and row.get('adjusted_ebitda_m') is not None:
        if abs(row['adjusted_ebitda_recomputed_m']-row['adjusted_ebitda_m'])>tol:
            errors.append(f'{row["period"]}: adjusted EBITDA reconciliation does not tie')
    if row.get('pretax_income_m') is not None:
        other=row.get('other_income_m')
        if other is not None and abs(row['pretax_income_m']-row['operating_income_m']-other)>tol:
            errors.append(f'{row["period"]}: pretax income does not tie')
    if row.get('net_income_m') is not None and row.get('income_tax_expense_m') is not None and row.get('pretax_income_m') is not None:
        if abs(row['net_income_m']-(row['pretax_income_m']-row['income_tax_expense_m']))>tol:
            errors.append(f'{row["period"]}: net income does not tie')
    return errors


