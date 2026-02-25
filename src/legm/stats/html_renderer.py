"""HTML-based chart renderer using Playwright for screenshot capture.

Renders Jinja2 HTML templates to PNG images for Twitter/web use.
Templates live in src/legm/stats/templates/ and use team colors,
player headshots, and modern sports-graphic design.
"""

import logging
import tempfile
from pathlib import Path

import httpx
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from legm.stats.models import (
    ChartData,
    PlayerAdvancedStats,
    PlayerSeasonStats,
)

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=False)

# -- Team colors: (primary, secondary) --
_TEAM_COLORS: dict[str, tuple[str, str]] = {
    "ATL": ("#e03a3e", "#c1d32f"),
    "BOS": ("#007a33", "#ba9653"),
    "BKN": ("#000000", "#ffffff"),
    "CHA": ("#1d1160", "#00788c"),
    "CHI": ("#ce1141", "#000000"),
    "CLE": ("#860038", "#fdbb30"),
    "DAL": ("#00538c", "#002b5e"),
    "DEN": ("#0e2240", "#fec524"),
    "DET": ("#c8102e", "#1d42ba"),
    "GSW": ("#1d428a", "#ffc72c"),
    "HOU": ("#ce1141", "#000000"),
    "IND": ("#002d62", "#fdbb30"),
    "LAC": ("#c8102e", "#1d428a"),
    "LAL": ("#552583", "#fdb927"),
    "MEM": ("#5d76a9", "#12173f"),
    "MIA": ("#98002e", "#f9a01b"),
    "MIL": ("#00471b", "#eee1c6"),
    "MIN": ("#0c2340", "#236192"),
    "NOP": ("#0c2340", "#c8102e"),
    "NYK": ("#006bb6", "#f58426"),
    "OKC": ("#007ac1", "#ef6136"),
    "ORL": ("#0077c0", "#c4ced4"),
    "PHI": ("#006bb6", "#ed174c"),
    "PHX": ("#1d1160", "#e56020"),
    "POR": ("#e03a3e", "#000000"),
    "SAC": ("#5a2d81", "#63727a"),
    "SAS": ("#c4ced4", "#000000"),
    "TOR": ("#ce1141", "#000000"),
    "UTA": ("#002b5c", "#00471b"),
    "WAS": ("#002b5c", "#e31837"),
}

_VERDICT_STYLES: dict[str, tuple[str, str]] = {
    "trash": ("#ef5350", "#1a0a0a"),
    "mid": ("#ffb300", "#1a150a"),
    "valid": ("#4caf50", "#0a1a0d"),
}

_LEAGUE_AVG: dict[str, float] = {
    "ppg": 23.0, "rpg": 6.0, "apg": 4.5,
    "fg_pct": 0.46, "fg3_pct": 0.36, "ft_pct": 0.78,
    "ts_pct": 0.575, "usg_pct": 0.20,
}

# Headshot cache
_headshot_cache: dict[int, str | None] = {}


