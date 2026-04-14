from __future__ import annotations

from news_trend_predictor.config.settings import get_settings
from news_trend_predictor.logging_utils import configure_logging
from news_trend_predictor.pipeline.orchestrator import PipelineRunner


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    PipelineRunner(settings).run()


if __name__ == "__main__":
    main()
