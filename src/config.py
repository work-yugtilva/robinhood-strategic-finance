"""Source and period constants for the historical pipeline."""
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'data' / 'processed'
CUTOFF = date(2026, 9, 28)
BASE = 'https://www.globenewswire.com'
ARCHIVE = BASE + '/en/search/organization/Robinhood%2520Markets%CE%B4%2520Inc%C2%A7?page={}'
SEC_FACTS = 'https://data.sec.gov/api/xbrl/companyfacts/CIK0001783879.json'
IR_QUARTERS = 'https://investors.robinhood.com/financials/quarterly-results'
IR_MONTHS = 'https://investors.robinhood.com/financials/monthly-metrics'

FILINGS = [
    ('2023Q1','0001783879-23-000117'),('2023Q2','0001783879-23-000175'),
    ('2023Q3','0001783879-23-000268'),('2023FY','0001783879-24-000054'),
    ('2024Q1','0001783879-24-000145'),('2024Q2','0001783879-24-000233'),
    ('2024Q3','0001783879-24-000296'),('2024FY','0001783879-25-000049'),
    ('2025Q1','0001783879-25-000145'),('2025Q2','0001783879-25-000251'),
    ('2025Q3','0001783879-25-000310'),('2025FY','0001783879-26-000029'),
    ('2026Q1','0001783879-26-000062'),('2026Q2','0001783879-26-000114'),
]

