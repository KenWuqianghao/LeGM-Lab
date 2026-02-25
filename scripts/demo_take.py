"""Demo script: analyze "KD was the best player on the Warriors team"."""

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

# KD's best Warriors season (2018-19) — realistic stats
kd_basic = PlayerSeasonStats(
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
    turnovers=2.9,
    plus_minus=6.4,
)

kd_adv = PlayerAdvancedStats(
    player_name="Kevin Durant",
    player_id=201142,
    season="2018-19",
    team="GSW",
    ts_pct=0.631,
    efg_pct=0.568,
    usg_pct=0.303,
    off_rating=118.8,
    def_rating=107.3,
    net_rating=11.5,
    ast_ratio=28.6,
    tov_pct=0.124,
    pace=100.8,
    pie=0.178,
)

# Steph's same season (2018-19)
steph_basic = PlayerSeasonStats(
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
    plus_minus=8.0,
)

steph_adv = PlayerAdvancedStats(
    player_name="Stephen Curry",
    player_id=201939,
    season="2018-19",
    team="GSW",
    ts_pct=0.640,
    efg_pct=0.580,
    usg_pct=0.311,
    off_rating=121.3,
    def_rating=108.2,
    net_rating=13.1,
    ast_ratio=27.4,
    tov_pct=0.118,
    pace=101.2,
    pie=0.168,
)

# Generate the comparison chart
chart_bytes = generate_comparison_chart(kd_basic, steph_basic, kd_adv, steph_adv)
chart_path = Path("charts/demo_kd_vs_steph.png")
chart_path.parent.mkdir(exist_ok=True)
chart_path.write_bytes(chart_bytes)
print(f"Chart saved to: {chart_path} ({len(chart_bytes):,} bytes)")

# Also generate individual stat cards
kd_card = generate_stat_card(kd_basic, kd_adv)
kd_card_path = Path("charts/demo_kd_card.png")
kd_card_path.write_bytes(kd_card)
print(f"KD stat card saved to: {kd_card_path} ({len(kd_card):,} bytes)")

steph_card = generate_stat_card(steph_basic, steph_adv)
steph_card_path = Path("charts/demo_steph_card.png")
steph_card_path.write_bytes(steph_card)
print(f"Steph stat card saved to: {steph_card_path} ({len(steph_card):,} bytes)")

# Simulated LeGM analysis response
analysis = {
    "verdict": "mid",
    "confidence": 0.65,
    "roast": (
        "Bro really said KD was the best Warrior when Steph had a .640 TS% "
        "and +13.1 net rating vs KD's .631 TS% and +11.5 💀 "
        "KD was a cheat code but Steph was literally the system dawg"
    ),
    "reasoning": (
        "While KD was an elite scorer on GSW, Steph's 2018-19 season had "
        "higher true shooting (.640 vs .631), better net rating (+13.1 vs +11.5), "
        "and the Warriors' offensive rating historically cratered more without Steph "
        "than without KD. KD was incredible, but 'best player' is a stretch "
        "when Steph's gravity ran the offense."
    ),
    "stats_used": [
        "KD 26.0 PPG / .631 TS% / +11.5 net rating",
        "Steph 27.3 PPG / .640 TS% / +13.1 net rating",
    ],
}

# --- Agent-driven flexible chart (KD vs Steph) ---
kd_steph_chart = ChartData(
    title="KD vs Steph — 2018-19 Warriors",
    subtitle="Who was really the best player on this team?",
    label_a="Kevin Durant",
    label_b="Stephen Curry",
    rows=[
        ChartRow(label="PPG", value_a=26.0, value_b=27.3, fmt="number"),
        ChartRow(label="TS%", value_a=0.631, value_b=0.640, fmt="percent"),
        ChartRow(label="Net Rtg", value_a=11.5, value_b=13.1, fmt="plus"),
        ChartRow(label="USG%", value_a=0.303, value_b=0.311, fmt="percent"),
        ChartRow(label="PIE", value_a=0.178, value_b=0.168, fmt="number"),
    ],
)

flex_bytes = generate_flexible_chart(kd_steph_chart)
flex_path = Path("charts/demo_kd_vs_steph_flexible.png")
flex_path.write_bytes(flex_bytes)
print(f"Flexible chart saved to: {flex_path} ({len(flex_bytes):,} bytes)")

print("\n" + "=" * 60)
print("LeGM Analysis")
print("=" * 60)
print(json.dumps(analysis, indent=2))
