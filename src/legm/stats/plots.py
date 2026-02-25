"""Chart generation for LeGM take analysis — PicTex-powered stat cards."""

import io

from pictex import (
    Canvas,
    Column,
    LinearGradient,
    Row,
    Shadow,
    Text,
    TextAlign,
)

from legm.stats.models import ChartData, PlayerAdvancedStats, PlayerSeasonStats

# -- Design tokens --
_BG = LinearGradient(
    colors=["#0f1923", "#152232", "#0f1923"],
    start_point=(0.0, 0.0),
    end_point=(1.0, 1.0),
)
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
    "ppg": 23.0, "rpg": 6.0, "apg": 4.5,
    "fg_pct": 0.46, "fg3_pct": 0.36, "ft_pct": 0.78,
    "ts_pct": 0.575, "usg_pct": 0.20, "net_rating": 0.0, "pie": 0.10,
}

_LABEL_TO_KEY: dict[str, str] = {
    "PPG": "ppg", "RPG": "rpg", "APG": "apg",
    "FG%": "fg_pct", "FG PCT": "fg_pct",
    "3P%": "fg3_pct", "3PT%": "fg3_pct", "FT%": "ft_pct",
    "TS%": "ts_pct", "USG%": "usg_pct",
    "NET RTG": "net_rating", "PIE": "pie",
}

_CANVAS_W = 1200
_CANVAS_H = 675


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


def _make_canvas() -> Canvas:
    """Create a standard LeGM canvas."""
    return (
        Canvas()
        .font_family("Arial")
        .color(_TEXT)
        .background_color(_BG)
        .size(width=_CANVAS_W, height=_CANVAS_H)
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
    cell = (
        Text(text)
        .font_size(size)
        .font_weight(weight)
        .color(color)
        .text_align(align)
    )
    if width:
        cell.size(width=width)
    else:
        cell.flex_grow(1)
    return cell


# ---------------------------------------------------------------------------
# Comparison chart — clean table layout
# ---------------------------------------------------------------------------


def generate_comparison_chart(
    stats_a: PlayerSeasonStats,
    stats_b: PlayerSeasonStats,
    adv_a: PlayerAdvancedStats | None = None,
    adv_b: PlayerAdvancedStats | None = None,
) -> bytes:
    """Create a table-style comparison chart. Returns PNG bytes."""
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
        rows=[
            (label, va, vb, is_pct, hib)
            for label, va, vb, is_pct, hib in rows
        ],
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
) -> bytes:
    """Build and render a comparison table."""
    canvas = _make_canvas()

    # Header
    children: list[Column | Row | Text] = [
        _header_text(title),
    ]
    if subtitle:
        children.append(_subtitle_text(subtitle))

    # Column headers
    header_row = (
        Row(
            _stat_cell("STAT", color=_TEXT_DIM, size=12, weight=700),
            _stat_cell(name_a, color=_ACCENT_A, size=13, weight=700),
            _stat_cell(name_b, color=_ACCENT_B, size=13, weight=700),
            _stat_cell("EDGE", color=_TEXT_DIM, size=12, weight=700, width=100),
        )
        .size(width="100%")
        .padding(8, 24)
    )
    children.append(_divider())
    children.append(header_row)
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
            .padding(10, 24)
            .background_color(row_bg)
            .border_radius(4)
        )
        children.append(stat_row)

    # Bottom divider + tally
    children.append(_divider())
    tally = (
        Row(
            _stat_cell(
                f"{full_name_a} leads {wins_a}",
                color=_ACCENT_A, size=14, weight=700,
            ),
            _stat_cell(
                f"{full_name_b} leads {wins_b}",
                color=_ACCENT_B, size=14, weight=700,
            ),
        )
        .size(width="100%")
        .padding(8, 24)
    )
    children.append(tally)
    children.append(_watermark())

    card = (
        Column(*children)
        .size(width="100%", height="100%")
        .padding(32, 40)
        .gap(4)
        .justify_content("start")
    )

    return _render_to_bytes(canvas, card)


# ---------------------------------------------------------------------------
# Stat card — single player
# ---------------------------------------------------------------------------


def generate_stat_card(
    stats: PlayerSeasonStats,
    advanced: PlayerAdvancedStats | None = None,
) -> bytes:
    """Create a two-column stat card with color-coded values. Returns PNG bytes."""
    canvas = _make_canvas()

    left_rows = [
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

    # Player name
    children: list[Column | Row | Text] = [
        _header_text(stats.player_name.upper(), size=30),
    ]

    # Hero PPG
    hero = (
        Column(
            Text(f"{stats.ppg}")
                .font_size(56)
                .font_weight(700)
                .color(_GOLD)
                .text_align(TextAlign.CENTER)
                .size(width="100%")
                .text_shadows(
                    Shadow(offset=(0, 0), blur_radius=20, color="#ffb30040"),
                ),
            Text("PPG")
                .font_size(13)
                .color(_TEXT_DIM)
                .text_align(TextAlign.CENTER)
                .size(width="100%"),
        )
        .size(width="100%")
        .gap(0)
        .align_items("center")
    )
    children.append(hero)

    # Meta line
    meta = f"{stats.team}  |  {stats.season}  |  {stats.games_played} GP  |  {stats.mpg} MPG"
    children.append(_subtitle_text(meta))

    # Stat columns
    def _stat_column(
        header: str, header_color: str, rows: list[tuple[str, str, str]]
    ) -> Column:
        col_children: list[Row | Text] = [
            Text(header)
                .font_size(12)
                .font_weight(700)
                .color(header_color)
                .text_align(TextAlign.CENTER)
                .size(width="100%"),
        ]
        for i, (label, value, color) in enumerate(rows):
            row_bg = _ROW_EVEN if i % 2 == 0 else _ROW_ODD
            row = (
                Row(
                    Text(label)
                        .font_size(13)
                        .font_weight(700)
                        .color(_TEXT_DIM)
                        .flex_grow(1),
                    Text(value)
                        .font_size(16)
                        .font_weight(700)
                        .color(color),
                )
                .size(width="100%")
                .padding(6, 16)
                .background_color(row_bg)
                .border_radius(4)
            )
            col_children.append(row)
        return Column(*col_children).flex_grow(1).gap(3)

    columns_row_children = [
        _stat_column("OFFENSE", _ACCENT_A, left_rows),
    ]
    if right_rows:
        columns_row_children.append(
            _stat_column("IMPACT", _ACCENT_B, right_rows),
        )

    columns_row = Row(*columns_row_children).size(width="100%").gap(24)
    children.append(_divider())
    children.append(columns_row)
    children.append(_watermark())

    card = (
        Column(*children)
        .size(width="100%", height="100%")
        .padding(28, 40)
        .gap(6)
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
    """Render single-entity chart — one value column, color-coded."""
    canvas = _make_canvas()

    children: list[Column | Row | Text] = [
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
            .padding(10, 40)
            .background_color(row_bg)
            .border_radius(4)
        )
        children.append(stat_row)

    children.append(_watermark())

    card = (
        Column(*children)
        .size(width="100%", height="100%")
        .padding(32, 40)
        .gap(6)
        .justify_content("start")
    )

    return _render_to_bytes(canvas, card)
