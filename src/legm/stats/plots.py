"""Chart generation for LeGM take analysis — clean, minimal StatMuse-inspired."""

import io

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from legm.stats.models import ChartData, PlayerAdvancedStats, PlayerSeasonStats

matplotlib.use("Agg")

# -- Style constants --
_BG = "#0f1923"
_CARD_BG = "#162029"
_ROW_ALT = "#1a2733"
_TEXT = "#c8d6e0"
_TEXT_DIM = "#6b8298"
_TEXT_BRIGHT = "#ffffff"
_ACCENT_A = "#e05c44"  # warm coral-red
_ACCENT_B = "#4fc3f7"  # clean blue
_GREEN = "#4caf50"
_RED = "#ef5350"
_GOLD = "#ffb300"
_DIVIDER = "#263640"
_WATERMARK = "#ffffff08"

# NBA league averages (rough benchmarks for color-coding)
_LEAGUE_AVG = {
    "ppg": 23.0,
    "rpg": 6.0,
    "apg": 4.5,
    "fg_pct": 0.46,
    "fg3_pct": 0.36,
    "ft_pct": 0.78,
    "ts_pct": 0.575,
    "usg_pct": 0.20,
    "net_rating": 0.0,
    "pie": 0.10,
}


def _text(
    ax: plt.Axes,
    x: float,
    y: float,
    s: str,
    *,
    color: str = _TEXT,
    size: int = 12,
    weight: str = "normal",
    ha: str = "center",
    va: str = "center",
    family: str = "sans-serif",
) -> None:
    """Render text on axes (transAxes coordinates)."""
    ax.text(
        x, y, s,
        transform=ax.transAxes,
        ha=ha, va=va,
        color=color, fontsize=size, fontweight=weight,
        fontfamily=family,
    )


def _hline(ax: plt.Axes, y: float, x0: float = 0.04, x1: float = 0.96) -> None:
    """Draw a subtle horizontal divider line."""
    ax.plot(
        [x0, x1], [y, y],
        color=_DIVIDER, linewidth=0.7,
        transform=ax.transAxes, clip_on=False,
    )


def _row_bg(ax: plt.Axes, y: float, h: float, color: str) -> None:
    """Draw a filled row background band."""
    rect = FancyBboxPatch(
        (0.03, y - h / 2), 0.94, h,
        boxstyle="square,pad=0",
        transform=ax.transAxes,
        facecolor=color, edgecolor="none",
        zorder=0, clip_on=False,
    )
    ax.add_patch(rect)


def _watermark(ax: plt.Axes) -> None:
    """Subtle LeGM branding in bottom-right."""
    _text(ax, 0.96, 0.025, "LeGM", color=_WATERMARK, size=14, weight="bold", ha="right")


def _color_for(stat_key: str, value: float) -> str:
    """Return green/red/neutral color based on league-average comparison."""
    avg = _LEAGUE_AVG.get(stat_key)
    if avg is None:
        return _TEXT_BRIGHT
    if value > avg * 1.05:
        return _GREEN
    if value < avg * 0.95:
        return _RED
    return _TEXT_BRIGHT


def _fmt(val: float, is_pct: bool = False, is_plus: bool = False) -> str:
    """Format a stat value for display."""
    if is_pct:
        return f"{val:.1%}"
    if is_plus:
        return f"{val:+.1f}"
    return f"{val:.1f}"


# ---------------------------------------------------------------------------
# Comparison chart — clean table layout
# ---------------------------------------------------------------------------


