"""Run real takes through the full agent pipeline with a live LLM."""

import asyncio
from pathlib import Path

from legm.agent.analyzer import TakeAnalyzer
from legm.config import settings
from legm.llm.factory import create_llm_provider
from legm.stats.cache import TTLCache
from legm.stats.client import NBAClient
from legm.stats.service import NBAStatsService


async def run_take(analyzer: TakeAnalyzer, take: str, chart_name: str) -> None:
    """Analyze a single take and print results."""
    print(f"\n{'=' * 60}")
    print(f"TAKE: {take}")
    print(f"{'=' * 60}\n")

    result = await analyzer.analyze(take)

    print(f"Verdict: {result.verdict.upper()} (confidence: {result.confidence})")
    print(f"\nTweet:\n{result.roast}")
    print(f"\nReasoning:\n{result.reasoning}")
    print(f"\nStats used: {result.stats_used}")

    if result.chart_png:
        charts_dir = Path("charts")
        charts_dir.mkdir(exist_ok=True)
        path = charts_dir / f"{chart_name}.png"
        path.write_bytes(result.chart_png)
        print(f"\nChart saved to: {path} ({len(result.chart_png):,} bytes)")

    if result.chart_data:
        print(f"\nChart data title: {result.chart_data.title}")
        for row in result.chart_data.rows:
            print(f"  {row.label}: {row.value_a}" + (f" vs {row.value_b}" if row.value_b is not None else ""))
    else:
        print("\nNo chart_data returned by LLM")


async def main() -> None:
    llm = create_llm_provider(settings)
    stats_service = NBAStatsService(NBAClient(), TTLCache())
    analyzer = TakeAnalyzer(llm, stats_service)

    takes = [
        (
            "The Cavs 3-1 comeback against Warriors was rigged "
            "and refs gave Cavs an unfair advantage",
            "live_cavs_comeback",
        ),
        (
            "KD was the best player on the Warriors team",
            "live_kd_vs_steph",
        ),
    ]

    for take, chart_name in takes:
        await run_take(analyzer, take, chart_name)


if __name__ == "__main__":
    asyncio.run(main())
