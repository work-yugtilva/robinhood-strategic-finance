# Robinhood Strategic Finance & Operating Model

**Phase 3:** historical financial analysis for the question: Which financial and operating drivers convert Robinhood's customer assets and broader products into sustainable revenue and operating profit?

The current deliverables are 14 quarterly financial records, monthly operating KPIs through August 2026, exact revenue growth bridges, customer and trading monetization, revenue mix, operating leverage, an interest-rate context series, and a [historical analysis](reports/HISTORICAL_ANALYSIS.md). [Source registry](data/source_registry.csv), [data quality report](DATA_QUALITY_REPORT.md), and [structural break log](reports/STRUCTURAL_BREAKS.md) preserve provenance and comparability limits. No forecast or recommendation has been built.

## Run

Use Python 3.11+ with `pip install -r requirements.txt`, then:

```bash
python -m src.phase3
python -m unittest discover -s tests -v
```

The command rebuilds Phase 2 source history, Phase 3 CSVs in `data/analysis/`, the four reports, and six charts. It reuses `data/raw/` and downloads missing sources; downloads need `curl` on PATH. `python -m src.pipeline --refresh` refreshes Phase 2 source files. Raw cache is ignored by Git; processed CSVs, checksums, source URLs, and curated filing-component facts are committed. A source failure names the affected URL. Values are USD millions (`_m`) or USD billions (`_b`) unless the [data dictionary](data/data_dictionary.csv) says otherwise. The three notebooks under `notebooks/` read the generated analysis CSVs; they do not recalculate source facts.

The [Q4 2025 platform-asset reconciliation](reports/Q4_2025_PLATFORM_ASSET_RECONCILIATION.md) explains why the revised $322.1 billion value is canonical while the preliminary $324 billion value remains in the audit trail. [Forecast driver framework](reports/FORECAST_DRIVER_FRAMEWORK.md) ranks later modeling inputs without producing forecasts.

This is an independent portfolio project based solely on publicly available information and is not affiliated with Robinhood Markets, Inc.
