"""Demo: analyze "The Cavs 3-1 comeback was rigged, refs gave Cavs unfair advantage"."""

import json
from pathlib import Path

from legm.stats.models import (
    ChartData,
    ChartRow,
    PlayerAdvancedStats,
    PlayerSeasonStats,
)
from legm.stats.plots import (
    generate_comparison_chart,
    generate_flexible_chart,
    generate_stat_card,
)

# --- 2016 Finals data (LeBron vs Steph) ---

# LeBron's 2015-16 regular season
lebron_basic = PlayerSeasonStats(
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
    plus_minus=10.1,
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
    ast_ratio=35.2,
    tov_pct=0.140,
    pace=93.4,
    pie=0.196,
)

# Steph's unanimous MVP 2015-16 season
steph_basic = PlayerSeasonStats(
    player_name="Stephen Curry",
    player_id=201939,
    season="2015-16",
    team="GSW",
    games_played=79,
    mpg=34.2,
    ppg=30.1,
    rpg=5.4,
    apg=6.7,
    spg=2.1,
    bpg=0.2,
    fg_pct=0.504,
    fg3_pct=0.454,
    ft_pct=0.908,
    turnovers=3.3,
    plus_minus=12.5,
)

steph_adv = PlayerAdvancedStats(
    player_name="Stephen Curry",
    player_id=201939,
    season="2015-16",
    team="GSW",
    ts_pct=0.669,
    efg_pct=0.630,
    usg_pct=0.321,
    off_rating=124.5,
    def_rating=103.8,
    net_rating=20.7,
    ast_ratio=33.9,
    tov_pct=0.133,
    pace=99.3,
    pie=0.218,
)

take = (
    "The Cavs 3-1 comeback against Warriors was rigged "
    "and refs gave Cavs an unfair advantage"
)

# --- Generate charts ---
charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

# LeBron vs Steph comparison
comp_bytes = generate_comparison_chart(lebron_basic, steph_basic, lebron_adv, steph_adv)
comp_path = charts_dir / "demo_lebron_vs_steph_2016.png"
comp_path.write_bytes(comp_bytes)
print(f"Comparison saved to: {comp_path} ({len(comp_bytes):,} bytes)")

# LeBron stat card
lbj_card = generate_stat_card(lebron_basic, lebron_adv)
lbj_path = charts_dir / "demo_lebron_card_2016.png"
lbj_path.write_bytes(lbj_card)
print(f"LeBron card saved to: {lbj_path} ({len(lbj_card):,} bytes)")

# Steph stat card
sc_card = generate_stat_card(steph_basic, steph_adv)
sc_path = charts_dir / "demo_steph_card_2016.png"
sc_path.write_bytes(sc_card)
print(f"Steph card saved to: {sc_path} ({len(sc_card):,} bytes)")

# --- Simulated LeGM response ---
# This is what the agent WOULD produce with the Basketball IQ prompt
analysis = {
    "verdict": "trash",
    "confidence": 0.92,
    "roast": (
        "Bro the refs rigged LeBron averaging 29.7/11.3/8.9 in the Finals "
        "with a Game 7 triple-double and THE Block?? Steph shot 40% from the "
        "field in the last 3 games. The refs didn't do that dawg 💀"
    ),
    "reasoning": (
        "The 'rigged' narrative ignores what actually happened on the court. "
        "LeBron led BOTH teams in points, rebounds, assists, steals, and blocks "
        "across the 7-game series — the only player in Finals history to do that. "
        "His Game 5-7 averages: 36.3/11.7/9.3. Meanwhile Steph shot 40.3% FG in "
        "the final 3 games and had 4+ turnovers in 3 of the last 4. Draymond's "
        "suspension in Game 5 was self-inflicted (accumulated flagrants). Bogut's "
        "injury hurt, but Cleveland also lost Kevin Love to injury in 2015 and "
        "nobody called that rigged. The Warriors blew a 3-1 lead because LeBron "
        "played historically great basketball and Steph/Klay couldn't sustain "
        "their shooting. Free throw disparity was 150-148 across the series — "
        "basically even. This take is pure cope."
    ),
    "stats_used": [
        "LeBron Finals: 29.7 PPG / 11.3 RPG / 8.9 APG / 2.6 SPG / 2.3 BPG",
        "Steph Finals: 22.6 PPG / 4.9 RPG / 3.7 APG / .403 FG% Games 5-7",
        "Series FT disparity: CLE 150 — GSW 148 (virtually even)",
        "LeBron Game 7: 27/11/11 triple-double + The Block + The Drive",
    ],
}

# --- Agent-driven flexible chart (Finals G5-7 context) ---
finals_chart_data = ChartData(
    title="2016 NBA Finals — Games 5-7",
    subtitle="LeBron vs Steph when it mattered most",
    label_a="LeBron James",
    label_b="Stephen Curry",
    rows=[
        ChartRow(label="PPG", value_a=36.3, value_b=22.4, fmt="number"),
        ChartRow(label="RPG", value_a=11.7, value_b=4.8, fmt="number"),
        ChartRow(label="APG", value_a=9.3, value_b=3.7, fmt="number"),
        ChartRow(label="FG%", value_a=0.487, value_b=0.403, fmt="percent"),
        ChartRow(label="FTs", value_a=150, value_b=148, fmt="number"),
    ],
)

flex_bytes = generate_flexible_chart(finals_chart_data)
flex_path = charts_dir / "demo_finals_g5_7_flexible.png"
flex_path.write_bytes(flex_bytes)
print(f"Flexible chart saved to: {flex_path} ({len(flex_bytes):,} bytes)")

print(f"\n{'=' * 60}")
print(f"Take: {take}")
print(f"{'=' * 60}")
print(json.dumps(analysis, indent=2))