def generate_comparison_chart(
    stats_a: PlayerSeasonStats,
    stats_b: PlayerSeasonStats,
    adv_a: PlayerAdvancedStats | None = None,
    adv_b: PlayerAdvancedStats | None = None,
) -> bytes:
    """Create a clean table-style comparison chart.

    Returns PNG image bytes at 200 DPI in 16:9 aspect ratio.
    """
    # Build stat rows: (label, val_a, val_b, is_pct, higher_is_better)
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
            ("Net Rtg", adv_a.net_rating, adv_b.net_rating, False, True),
        ])

    n_rows = len(rows)

    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)
    ax.axis("off")

    # -- Title block --
    _text(ax, 0.5, 0.94, f"{stats_a.player_name}  vs  {stats_b.player_name}",
          color=_TEXT_BRIGHT, size=26, weight="bold")

    season_text = stats_a.season
    if stats_a.season != stats_b.season:
        season_text = f"{stats_a.season} / {stats_b.season}"
    _text(ax, 0.5, 0.895, f"{stats_a.team}  |  {season_text}",
          color=_TEXT_DIM, size=13)

    # -- Table header --
    header_y = 0.83
    _hline(ax, header_y - 0.02)
    _text(ax, 0.20, header_y, "STAT", color=_TEXT_DIM, size=11, weight="bold", ha="center")
    _text(ax, 0.40, header_y, stats_a.player_name.split()[-1].upper(),
          color=_ACCENT_A, size=12, weight="bold", ha="center")
    _text(ax, 0.60, header_y, stats_b.player_name.split()[-1].upper(),
          color=_ACCENT_B, size=12, weight="bold", ha="center")
    _text(ax, 0.80, header_y, "EDGE", color=_TEXT_DIM, size=11, weight="bold", ha="center")
    _hline(ax, header_y - 0.035)

    # -- Stat rows --
    y_start = header_y - 0.08
    row_h = 0.065 if n_rows <= 7 else 0.055
    wins_a = 0
    wins_b = 0

    for i, (label, va, vb, is_pct, higher_better) in enumerate(rows):
        y = y_start - i * (row_h + 0.015)

        # Alternating row background
        if i % 2 == 0:
            _row_bg(ax, y, row_h, _ROW_ALT)

        # Determine winner
        a_wins = (va > vb) if higher_better else (va < vb)
        b_wins = (vb > va) if higher_better else (vb < va)
        if a_wins:
            wins_a += 1
        elif b_wins:
            wins_b += 1

        color_a = _TEXT_BRIGHT if a_wins else _TEXT
        color_b = _TEXT_BRIGHT if b_wins else _TEXT
        weight_a = "bold" if a_wins else "normal"
        weight_b = "bold" if b_wins else "normal"

        # Stat label
        _text(ax, 0.20, y, label, color=_TEXT_DIM, size=13, weight="bold", ha="center")

        # Values
        fmt_a = _fmt(va, is_pct=is_pct, is_plus=(label == "Net Rtg"))
        fmt_b = _fmt(vb, is_pct=is_pct, is_plus=(label == "Net Rtg"))
        _text(ax, 0.40, y, fmt_a, color=color_a, size=16, weight=weight_a, ha="center")
        _text(ax, 0.60, y, fmt_b, color=color_b, size=16, weight=weight_b, ha="center")

        # Winner arrow
        if a_wins:
            _text(ax, 0.80, y, "\u25c0", color=_ACCENT_A, size=14, ha="center")
        elif b_wins:
            _text(ax, 0.80, y, "\u25b6", color=_ACCENT_B, size=14, ha="center")
        else:
            _text(ax, 0.80, y, "\u2014", color=_TEXT_DIM, size=14, ha="center")

    # -- Bottom divider --
    bottom_y = y_start - n_rows * (row_h + 0.015) + 0.01
    _hline(ax, bottom_y)

    # -- Win tally --
    tally_y = bottom_y - 0.05
    _text(ax, 0.35, tally_y, f"\u25a0  {stats_a.player_name.split()[-1]} leads {wins_a}",
          color=_ACCENT_A, size=13, weight="bold", ha="center")
    _text(ax, 0.65, tally_y, f"\u25a0  {stats_b.player_name.split()[-1]} leads {wins_b}",
          color=_ACCENT_B, size=13, weight="bold", ha="center")

    _watermark(ax)
    return _fig_to_bytes(fig)


# ---------------------------------------------------------------------------
# Stat card — single player
# ---------------------------------------------------------------------------


