"""Chart generation for LeGM take analysis — PicTex-powered stat cards.

StatMuse-inspired design with player headshots, team-colored gradients,
and dynamic canvas sizing.
"""

import io
import logging
import tempfile

import httpx
from pictex import (
    Canvas,
    Column,
    Image,
    LinearGradient,
    Row,
    Shadow,
    Text,
    TextAlign,
)

from legm.stats.models import ChartData, PlayerAdvancedStats, PlayerSeasonStats

logger = logging.getLogger(__name__)

# -- Team colors: (primary, secondary) per abbreviation --
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

# -- Design tokens --
_CARD_BG = "#162029"
_ROW_EVEN = "#1a2733"
_ROW_ODD = "#162029"
_TEXT = "#c8d6e0"
_TEXT_DIM = "#6b8298"
_TEXT_BRIGHT = "#ffffff"
_ACCENT_A = "#e05c44"
_ACCENT_B = "#4fc3f7"
_GREEN = "#4caf50"
_RED = "#ef5350"
_GOLD = "#ffb300"
_DIVIDER = "#263640"

# NBA league averages for color-coding
_LEAGUE_AVG: dict[str, float] = {
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

_CANVAS_W = 1200
_HEADSHOT_BADGE = 56
_HEADSHOT_CARD = 90

# -- Headshot cache --
_headshot_cache: dict[int, str | None] = {}


def _get_team_colors(team: str) -> tuple[str, str]:
    """Return (primary, secondary) color for a team abbreviation."""
    return _TEAM_COLORS.get(team, ("#0f1923", "#152232"))


def _team_gradient(team: str) -> LinearGradient:
    """Create a subtle dark gradient tinted with team colors."""
    primary, secondary = _get_team_colors(team)
    return LinearGradient(
        colors=[_darken(primary, 0.25), "#0f1923", _darken(secondary, 0.25)],
        start_point=(0.0, 0.0),
        end_point=(1.0, 1.0),
    )


def _dual_team_gradient(team_a: str, team_b: str) -> LinearGradient:
    """Create a gradient blending both teams' primary colors (darkened)."""
    primary_a, _ = _get_team_colors(team_a)
    primary_b, _ = _get_team_colors(team_b)
    return LinearGradient(
        colors=[_darken(primary_a, 0.3), "#0f1923", _darken(primary_b, 0.3)],
        start_point=(0.0, 0.0),
        end_point=(1.0, 1.0),
    )


def _darken(hex_color: str, factor: float) -> str:
    """Darken a hex color by a factor (0.0 = black, 1.0 = original)."""
    hex_color = hex_color.lstrip("#")
    r = int(int(hex_color[0:2], 16) * factor)
    g = int(int(hex_color[2:4], 16) * factor)
    b = int(int(hex_color[4:6], 16) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def _fetch_headshot(player_id: int) -> str | None:
    """Download a player headshot and return the temp file path, or None on failure.

    Results are cached in-memory so each player is fetched at most once.
    """
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


def _headshot_image(player_id: int, size: int = _HEADSHOT_BADGE) -> Image | None:
    """Return a PicTex Image builder for the player headshot, or None."""
    path = _fetch_headshot(player_id)
    if path is None:
        return None
    return Image(path).size(width=size, height=int(size * 760 / 1040))


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


def _fmt(val: float, *, is_pct: bool = False, is_plus: bool = False) -> str:
    if is_pct:
        return f"{val:.1%}"
    if is_plus:
        return f"{val:+.1f}"
    return f"{val:.1f}"


def _fmt_from_hint(val: float, fmt: str) -> str:
    if fmt == "percent":
        return f"{val:.1%}"
    if fmt == "plus":
        return f"{val:+.1f}"
    return f"{val:.1f}"


def _render_to_bytes(canvas: Canvas, *builders: Column | Row) -> bytes:
    """Render a PicTex canvas to PNG bytes."""
    image = canvas.render(*builders, scale_factor=2)
    pil = image.to_pillow()
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def _make_canvas(height: int, background: LinearGradient | None = None) -> Canvas:
    """Create a LeGM canvas with dynamic height and optional team gradient."""
    bg = background or LinearGradient(
        colors=["#0f1923", "#152232", "#0f1923"],
        start_point=(0.0, 0.0),
        end_point=(1.0, 1.0),
    )
    return (
        Canvas()
        .font_family("Arial")
        .color(_TEXT)
        .background_color(bg)
        .size(width=_CANVAS_W, height=height)
    )


def _header_text(text: str, *, size: int = 28, color: str = _TEXT_BRIGHT) -> Text:
    return (
        Text(text)
        .font_size(size)
        .font_weight(700)
        .color(color)
        .text_align(TextAlign.CENTER)
        .size(width="100%")
    )


def _subtitle_text(text: str) -> Text:
    return (
        Text(text)
        .font_size(14)
        .color(_TEXT_DIM)
        .text_align(TextAlign.CENTER)
        .size(width="100%")
    )


def _divider() -> Row:
    return Row().size(width="100%", height=1).background_color(_DIVIDER)


def _watermark() -> Text:
    return (
        Text("LeGM")
        .font_size(13)
        .font_weight(700)
        .color("#ffffff15")
        .text_align(TextAlign.RIGHT)
        .size(width="100%")
    )


def _stat_cell(
    text: str,
    *,
    width: int | str = 0,
    color: str = _TEXT,
    size: int = 15,
    weight: int = 400,
    align: TextAlign = TextAlign.CENTER,
) -> Text:
    cell = Text(text).font_size(size).font_weight(weight).color(color).text_align(align)
    if width:
        cell.size(width=width)
    else:
        cell.flex_grow(1)
    return cell


# ---------------------------------------------------------------------------
# Comparison chart — StatMuse-inspired with headshots + team gradients
# ---------------------------------------------------------------------------


def generate_comparison_chart(
    stats_a: PlayerSeasonStats,
    stats_b: PlayerSeasonStats,
    adv_a: PlayerAdvancedStats | None = None,
    adv_b: PlayerAdvancedStats | None = None,
) -> bytes:
    """Create a table-style comparison chart with headshots. Returns PNG bytes."""
    rows: list[tuple[str, float, float, bool, bool]] = [
        ("PPG", stats_a.ppg, stats_b.ppg, False, True),
        ("RPG", stats_a.rpg, stats_b.rpg, False, True),
        ("APG", stats_a.apg, stats_b.apg, False, True),
        ("FG%", stats_a.fg_pct, stats_b.fg_pct, True, True),
    ]
    if adv_a and adv_b:
        rows.extend(
            [
                ("TS%", adv_a.ts_pct, adv_b.ts_pct, True, True),
                ("USG%", adv_a.usg_pct, adv_b.usg_pct, True, True),
                ("Net Rtg", adv_a.net_rating, adv_b.net_rating, False, True),
            ]
        )

    name_a = stats_a.player_name.split()[-1].upper()
    name_b = stats_b.player_name.split()[-1].upper()

    season_text = stats_a.season
    if stats_a.season != stats_b.season:
        season_text = f"{stats_a.season} / {stats_b.season}"

    return _build_comparison_table(
        title=f"{stats_a.player_name}  vs  {stats_b.player_name}",
        subtitle=f"{stats_a.team}  |  {season_text}",
        name_a=name_a,
        name_b=name_b,
        full_name_a=stats_a.player_name.split()[-1],
        full_name_b=stats_b.player_name.split()[-1],
        rows=[(label, va, vb, is_pct, hib) for label, va, vb, is_pct, hib in rows],
        player_id_a=stats_a.player_id,
        player_id_b=stats_b.player_id,
        team_a=stats_a.team,
        team_b=stats_b.team,
    )


def _build_comparison_table(
    *,
    title: str,
    subtitle: str | None,
    name_a: str,
    name_b: str,
    full_name_a: str,
    full_name_b: str,
    rows: list[tuple[str, float, float, bool, bool]],
    player_id_a: int | None = None,
    player_id_b: int | None = None,
    team_a: str = "",
    team_b: str = "",
) -> bytes:
    """Build and render a comparison table with headshots and team gradient."""
    num_rows = len(rows)
    canvas_h = 170 + (num_rows * 40)

    bg = _dual_team_gradient(team_a, team_b) if team_a and team_b else None
    canvas = _make_canvas(canvas_h, background=bg)

    # -- Header: [badge_a] Title [badge_b] on one compact line --
    headshot_a = (
        _headshot_image(player_id_a, _HEADSHOT_BADGE) if player_id_a else None
    )
    headshot_b = (
        _headshot_image(player_id_b, _HEADSHOT_BADGE) if player_id_b else None
    )

    title_col = (
        Column(
            _header_text(title, size=24),
            _subtitle_text(subtitle) if subtitle else Text("").size(height=0),
        )
        .flex_grow(1)
        .gap(2)
        .align_items("center")
        .justify_content("center")
    )

    header_parts: list[Column | Row | Text | Image] = []
    if headshot_a:
        header_parts.append(headshot_a)
    header_parts.append(title_col)
    if headshot_b:
        header_parts.append(headshot_b)

    header_row = (
        Row(*header_parts)
        .size(width="100%")
        .padding(0, 24)
        .align_items("center")
        .justify_content("center")
        .gap(12)
    )

    children: list[Column | Row | Text | Image] = [header_row]

    # Column headers
    col_header_row = (
        Row(
            _stat_cell("STAT", color=_TEXT_DIM, size=12, weight=700),
            _stat_cell(name_a, color=_ACCENT_A, size=13, weight=700),
            _stat_cell(name_b, color=_ACCENT_B, size=13, weight=700),
            _stat_cell("EDGE", color=_TEXT_DIM, size=12, weight=700, width=100),
        )
        .size(width="100%")
        .padding(6, 24)
    )
    children.append(_divider())
    children.append(col_header_row)
    children.append(_divider())

    # Stat rows
    wins_a = 0
    wins_b = 0

    for i, (label, va, vb, is_pct, higher_better) in enumerate(rows):
        a_wins = (va > vb) if higher_better else (va < vb)
        b_wins = (vb > va) if higher_better else (vb < va)
        if a_wins:
            wins_a += 1
        elif b_wins:
            wins_b += 1

        color_a = _TEXT_BRIGHT if a_wins else _TEXT
        color_b = _TEXT_BRIGHT if b_wins else _TEXT
        weight_a = 700 if a_wins else 400
        weight_b = 700 if b_wins else 400

        fmt_a = _fmt(va, is_pct=is_pct, is_plus=(label == "Net Rtg"))
        fmt_b = _fmt(vb, is_pct=is_pct, is_plus=(label == "Net Rtg"))

        if a_wins:
            edge_text, edge_color = "<", _ACCENT_A
        elif b_wins:
            edge_text, edge_color = ">", _ACCENT_B
        else:
            edge_text, edge_color = "-", _TEXT_DIM

        row_bg = _ROW_EVEN if i % 2 == 0 else _ROW_ODD
        stat_row = (
            Row(
                _stat_cell(label, color=_TEXT_DIM, size=14, weight=700),
                _stat_cell(fmt_a, color=color_a, size=17, weight=weight_a),
                _stat_cell(fmt_b, color=color_b, size=17, weight=weight_b),
                _stat_cell(edge_text, color=edge_color, size=15, width=100),
            )
            .size(width="100%")
            .padding(8, 24)
            .background_color(row_bg)
            .border_radius(4)
        )
        children.append(stat_row)

    # Tally
    children.append(_divider())
    tally = (
        Row(
            _stat_cell(
                f"{full_name_a} leads {wins_a}",
                color=_ACCENT_A,
                size=14,
                weight=700,
            ),
            _stat_cell(
                f"{full_name_b} leads {wins_b}",
                color=_ACCENT_B,
                size=14,
                weight=700,
            ),
        )
        .size(width="100%")
        .padding(6, 24)
    )
    children.append(tally)
    children.append(_watermark())

    card = (
        Column(*children)
        .size(width="100%", height="100%")
        .padding(24, 32)
        .gap(4)
        .justify_content("start")
    )

    return _render_to_bytes(canvas, card)


# ---------------------------------------------------------------------------
# Stat card — single player, StatMuse-inspired layout
# ---------------------------------------------------------------------------


def generate_stat_card(
    stats: PlayerSeasonStats,
    advanced: PlayerAdvancedStats | None = None,
) -> bytes:
    """Create a stat card with headshot on the left and stats on the right.

    Returns PNG bytes.
    """
    stat_rows: list[tuple[str, str, str]] = [
        ("PPG", f"{stats.ppg}", _color_for("ppg", stats.ppg)),
        ("RPG", f"{stats.rpg}", _color_for("rpg", stats.rpg)),
        ("APG", f"{stats.apg}", _color_for("apg", stats.apg)),
        ("FG%", f"{stats.fg_pct:.1%}", _color_for("fg_pct", stats.fg_pct)),
        ("3P%", f"{stats.fg3_pct:.1%}", _color_for("fg3_pct", stats.fg3_pct)),
        ("FT%", f"{stats.ft_pct:.1%}", _color_for("ft_pct", stats.ft_pct)),
    ]

    if advanced:
        stat_rows.extend(
            [
                (
                    "TS%",
                    f"{advanced.ts_pct:.1%}",
                    _color_for("ts_pct", advanced.ts_pct),
                ),
                (
                    "USG%",
                    f"{advanced.usg_pct:.1%}",
                    _color_for("usg_pct", advanced.usg_pct),
                ),
                (
                    "Net Rtg",
                    f"{advanced.net_rating:+.1f}",
                    _color_for("net_rating", advanced.net_rating),
                ),
                ("PIE", f"{advanced.pie:.3f}", _color_for("pie", advanced.pie)),
                ("ORtg", f"{advanced.off_rating:.1f}", _TEXT_BRIGHT),
                ("DRtg", f"{advanced.def_rating:.1f}", _TEXT_BRIGHT),
            ]
        )

    num_stat_rows = len(stat_rows)
    canvas_h = 140 + (num_stat_rows * 30)

    bg = _team_gradient(stats.team)
    canvas = _make_canvas(canvas_h, background=bg)

    children: list[Column | Row | Text | Image] = []

    # -- Header: [headshot badge] NAME  |  hero PPG --
    headshot = _headshot_image(stats.player_id, size=_HEADSHOT_CARD)

    name_block = (
        Column(
            Text(stats.player_name.upper())
            .font_size(22)
            .font_weight(700)
            .color(_TEXT_BRIGHT),
            Text(
                f"{stats.team}  |  {stats.season}  |  "
                f"{stats.games_played} GP  |  {stats.mpg} MPG"
            )
            .font_size(12)
            .color(_TEXT_DIM),
        )
        .gap(2)
        .justify_content("center")
    )

    hero_block = (
        Row(
            Text(f"{stats.ppg}")
            .font_size(36)
            .font_weight(700)
            .color(_GOLD)
            .text_shadows(
                Shadow(offset=(0, 0), blur_radius=16, color="#ffb30040"),
            ),
            Text("PPG").font_size(12).color(_TEXT_DIM).font_weight(700),
        )
        .gap(6)
        .align_items("end")
    )

    header_parts: list[Column | Row | Text | Image] = []
    if headshot:
        header_parts.append(headshot)
    header_parts.append(name_block)
    # Push hero stat to the right
    spacer = Row().flex_grow(1)
    header_parts.append(spacer)
    header_parts.append(hero_block)

    header_row = (
        Row(*header_parts)
        .size(width="100%")
        .align_items("center")
        .gap(12)
    )
    children.append(header_row)
    children.append(_divider())

    # -- Stat rows: two-column grid for density --
    for i, (label, value, color) in enumerate(stat_rows):
        row_bg = _ROW_EVEN if i % 2 == 0 else _ROW_ODD
        row = (
            Row(
                Text(label)
                .font_size(13)
                .font_weight(700)
                .color(_TEXT_DIM)
                .flex_grow(1),
                Text(value).font_size(15).font_weight(700).color(color),
            )
            .size(width="100%")
            .padding(4, 16)
            .background_color(row_bg)
            .border_radius(4)
        )
        children.append(row)

    children.append(_watermark())

    card = (
        Column(*children)
        .size(width="100%", height="100%")
        .padding(20, 28)
        .gap(3)
        .justify_content("start")
    )

    return _render_to_bytes(canvas, card)


# ---------------------------------------------------------------------------
# Flexible chart — agent-driven data
# ---------------------------------------------------------------------------


def generate_flexible_chart(chart_data: ChartData) -> bytes:
    """Create a chart from agent-provided ChartData. Returns PNG bytes.

    Comparison mode when label_b is set. Single-entity mode otherwise.
    """
    if chart_data.label_b is not None:
        name_a_short = (
            chart_data.label_a.split()[-1].upper()
            if " " in chart_data.label_a
            else chart_data.label_a.upper()
        )
        name_b_short = (
            chart_data.label_b.split()[-1].upper()
            if " " in chart_data.label_b
            else chart_data.label_b.upper()
        )

        rows = [
            (
                r.label,
                r.value_a,
                r.value_b if r.value_b is not None else 0.0,
                r.fmt == "percent",
                r.higher_is_better,
            )
            for r in chart_data.rows
        ]

        return _build_comparison_table(
            title=chart_data.title,
            subtitle=chart_data.subtitle,
            name_a=name_a_short,
            name_b=name_b_short,
            full_name_a=chart_data.label_a.split()[-1],
            full_name_b=(chart_data.label_b or "").split()[-1],
            rows=rows,
        )

    return _render_single_chart(chart_data)


def _render_single_chart(chart_data: ChartData) -> bytes:
    """Render single-entity chart with dynamic height and tighter spacing."""
    num_rows = len(chart_data.rows)
    canvas_h = 150 + (num_rows * 40)

    canvas = _make_canvas(canvas_h)

    children: list[Column | Row | Text | Image] = [
        _header_text(chart_data.title),
    ]
    if chart_data.subtitle:
        children.append(_subtitle_text(chart_data.subtitle))

    # Entity label
    children.append(
        Text(chart_data.label_a.upper())
        .font_size(16)
        .font_weight(700)
        .color(_ACCENT_A)
        .text_align(TextAlign.CENTER)
        .size(width="100%")
    )
    children.append(_divider())

    # Stat rows
    for i, row in enumerate(chart_data.rows):
        key = _LABEL_TO_KEY.get(row.label.upper().strip())
        color = _color_for(key, row.value_a) if key else _TEXT_BRIGHT

        row_bg = _ROW_EVEN if i % 2 == 0 else _ROW_ODD
        stat_row = (
            Row(
                Text(row.label)
                .font_size(14)
                .font_weight(700)
                .color(_TEXT_DIM)
                .flex_grow(1),
                Text(_fmt_from_hint(row.value_a, row.fmt))
                .font_size(17)
                .font_weight(700)
                .color(color),
            )
            .size(width="100%")
            .padding(8, 40)
            .background_color(row_bg)
            .border_radius(4)
        )
        children.append(stat_row)

    children.append(_watermark())

    card = (
        Column(*children)
        .size(width="100%", height="100%")
        .padding(24, 32)
        .gap(4)
        .justify_content("start")
    )

    return _render_to_bytes(canvas, card)
