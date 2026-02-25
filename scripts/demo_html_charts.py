"""Generate demo charts using the HTML renderer.

Usage:
    uv run python scripts/demo_html_charts.py
"""

from pathlib import Path

from legm.stats.html_renderer import (
    generate_comparison_chart,
    generate_stat_card,
    generate_verdict_card,
)
from legm.stats.models import PlayerAdvancedStats, PlayerSeasonStats

CHARTS_DIR = Path("charts")
CHARTS_DIR.mkdir(exist_ok=True)


def main() -> None:
    # -- KD vs Steph (2018-19 GSW) --
    kd = PlayerSeasonStats(
        player_name="Kevin Durant",
        player_id=201142,
        season="2018-19",
        team="GSW",
        games_played=78,
        mpg=34.6,
        ppg=26.0,
        rpg=6.4,
        apg=5.9,
        spg=0.7,
        bpg=1.1,
        fg_pct=0.521,
        fg3_pct=0.353,
        ft_pct=0.885,
        turnovers=2.7,
        plus_minus=6.4,
    )
    kd_adv = PlayerAdvancedStats(
        player_name="Kevin Durant",
        player_id=201142,
        season="2018-19",
        team="GSW",
        ts_pct=0.631,
        efg_pct=0.567,
        usg_pct=0.303,
        off_rating=118.8,
        def_rating=107.3,
        net_rating=11.5,
        ast_ratio=0.286,
        tov_pct=0.115,
        pace=100.9,
        pie=0.184,
    )

    steph = PlayerSeasonStats(
        player_name="Stephen Curry",
        player_id=201939,
        season="2018-19",
        team="GSW",
        games_played=69,
        mpg=33.8,
        ppg=27.3,
        rpg=5.3,
        apg=5.2,
        spg=1.3,
        bpg=0.4,
        fg_pct=0.472,
        fg3_pct=0.437,
        ft_pct=0.916,
        turnovers=2.8,
        plus_minus=7.1,
    )
    steph_adv = PlayerAdvancedStats(
        player_name="Stephen Curry",
        player_id=201939,
        season="2018-19",
        team="GSW",
        ts_pct=0.640,
        efg_pct=0.566,
        usg_pct=0.311,
        off_rating=120.2,
        def_rating=107.1,
        net_rating=13.1,
        ast_ratio=0.291,
        tov_pct=0.121,
        pace=101.5,
        pie=0.178,
    )

    # -- LeBron 2015-16 --
    lebron = PlayerSeasonStats(
        player_name="LeBron James",
        player_id=2544,
        season="2015-16",
        team="CLE",
        games_played=76,
        mpg=35.6,
        ppg=25.3,
        rpg=7.4,
        apg=6.8,
        spg=1.4,
        bpg=0.6,
        fg_pct=0.520,
        fg3_pct=0.309,
        ft_pct=0.731,
        turnovers=3.3,
        plus_minus=4.5,
    )
    lebron_adv = PlayerAdvancedStats(
        player_name="LeBron James",
        player_id=2544,
        season="2015-16",
        team="CLE",
        ts_pct=0.588,
        efg_pct=0.551,
        usg_pct=0.316,
        off_rating=113.9,
        def_rating=103.7,
        net_rating=10.2,
        ast_ratio=0.312,
        tov_pct=0.130,
        pace=96.1,
        pie=0.196,
    )

    # 1. Comparison chart
    print("Generating comparison chart (KD vs Steph)...")
    png = generate_comparison_chart(kd, steph, kd_adv, steph_adv)
    (CHARTS_DIR / "html_comparison.png").write_bytes(png)
    print(f"  -> charts/html_comparison.png ({len(png):,} bytes)")

    # 2. Stat card
    print("Generating stat card (LeBron 2015-16)...")
    png = generate_stat_card(lebron, lebron_adv)
    (CHARTS_DIR / "html_stat_card.png").write_bytes(png)
    print(f"  -> charts/html_stat_card.png ({len(png):,} bytes)")

    # 3. Verdict card
    print("Generating verdict card...")
    png = generate_verdict_card(
        take_text="LeBron is washed, he can't even carry a team anymore",
        verdict="trash",
        confidence=0.94,
        roast=(
            "Bro averaged 25.7/7.3/8.3 last season on 54% TS at age 40. "
            "Your take is washed, not LeBron. Respectfully."
        ),
        stats_used=[
            "Season Averages 2024-25",
            "Advanced Stats",
            "Game Log (Last 10)",
        ],
        player_id=2544,
    )
    (CHARTS_DIR / "html_verdict.png").write_bytes(png)
    print(f"  -> charts/html_verdict.png ({len(png):,} bytes)")

    # 4. Stat card without advanced stats
    print("Generating stat card (Steph, basic only)...")
    png = generate_stat_card(steph)
    (CHARTS_DIR / "html_stat_card_basic.png").write_bytes(png)
    print(f"  -> charts/html_stat_card_basic.png ({len(png):,} bytes)")

    print("\nDone! All charts in charts/")


if __name__ == "__main__":
    main()
