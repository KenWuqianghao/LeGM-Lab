"""Run a single take through the full agent pipeline."""

import asyncio
import sys
from pathlib import Path

from legm.agent.analyzer import TakeAnalyzer
from legm.config import settings
from legm.llm.factory import create_llm_provider
from legm.stats.cache import TTLCache
from legm.stats.client import NBAClient
from legm.stats.service import NBAStatsService


async def main() -> None:
    take = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "KD was the best player on the Warriors team"

    llm = create_llm_provider(settings)
    stats_service = NBAStatsService(NBAClient(), TTLCache())
    analyzer = TakeAnalyzer(llm, stats_service)

    print(f"TAKE: {take}\n")
    result = await analyzer.analyze(take)

    print(f"Verdict: {result.verdict.upper()} (confidence: {result.confidence})")
    print(f"\nTweet:\n{result.roast}")
    print(f"\nReasoning:\n{result.reasoning}")
    print(f"\nStats used: {result.stats_used}")

    if result.chart_png:
        path = Path("charts/live_single_take.png")
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(result.chart_png)
        print(f"\nChart saved to: {path} ({len(result.chart_png):,} bytes)")

    if result.chart_data:
        print(f"\nChart title: {result.chart_data.title}")
        for row in result.chart_data.rows:
            print(f"  {row.label}: {row.value_a}" + (f" vs {row.value_b}" if row.value_b is not None else ""))


if __name__ == "__main__":
    asyncio.run(main())