def generate_stat_card(
    stats: PlayerSeasonStats,
    advanced: PlayerAdvancedStats | None = None,
) -> bytes:
    """Create a clean two-column stat card with color-coded values.

    Returns PNG image bytes at 200 DPI in 16:9 aspect ratio.
    """
    left_rows: list[tuple[str, str, str]] = [
        ("PPG", f"{stats.ppg}", _color_for("ppg", stats.ppg)),
        ("RPG", f"{stats.rpg}", _color_for("rpg", stats.rpg)),
        ("APG", f"{stats.apg}", _color_for("apg", stats.apg)),
        ("FG%", f"{stats.fg_pct:.1%}", _color_for("fg_pct", stats.fg_pct)),
        ("3P%", f"{stats.fg3_pct:.1%}", _color_for("fg3_pct", stats.fg3_pct)),
        ("FT%", f"{stats.ft_pct:.1%}", _color_for("ft_pct", stats.ft_pct)),
    ]

    right_rows: list[tuple[str, str, str]] = []
    if advanced:
        right_rows = [
            ("TS%", f"{advanced.ts_pct:.1%}", _color_for("ts_pct", advanced.ts_pct)),
            ("USG%", f"{advanced.usg_pct:.1%}", _color_for("usg_pct", advanced.usg_pct)),
            ("Net Rtg", f"{advanced.net_rating:+.1f}", _color_for("net_rating", advanced.net_rating)),
            ("PIE", f"{advanced.pie:.3f}", _color_for("pie", advanced.pie)),
            ("ORtg", f"{advanced.off_rating:.1f}", _TEXT_BRIGHT),
            ("DRtg", f"{advanced.def_rating:.1f}", _TEXT_BRIGHT),
        ]

    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)
    ax.axis("off")

    # -- Player name --
    _text(ax, 0.5, 0.94, stats.player_name.upper(),
          color=_TEXT_BRIGHT, size=28, weight="bold")

    # -- Hero PPG --
    _text(ax, 0.5, 0.84, f"{stats.ppg}",
          color=_GOLD, size=60, weight="bold")
    _text(ax, 0.5, 0.77, "PPG",
          color=_TEXT_DIM, size=13)

    # -- Meta line --
    _text(ax, 0.5, 0.72,
          f"{stats.team}  |  {stats.season}  |  {stats.games_played} GP  |  {stats.mpg} MPG",
          color=_TEXT_DIM, size=12)

    # -- Section headers --
    section_y = 0.65
    _text(ax, 0.25, section_y, "OFFENSE", color=_ACCENT_A, size=12, weight="bold")
    _hline(ax, section_y - 0.02, 0.06, 0.44)

    if right_rows:
        _text(ax, 0.75, section_y, "IMPACT", color=_ACCENT_B, size=12, weight="bold")
        _hline(ax, section_y - 0.02, 0.56, 0.94)

    # -- Stat rows --
    y_start = section_y - 0.065
    row_h = 0.07

    for i, (label, value, color) in enumerate(left_rows):
        y = y_start - i * row_h
        if i % 2 == 0:
            _row_bg(ax, y, row_h * 0.85, _ROW_ALT)
        _text(ax, 0.08, y, label, color=_TEXT_DIM, size=13, weight="bold", ha="left")
        _text(ax, 0.42, y, value, color=color, size=16, weight="bold", ha="right")

    for i, (label, value, color) in enumerate(right_rows):
        y = y_start - i * row_h
        if i % 2 == 0:
            _row_bg(ax, y, row_h * 0.85, _ROW_ALT)
        _text(ax, 0.58, y, label, color=_TEXT_DIM, size=13, weight="bold", ha="left")
        _text(ax, 0.92, y, value, color=color, size=16, weight="bold", ha="right")

    _watermark(ax)
    return _fig_to_bytes(fig)


# ---------------------------------------------------------------------------
# Flexible chart — agent-driven data
# ---------------------------------------------------------------------------

# Map display labels to _LEAGUE_AVG keys for color coding
_LABEL_TO_KEY: dict[str, str] = {
    "PPG": "ppg",
    "RPG": "rpg",
    "APG": "apg",
    "FG%": "fg_pct",
    "FG PCT": "fg_pct",
    "3P%": "fg3_pct",
    "3PT%": "fg3_pct",
    "FT%": "ft_pct",
    "TS%": "ts_pct",
    "USG%": "usg_pct",
    "NET RTG": "net_rating",
    "PIE": "pie",
}


def _normalize_label(label: str) -> str | None:
    """Map a display label like 'FG%' to the _LEAGUE_AVG key like 'fg_pct'."""
    return _LABEL_TO_KEY.get(label.upper().strip())


def _fmt_from_hint(val: float, fmt: str) -> str:
    """Format a value using the format hint from ChartRow."""
    if fmt == "percent":
        return f"{val:.1%}"
    if fmt == "plus":
        return f"{val:+.1f}"
    return f"{val:.1f}"


def generate_flexible_chart(chart_data: ChartData) -> bytes:
    """Create a chart from agent-provided ChartData.

    Comparison mode when label_b is set (two columns + EDGE arrows).
    Single-entity mode when label_b is None (one value column, color-coded).

    Returns PNG image bytes at 200 DPI in 16:9 aspect ratio.
    """
    is_comparison = chart_data.label_b is not None
    rows = chart_data.rows
    n_rows = len(rows)

    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)
    ax.axis("off")

    # -- Title --
    _text(ax, 0.5, 0.94, chart_data.title,
          color=_TEXT_BRIGHT, size=26, weight="bold")

    # -- Subtitle --
    subtitle_y = 0.895
    if chart_data.subtitle:
        _text(ax, 0.5, subtitle_y, chart_data.subtitle,
              color=_TEXT_DIM, size=13)

    if is_comparison:
        return _render_comparison(ax, fig, chart_data, rows, n_rows, subtitle_y)
    return _render_single(ax, fig, chart_data, rows, n_rows, subtitle_y)