def _darken(hex_color: str, factor: float) -> str:
    hex_color = hex_color.lstrip("#")
    r = int(int(hex_color[0:2], 16) * factor)
    g = int(int(hex_color[2:4], 16) * factor)
    b = int(int(hex_color[4:6], 16) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def _get_team_colors(team: str) -> tuple[str, str]:
    return _TEAM_COLORS.get(team, ("#4488aa", "#335577"))


def _fetch_headshot(player_id: int) -> str | None:
    """Download headshot, return local file path or None."""
    if player_id in _headshot_cache:
        return _headshot_cache[player_id]

    url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"
    try:
        resp = httpx.get(url, timeout=5.0, follow_redirects=True)
        resp.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(resp.content)
        _headshot_cache[player_id] = tmp.name
        return tmp.name
    except Exception:
        logger.debug("Failed to fetch headshot for player_id=%d", player_id)
        _headshot_cache[player_id] = None
        return None


def _stat_color(key: str, value: float) -> str:
    avg = _LEAGUE_AVG.get(key)
    if avg is None:
        return "#b0bec5"
    ratio = value / avg if avg != 0 else 1.0
    if ratio > 1.10:
        return "#4caf50"
    if ratio > 1.02:
        return "#81c784"
    if ratio < 0.90:
        return "#ef5350"
    if ratio < 0.98:
        return "#e57373"
    return "#b0bec5"


def _stat_bar_pct(value: float, max_val: float) -> float:
    """Calculate bar width as percentage (0-100)."""
    if max_val == 0:
        return 0
    return min(100, max(5, (value / max_val) * 100))


def _fmt(val: float, *, is_pct: bool = False, is_plus: bool = False) -> str:
    if is_pct:
        return f"{val:.1%}"
    if is_plus:
        return f"{val:+.1f}"
    return f"{val:.1f}"


def _render_html_to_png(
    html: str,
    width: int,
    height: int,
    *,
    device_scale_factor: int = 2,
) -> bytes:
    """Render an HTML string to PNG bytes using Playwright."""
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        f.write(html)
        html_path = f.name

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=device_scale_factor,
        )
        page.goto(f"file://{html_path}")
        # Wait for fonts to load
        page.wait_for_load_state("networkidle")
        png_bytes = page.screenshot(type="png")
        browser.close()

    return png_bytes


# ---------------------------------------------------------------------------
# Public API: Comparison chart
# ---------------------------------------------------------------------------


def generate_comparison_chart(
    stats_a: PlayerSeasonStats,
    stats_b: PlayerSeasonStats,
    adv_a: PlayerAdvancedStats | None = None,
    adv_b: PlayerAdvancedStats | None = None,
) -> bytes:
    """Render a comparison chart as PNG. Returns bytes."""
    color_a_primary, color_a_secondary = _get_team_colors(stats_a.team)
    color_b_primary, color_b_secondary = _get_team_colors(stats_b.team)

    rows: list[tuple[str, float, float, bool, bool]] = [
        ("PPG", stats_a.ppg, stats_b.ppg, False, True),
        ("RPG", stats_a.rpg, stats_b.rpg, False, True),
        ("APG", stats_a.apg, stats_b.apg, False, True),
        ("FG%", stats_a.fg_pct, stats_b.fg_pct, True, True),
    ]
    if adv_a and adv_b:
        rows.extend([
            ("TS%", adv_a.ts_pct, adv_b.ts_pct, True, True),
            ("USG%", adv_a.usg_pct, adv_b.usg_pct, True, True),
            ("NET RTG", adv_a.net_rating, adv_b.net_rating, False, True),
        ])

    wins_a = 0
    wins_b = 0
    stat_data = []
    for label, va, vb, is_pct, higher_better in rows:
        a_wins = (va > vb) if higher_better else (va < vb)
        b_wins = (vb > va) if higher_better else (vb < va)
        if a_wins:
            wins_a += 1
        elif b_wins:
            wins_b += 1

        max_val = max(abs(va), abs(vb), 0.001)
        stat_data.append({
            "label": label,
            "fmt_a": _fmt(va, is_pct=is_pct, is_plus=(label == "NET RTG")),
            "fmt_b": _fmt(vb, is_pct=is_pct, is_plus=(label == "NET RTG")),
            "a_wins": a_wins,
            "b_wins": b_wins,
            "bar_pct_a": _stat_bar_pct(abs(va), max_val),
            "bar_pct_b": _stat_bar_pct(abs(vb), max_val),
        })

    headshot_a = _fetch_headshot(stats_a.player_id)
    headshot_b = _fetch_headshot(stats_b.player_id)

    season_text = stats_a.season
    if stats_a.season != stats_b.season:
        season_text = f"{stats_a.season} / {stats_b.season}"

    template = _env.get_template("comparison.html")
    html = template.render(
        name_a=stats_a.player_name,
        name_b=stats_b.player_name,
        name_a_short=stats_a.player_name.split()[-1],
        name_b_short=stats_b.player_name.split()[-1],
        meta_a=f"{stats_a.team} | {stats_a.season}",
        meta_b=f"{stats_b.team} | {stats_b.season}",
        subtitle=season_text,
        headshot_a=headshot_a or "",
        headshot_b=headshot_b or "",
        color_a=color_a_primary,
        color_b=color_b_primary,
        bg_color_a=_darken(color_a_primary, 0.15),
        bg_dark_a=_darken(color_a_primary, 0.12),
        bg_dark_b=_darken(color_b_primary, 0.12),
        glow_a=color_a_primary,
        glow_b=color_b_primary,
        stats=stat_data,
        wins_a=wins_a,
        wins_b=wins_b,
    )

    return _render_html_to_png(html, 1200, 675)


