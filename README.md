# Robinhood Strategic Finance & Operating Model

**Phase 4:** a 12-quarter, driver-based operating forecast for the question: What would have to happen operationally for Robinhood to continue producing strong revenue growth and operating leverage?

The project uses 14 reported quarterly financial records through 2026 Q2 and monthly operating KPIs through August 2026. The [historical analysis](reports/HISTORICAL_ANALYSIS.md) establishes revenue, customer, trading, interest and expense drivers. Phase 4 adds [Base, Upside and Downside results](reports/FORECAST_RESULTS.md), [editable assumption rows](data/forecast/forecast_assumptions.csv), exact annual bridges, and [sensitivity analysis](reports/SENSITIVITY_ANALYSIS.md). The Q3 2026 estimate uses July/August operating observations plus September assumptions and is labeled **forecast/nowcast**. There is no valuation or management recommendation.

## Run

Use Python 3.11+ with `pip install -r requirements.txt`, then:

```bash
python -m src.phase3
python -m src.phase4
python -m unittest discover -s tests -v
```

The Phase 3 command rebuilds source history, analysis CSVs, reports and charts. It reuses ignored `data/raw/` and downloads missing sources; downloads need `curl` on PATH. `python -m src.pipeline --refresh` refreshes Phase 2 source files. Phase 4 reads the approved historical files without changing them and writes five CSVs under `data/forecast/`, four reports, five charts, and three thin notebooks. Values are USD millions (`_m`) or billions (`_b`) unless the [data dictionary](data/data_dictionary.csv) or [forecast method](reports/FORECAST_METHOD.md) says otherwise. Tests include full revenue and expense ties, bridge ties, historical-file hashes, and repeat-build byte identity.

The [Q4 2025 platform-asset reconciliation](reports/Q4_2025_PLATFORM_ASSET_RECONCILIATION.md) explains why the revised $322.1 billion value is canonical while the preliminary $324 billion value remains in the audit trail. The [forecast risks](reports/FORECAST_RISKS.md) explain where public data and structural breaks limit precision.

This is an independent portfolio project based solely on publicly available information and is not affiliated with Robinhood Markets, Inc.
