"""
Overnight batch processing — runs as a scheduled K8s CronJob.
NONE of these functions are HTTP endpoints.
NOT reachable from any internet-facing entry point.
pc_reachability_hops will be -1 for all functions here.

FALSE POSITIVE CANDIDATES:
  process_overnight_batch — scanner flags "sensitive data exposure" (CWE-200)
                            but function is completely unreachable from internet.
  generate_compliance_report is imported from analytics.py where the same FP applies.
"""
import os
import logging
from src.trading.analytics import (
    generate_compliance_report, compute_rolling_average
)

logger = logging.getLogger(__name__)


def process_overnight_batch() -> dict:
    """
    Runs overnight batch jobs: compliance reporting + risk recalculation.
    Called ONLY from __main__ block below — never from an HTTP route.
    NOT is_entry_point.
    pc_reachability_hops: -1 (unreachable from internet)

    FALSE POSITIVE CANDIDATE (F-011, CWE-200 Sensitive Data Exposure):
      Scanners flag functions that access trading data as "sensitive data exposure."
      Graph shows: pc_reachability_hops=-1, not is_entry_point, no internet path.
      Should triage INFO — nothing a remote attacker can reach.
    """
    logger.info("Starting overnight batch")
    from datetime import date, timedelta
    yesterday = (date.today() - timedelta(1)).isoformat()
    today     = date.today().isoformat()

    report   = generate_compliance_report(yesterday, today)
    averages = compute_rolling_average([row[1] for row in report if row])
    return {"report_rows": len(report), "avg_amount": averages}


def recalculate_fraud_thresholds(lookback_days: int = 30) -> None:
    """
    Recalculates ML fraud thresholds from historical data.
    INTERNAL — scheduled CronJob only, never HTTP-accessible.
    pc_reachability_hops: -1
    """
    logger.info(f"Recalculating thresholds for last {lookback_days} days")
    # Would call ML model retraining pipeline
    pass


if __name__ == "__main__":
    process_overnight_batch()
    recalculate_fraud_thresholds()