# ---------------------------------------------------------------------------
# Public API: Stat card
# ---------------------------------------------------------------------------


def generate_stat_card(
    stats: PlayerSeasonStats,
    advanced: PlayerAdvancedStats | None = None,
) -> bytes:
    """Render a single-player stat card as PNG. Returns bytes."""
    color_primary, color_secondary = _get_team_colors(stats.team)

    stat_rows: list[tuple[str, str, float, str]] = [
        ("PPG", f"{stats.ppg}", stats.ppg, "ppg"),
        ("RPG", f"{stats.rpg}", stats.rpg, "rpg"),
        ("APG", f"{stats.apg}", stats.apg, "apg"),
        ("FG%", f"{stats.fg_pct:.1%}", stats.fg_pct, "fg_pct"),
        ("3P%", f"{stats.fg3_pct:.1%}", stats.fg3_pct, "fg3_pct"),
        ("FT%", f"{stats.ft_pct:.1%}", stats.ft_pct, "ft_pct"),
    ]

    if advanced:
        stat_rows.extend([
            ("TS%", f"{advanced.ts_pct:.1%}", advanced.ts_pct, "ts_pct"),
            ("USG%", f"{advanced.usg_pct:.1%}", advanced.usg_pct, "usg_pct"),
            (
                "NET RTG",
                f"{advanced.net_rating:+.1f}",
                advanced.net_rating,
                "net_rating",
            ),
        ])

    # Compute bar percentages (relative to reasonable maximums)
    max_vals = {
        "ppg": 35.0, "rpg": 15.0, "apg": 12.0,
        "fg_pct": 1.0, "fg3_pct": 1.0, "ft_pct": 1.0,
        "ts_pct": 1.0, "usg_pct": 0.40, "net_rating": 15.0,
    }

    stat_data = []
    for label, display, value, key in stat_rows:
        max_val = max_vals.get(key, 30.0)
        stat_data.append({
            "label": label,
            "display": display,
            "bar_pct": _stat_bar_pct(abs(value), max_val),
            "color": _stat_color(key, value),
        })

    headshot = _fetch_headshot(stats.player_id)

    template = _env.get_template("stat_card.html")
    html = template.render(
        player_name=stats.player_name,
        meta=(
            f"{stats.team} | {stats.season}"
            f" | {stats.games_played} GP | {stats.mpg} MPG"
        ),
        headshot_url=headshot or "",
        hero_value=f"{stats.ppg}",
        hero_label="PPG",
        color_primary=color_primary,
        color_secondary=color_secondary,
        bg_dark=_darken(color_primary, 0.12),
        bg_dark_secondary=_darken(color_secondary, 0.12),
        stats=stat_data,
    )

    return _render_html_to_png(html, 680, 880)


# ---------------------------------------------------------------------------
# Public API: Verdict card
# ---------------------------------------------------------------------------


