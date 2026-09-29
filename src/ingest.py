"""Retrieve and verify company and SEC source files."""
import csv
import hashlib
import re
import subprocess
from datetime import date
from lxml import html
from .config import ROOT, RAW, BASE, ARCHIVE, CUTOFF

def fetch(url, path, refresh=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not refresh:
        return path.read_bytes(), 'cached'
    result = subprocess.run(
        ['curl','-L','--fail','--silent','--show-error','--max-time','35',
         '-A','RobinhoodStrategicFinance research contact: portfolio-research@example.com',url],
        capture_output=True)
    if result.returncode:
        raise RuntimeError(f'{url}: {result.stderr.decode(errors="replace").strip()}')
    path.write_bytes(result.stdout)
    return result.stdout, 'downloaded'


def verify_cache(refresh=False):
    manifest_path=ROOT/'data/source_manifest.csv'
    if refresh or not manifest_path.exists():
        return
    seen=set()
    for row in csv.DictReader(manifest_path.open()):
        name=row.get('cache_filename','')
        digest=row.get('sha256','')
        if not name or not digest or name in seen:
            continue
        seen.add(name)
        path=RAW/name
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise RuntimeError(f'Cached source checksum mismatch: {path}; rerun with --refresh to redownload')


def month_range():
    return [f'{y}-{m:02d}' for y in range(2023,2027) for m in range(1,13)
            if (y,m) <= (2026,8)]


def discover(cache, refresh=False):
    found = {}
    for page in range(1,41):
        raw,_ = fetch(ARCHIVE.format(page), cache / f'gnw_index_{page}.html', refresh)
        tree = html.fromstring(raw)
        page_dates=[]
        for a in tree.xpath('//a[@href]'):
            href = a.get('href','')
            title = ' '.join(a.xpath('.//text()')).strip()
            if not href.startswith('/news-release/'):
                continue
            m = re.search(r'/news-release/(\d{4})/(\d{2})/(\d{2})/',href)
            if m:
                page_dates.append(date(*map(int,m.groups())))
            if not ('Operating Data' in title or ('Robinhood Reports' in title and 'Results' in title)):
                continue
            if not m or not date(*map(int,m.groups())) <= CUTOFF:
                continue
            found[BASE+href] = title
        if page_dates and max(page_dates)<date(2023,1,1):
            break
    return found


def release_period(title):
    t = title.lower()
    for name, q in [('first quarter',1),('second quarter',2),('third quarter',3),('fourth quarter',4)]:
        m = re.search(name+r'(?:\s+and\s+full\s+year)?\s+(20\d{2})',t)
        if m:
            return 'quarter', f'{m.group(1)}Q{q}'
    m = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(20\d{2})',t)
    if m:
        months = ['january','february','march','april','may','june','july','august','september','october','november','december']
        return 'month', f'{m.group(2)}-{months.index(m.group(1))+1:02d}'
    return None,None


def sec_fact(facts, tag, start, end, accession):
    entries=facts['facts']['us-gaap'][tag]['units']['USD']
    for x in entries:
        if x.get('start')==start and x.get('end')==end and x.get('accn')==accession:
            return x['val']/1_000_000
    return None