def _render_comparison(
    ax: plt.Axes,
    fig: plt.Figure,
    chart_data: ChartData,
    rows: list,
    n_rows: int,
    subtitle_y: float,
) -> bytes:
    """Render comparison mode — two value columns + EDGE arrows."""
    # -- Table header --
    header_y = subtitle_y - 0.04
    _hline(ax, header_y - 0.02)

    # Short labels for column headers (last name or full label)
    name_a = chart_data.label_a.split()[-1].upper() if " " in chart_data.label_a else chart_data.label_a.upper()
    name_b = chart_data.label_b.split()[-1].upper() if chart_data.label_b and " " in chart_data.label_b else (chart_data.label_b or "").upper()

    _text(ax, 0.20, header_y, "STAT", color=_TEXT_DIM, size=11, weight="bold", ha="center")
    _text(ax, 0.40, header_y, name_a,
          color=_ACCENT_A, size=12, weight="bold", ha="center")
    _text(ax, 0.60, header_y, name_b,
          color=_ACCENT_B, size=12, weight="bold", ha="center")
    _text(ax, 0.80, header_y, "EDGE", color=_TEXT_DIM, size=11, weight="bold", ha="center")
    _hline(ax, header_y - 0.035)

    # -- Stat rows --
    y_start = header_y - 0.08
    row_h = 0.065 if n_rows <= 7 else 0.055
    wins_a = 0
    wins_b = 0

    for i, row in enumerate(rows):
        y = y_start - i * (row_h + 0.015)
        va = row.value_a
        vb = row.value_b if row.value_b is not None else 0.0

        if i % 2 == 0:
            _row_bg(ax, y, row_h, _ROW_ALT)

        a_wins = (va > vb) if row.higher_is_better else (va < vb)
        b_wins = (vb > va) if row.higher_is_better else (vb < va)
        if a_wins:
            wins_a += 1
        elif b_wins:
            wins_b += 1

        color_a = _TEXT_BRIGHT if a_wins else _TEXT
        color_b = _TEXT_BRIGHT if b_wins else _TEXT
        weight_a = "bold" if a_wins else "normal"
        weight_b = "bold" if b_wins else "normal"

        _text(ax, 0.20, y, row.label, color=_TEXT_DIM, size=13, weight="bold", ha="center")
        _text(ax, 0.40, y, _fmt_from_hint(va, row.fmt),
              color=color_a, size=16, weight=weight_a, ha="center")
        _text(ax, 0.60, y, _fmt_from_hint(vb, row.fmt),
              color=color_b, size=16, weight=weight_b, ha="center")

        if a_wins:
            _text(ax, 0.80, y, "\u25c0", color=_ACCENT_A, size=14, ha="center")
        elif b_wins:
            _text(ax, 0.80, y, "\u25b6", color=_ACCENT_B, size=14, ha="center")
        else:
            _text(ax, 0.80, y, "\u2014", color=_TEXT_DIM, size=14, ha="center")

    # -- Bottom divider + win tally --
    bottom_y = y_start - n_rows * (row_h + 0.015) + 0.01
    _hline(ax, bottom_y)

    tally_y = bottom_y - 0.05
    _text(ax, 0.35, tally_y,
          f"\u25a0  {chart_data.label_a.split()[-1]} leads {wins_a}",
          color=_ACCENT_A, size=13, weight="bold", ha="center")
    _text(ax, 0.65, tally_y,
          f"\u25a0  {(chart_data.label_b or '').split()[-1]} leads {wins_b}",
          color=_ACCENT_B, size=13, weight="bold", ha="center")

    _watermark(ax)
    return _fig_to_bytes(fig)


def _render_single(
    ax: plt.Axes,
    fig: plt.Figure,
    chart_data: ChartData,
    rows: list,
    n_rows: int,
    subtitle_y: float,
) -> bytes:
    """Render single-entity mode — one value column, color-coded."""
    # -- Entity name --
    _text(ax, 0.5, subtitle_y - 0.04, chart_data.label_a.upper(),
          color=_ACCENT_A, size=16, weight="bold")

    # -- Section header --
    section_y = subtitle_y - 0.10
    _hline(ax, section_y - 0.02, 0.15, 0.85)

    # -- Stat rows --
    y_start = section_y - 0.065
    row_h = 0.07

    for i, row in enumerate(rows):
        y = y_start - i * row_h

        if i % 2 == 0:
            _row_bg(ax, y, row_h * 0.85, _ROW_ALT)

        # Color based on league average if possible
        key = _normalize_label(row.label)
        if key:
            color = _color_for(key, row.value_a)
        else:
            color = _TEXT_BRIGHT

        _text(ax, 0.20, y, row.label, color=_TEXT_DIM, size=13, weight="bold", ha="left")
        _text(ax, 0.80, y, _fmt_from_hint(row.value_a, row.fmt),
              color=color, size=16, weight="bold", ha="right")

    _watermark(ax)
    return _fig_to_bytes(fig)


# ---------------------------------------------------------------------------
# Output helper
# ---------------------------------------------------------------------------


def _fig_to_bytes(fig: plt.Figure) -> bytes:
    """Render a matplotlib figure to PNG bytes at 200 DPI and close it."""
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=200,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    buf.seek(0)
    return buf.read()