def generate_verdict_card(
    take_text: str,
    verdict: str,
    confidence: float,
    roast: str,
    stats_used: list[str] | None = None,
    player_id: int | None = None,
) -> bytes:
    """Render a verdict card for a take analysis. Returns PNG bytes."""
    verdict_lower = verdict.lower().strip()
    verdict_color, verdict_bg = _VERDICT_STYLES.get(
        verdict_lower, ("#4488aa", "#0a1117")
    )

    headshot = _fetch_headshot(player_id) if player_id else None

    template = _env.get_template("verdict.html")
    html = template.render(
        take_text=take_text,
        verdict=verdict.upper(),
        confidence_pct=int(confidence * 100),
        roast=roast,
        headshot_url=headshot or "",
        verdict_color=verdict_color,
        verdict_bg_tint=verdict_bg,
        stats_used=stats_used or [],
    )

    return _render_html_to_png(html, 1200, 675)


# ---------------------------------------------------------------------------
# Public API: Flexible chart (agent-driven)
# ---------------------------------------------------------------------------


def generate_flexible_chart(chart_data: ChartData) -> bytes:
    """Render a flexible chart from agent-provided ChartData. Returns PNG bytes."""
    if chart_data.label_b is not None:
        return _render_flexible_comparison(chart_data)
    return _render_flexible_single(chart_data)


def _render_flexible_comparison(chart_data: ChartData) -> bytes:
    """Render a flexible comparison using the comparison template."""
    wins_a = 0
    wins_b = 0
    stat_data = []

    for row in chart_data.rows:
        va = row.value_a
        vb = row.value_b if row.value_b is not None else 0.0
        a_wins = (va > vb) if row.higher_is_better else (va < vb)
        b_wins = (vb > va) if row.higher_is_better else (vb < va)
        if a_wins:
            wins_a += 1
        elif b_wins:
            wins_b += 1

        max_val = max(abs(va), abs(vb), 0.001)
        is_pct = row.fmt == "percent"
        is_plus = row.fmt == "plus"

        stat_data.append({
            "label": row.label,
            "fmt_a": _fmt(va, is_pct=is_pct, is_plus=is_plus),
            "fmt_b": _fmt(vb, is_pct=is_pct, is_plus=is_plus),
            "a_wins": a_wins,
            "b_wins": b_wins,
            "bar_pct_a": _stat_bar_pct(abs(va), max_val),
            "bar_pct_b": _stat_bar_pct(abs(vb), max_val),
        })

    name_a_short = chart_data.label_a.split()[-1]
    name_b_short = (chart_data.label_b or "").split()[-1]

    template = _env.get_template("comparison.html")
    html = template.render(
        name_a=chart_data.label_a,
        name_b=chart_data.label_b,
        name_a_short=name_a_short,
        name_b_short=name_b_short,
        meta_a="",
        meta_b="",
        subtitle=chart_data.subtitle or "",
        headshot_a="",
        headshot_b="",
        color_a="#e05c44",
        color_b="#4fc3f7",
        bg_color_a="#1a0c08",
        bg_dark_a="#1a0c08",
        bg_dark_b="#081218",
        glow_a="#e05c44",
        glow_b="#4fc3f7",
        stats=stat_data,
        wins_a=wins_a,
        wins_b=wins_b,
    )

    return _render_html_to_png(html, 1200, 675)


def _render_flexible_single(chart_data: ChartData) -> bytes:
    """Render a single-entity flexible chart using the stat card template."""
    stat_data = []
    for row in chart_data.rows:
        is_pct = row.fmt == "percent"
        is_plus = row.fmt == "plus"
        display = _fmt(row.value_a, is_pct=is_pct, is_plus=is_plus)
        stat_data.append({
            "label": row.label,
            "display": display,
            "bar_pct": min(100, max(5, abs(row.value_a) / 35 * 100)),
            "color": "#ffffff",
        })

    template = _env.get_template("stat_card.html")
    html = template.render(
        player_name=chart_data.label_a,
        meta=chart_data.subtitle or "",
        headshot_url="",
        hero_value=stat_data[0]["display"] if stat_data else "",
        hero_label=stat_data[0]["label"] if stat_data else "",
        color_primary="#4488aa",
        color_secondary="#335577",
        bg_dark="#0a1520",
        bg_dark_secondary="#0a1218",
        stats=stat_data,
    )

    return _render_html_to_png(html, 680, 880)
