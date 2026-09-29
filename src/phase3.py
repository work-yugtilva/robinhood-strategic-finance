"""Rebuild Phase 2 source history, then Phase 3 analysis and artifacts."""
from .pipeline import run as rebuild_history
from .historical_analysis import run as build_analysis
from .analysis_artifacts import run as build_artifacts


def run():
    rebuild_history(refresh=False)
    build_analysis()
    build_artifacts()
    print('Phase 3 historical analysis complete.')


if __name__ == '__main__':
    run()
