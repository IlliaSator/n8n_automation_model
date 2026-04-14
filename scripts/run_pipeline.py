from __future__ import annotations

import argparse
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from news_trend_predictor.config.settings import get_settings
from news_trend_predictor.logging_utils import configure_logging
from news_trend_predictor.pipeline.orchestrator import PipelineRunner

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run News Trend Predictor pipeline.")
    parser.add_argument("--mode", choices=["once", "schedule"], default="once")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    runner = PipelineRunner(settings)

    if args.mode == "once":
        runner.run()
        return

    scheduler = BlockingScheduler()
    scheduler.add_job(runner.run, CronTrigger.from_crontab(settings.schedule_cron), max_instances=1, coalesce=True)
    LOGGER.info("Starting scheduler with cron: %s", settings.schedule_cron)
    scheduler.start()


if __name__ == "__main__":
    main()
