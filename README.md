# Robinhood Strategic Finance & Operating Model

**Phase 2:** public historical data pipeline for the question: Which financial and operating drivers convert Robinhood's customer assets and broader products into sustainable revenue and operating profit?

The current deliverables are 14 quarterly financial records, monthly operating KPI observations through August 2026, quarterly KPI aggregation where source months are complete, a source registry/manifest, and [DATA_QUALITY_REPORT.md](DATA_QUALITY_REPORT.md). The report identifies source and coverage limits. No forecast or recommendation has been built.

## Run

Use Python 3.11+ with `pip install -r requirements.txt`, then:

```bash
python -m src.pipeline
python -m unittest discover -s tests -v
```

The pipeline reuses `data/raw/` and downloads missing sources. `python -m src.pipeline --refresh` refreshes cached sources. Downloads need `curl` on PATH. Raw cache is ignored by Git; processed CSVs, checksums, and source URLs are committed. A source failure raises an error naming the URL. Values are USD millions (`_m`) or USD billions (`_b`) unless the data dictionary specifies a count unit.

This is an independent portfolio project based solely on publicly available information and is not affiliated with Robinhood Markets, Inc.
