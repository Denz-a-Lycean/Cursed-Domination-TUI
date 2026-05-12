"""ANSI/engine presenter adapter so `CombatSystem` and `Game` run inside the 140x30 frame."""

from __future__ import annotations

import re
import sys
import textwrap
import time
import os
import types
import math

from core.engine import (
    BG_MAIN,
    ESC,
    FG_BORDER,
    FG_DIM,
    FG_LABEL,
    FG_TITLE,
    FG_WHITE,
    RESET,
    WindowManager,
    get_keypress,
    get_keypress_nb,
)
from utils.effects import Colors, color_text

try:
    from utils.validator import ValidationError, validate_menu_index
except ImportError:
    ValidationError = ValueError

    def validate_menu_index(index, options):
        if not isinstance(options, (list, tuple)) or not options:
            raise ValidationError("Menu options cannot be empty.")
        if not isinstance(index, int) or not (0 <= index < len(options)):
            raise ValidationError("Selected menu index is out of range.")
        return index


def _clamp(s: str, max_len: int) -> str:
    s = str(s).replace("\n", " ")
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


ANSI_SEQ = re.compile(r"\033\[[0-9;]*m")


def _visible_len(text: str) -> int:
    return len(ANSI_SEQ.sub("", text))


def _pad_ansi_line(line: str, width: int) -> str:
    n = _visible_len(line)
    if n >= width:
        return line
    return line + (" " * (width - n))


def _center_ansi_line(line: str, width: int) -> str:
    n = _visible_len(line)
    if n >= width:
        return line
    left = (width - n) // 2
    right = width - n - left
    return (" " * left) + line + (" " * right)


def _strip_ansi(text: str) -> str:
    return ANSI_SEQ.sub("", str(text))


def _render_at(buf: str, oy: int, px: int, row: int, col: int, text: str) -> str:
    return buf + f"{ESC}{oy + row};{px + col}H{text}"


def _render_block(buf: str, oy: int, px: int, row: int, col: int, lines: list[str]) -> str:
    for idx, line in enumerate(lines):
        buf = _render_at(buf, oy, px, row + idx, col, line)
    return buf


def _segmented_bar(cur: int, maxv: int, width: int = 20, full_color: str = Colors.WHITE) -> str:
    maxv = max(1, int(maxv))
    cur = max(0, min(int(cur), maxv))
    ratio = cur / maxv
    filled = max(0, min(width, int(round(ratio * width))))

    if ratio <= 0.2:
        color = Colors.BRIGHT_RED
    elif ratio < 0.5:
        color = Colors.BRIGHT_YELLOW
    else:
        color = full_color

    return f"{color}{'▰' * filled}{FG_DIM}{'▱' * (width - filled)}{RESET}"


def _box_lines(title: str, width: int, body_lines: list[str], title_color: str = FG_LABEL) -> list[str]:
    width = max(18, int(width))
    title = _clamp(title, max(1, width - 10))
    label = f"[ {title} ]"
    inner = width - 2
    prefix = "── "
    visible_prefix = len(prefix) + len(label) + 1
    fill = max(0, inner - visible_prefix)
    top = (
        f"{FG_BORDER}┌{RESET}{FG_BORDER}{prefix}{RESET}"
        f"{title_color}{label}{RESET} {FG_BORDER}{'─' * fill}┐{RESET}"
    )
    body_w = width - 4
    body = [
        f"{FG_BORDER}│{RESET} {_pad_ansi_line(line, body_w)} {FG_BORDER}│{RESET}"
        for line in body_lines
    ]
    bottom = f"{FG_BORDER}└{'─' * (width - 2)}┘{RESET}"
    return [top, *body, bottom]


def _footer_bar(width: int, text: str) -> str:
    width = max(10, int(width))
    inner = width - 2
    text = _clamp(text or "", inner - 2)
    label = f" {text} "
    fill = max(0, inner - _visible_len(label))
    left = fill // 2
    right = fill - left
    return f"{FG_BORDER}+{'=' * left}{RESET}{FG_WHITE}{label}{RESET}{FG_BORDER}{'=' * right}+{RESET}"


def _wrap_plain_text(text: str, width: int, max_lines: int) -> list[str]:
    clean = _strip_ansi(text).replace("\n", " ").strip()
    wrapped = textwrap.wrap(clean, width=max(1, width)) or [""]
    return wrapped[: max(1, max_lines)]


def _menu_window_start(selected: int, total: int, visible: int) -> int:
    total = max(0, int(total))
    visible = max(1, int(visible))
    if total <= visible:
        return 0
    selected = max(0, min(int(selected), total - 1))
    return max(0, min(selected - (visible // 2), total - visible))


def _enemy_box_title(parsed: dict) -> str:
    enemy_name = parsed.get("enemy_name", "Enemy").replace("(Special Grade)", "").strip().upper()
    if parsed.get("stage", 1) >= 5 or "SPECIAL GRADE" in parsed.get("enemy_name", "").upper():
        return f"SPECIAL GRADE: {enemy_name}"
    return f"CURSE: {enemy_name}"


def _top_border(panel_w: int) -> str:
    return "+" + "-" * max(3, panel_w - 2) + "+"


def _section_separator(panel_w: int, title: str) -> str:
    """|----- TITLE --------| centered label between pipes."""
    inner = panel_w - 2
    t = f" {title.strip()} "
    if len(t) >= inner:
        t = (" " + title.strip())[: inner]
    gaps = inner - len(t)
    left = gaps // 2
    right = gaps - left
    return "|" + ("-" * left) + t + ("-" * right) + "|"


def _parse_combat_status(lines: list[str]) -> dict | None:
    """If `lines` match `CombatSystem._status_lines` shape, return structured HUD data."""
    if not lines or len(lines) < 3:
        return None
    m0 = re.match(r"(?:Game Time:\s*(.+?)\s*\|\s*)?Battle Time:\s*(.+)", lines[0].strip())
    m1 = re.match(
        r"Player:\s*(.+?)\s*\((.+?)\)\s*\|\s*HP\s*(\d+)/(\d+)\s*\|\s*Domain\s*(\d+)%\s*\|\s*Instability\s*(\d+)(.*)",
        lines[1].strip(),
    )
    m2 = re.match(
        r"Enemy:\s*(.+?)\s*\|\s*(?:Type\s*(.+?)\s*\|\s*)?Stage\s*(\d+)\s*\|\s*Enemy HP\s*(\d+)/(\d+)",
        lines[2].strip(),
    )
    if not (m0 and m1 and m2):
        return None
    extra = (m1.group(7) or "")
    defending = "[DEFENDING]" in extra.upper() or "DEFENDING" in extra.upper()
    return {
        "game_time": (m0.group(1).strip() if m0.group(1) else "00:00"),
        "battle_time": m0.group(2).strip(),
        "player_name": m1.group(1).strip(),
        "player_class": m1.group(2).strip(),
        "hp": int(m1.group(3)),
        "hp_max": int(m1.group(4)),
        "domain": int(m1.group(5)),
        "instability": int(m1.group(6)),
        "defending": defending,
        "enemy_name": m2.group(1).strip(),
        "enemy_type": (m2.group(2) or "").strip(),
        "stage": int(m2.group(3)),
        "enemy_hp": int(m2.group(4)),
        "enemy_max": int(m2.group(5)),
    }


def _meter(cur: int, maxv: int, width: int, filled: str, empty: str) -> str:
    if maxv <= 0:
        maxv = 1
    f = int(round((cur / maxv) * width))
    f = max(0, min(width, f))
    return f"{filled * f}{empty * (width - f)}"


def _fmt_hud_lines(data: dict) -> list[str]:
    """Build rich HUD rows (no outer borders)."""
    hp_bar_w = 16
    dom_bar_w = 12
    en_bar_w = 14
    hp_r = data["hp"] / max(1, data["hp_max"])
    dm_r = data["domain"] / 100.0
    en_r = data["enemy_hp"] / max(1, data["enemy_max"])
    defend = ""
    if data.get("defending"):
        defend = f" {Colors.BRIGHT_YELLOW}[DEFENDING]{RESET}"
    # Show only the battle clock to avoid duplicative HUD information.
    line_times = (
        f"{Colors.CYAN}Clock{RESET}   "
        f"{FG_LABEL}Fight{RESET} {Colors.WHITE}{data['battle_time']:<8}{RESET}"
    )
    hp_chunk = (
        f"{Colors.BRIGHT_RED if hp_r <= 0.25 else Colors.GREEN}"
        f"{_meter(data['hp'], data['hp_max'], hp_bar_w, '█', '░')}"
        f"{RESET} {Colors.WHITE}{data['hp']}/{data['hp_max']}{RESET}"
    )
    dm_chunk = (
        f"{Colors.MAGENTA}{_meter(data['domain'], 100, dom_bar_w, '█', '░')}{RESET} "
        f"{Colors.WHITE}{data['domain']}%{RESET}"
    )
    line_vitals = (
        f"{FG_LABEL}{_clamp(data['player_name'], 14):<14}{RESET} "
        f"{FG_DIM}{_clamp(data.get('player_class', ''), 10):<10}{RESET} "
        f"{Colors.CYAN}HP{RESET} [{hp_chunk}]   "
        f"{Colors.CYAN}CURSE{RESET} [{dm_chunk}]   "
        f"{FG_DIM}Iy{RESET} {data['instability']}/5"
        f"{defend}"
    )
    en_chunk = (
        f"{Colors.RED}{_meter(data['enemy_hp'], data['enemy_max'], en_bar_w, '█', '░')}{RESET} "
        f"{Colors.WHITE}{data['enemy_hp']}/{data['enemy_max']}{RESET}"
    )
    line_eng = (
        f"{Colors.CYAN}Stage {Colors.WHITE}{data['stage']}{RESET}           "
        f"{FG_TITLE}{_clamp(data.get('enemy_name', 'TARGET'), 18)}{RESET}  [{en_chunk}]"
    )
    return [line_times, line_vitals, line_eng]


def _battlefield_block(frame: int, panel_w: int, player_class: str = "Seeker") -> list[str]:
    """
    Small animated battlefield block. Uses subtle frame-to-frame shifts while the menu waits.
    """
    # Keep within inner content width.
    inner = max(20, panel_w - 4)
    wob = (frame % 4) - 1  # -1..2
    wob2 = 1 - (frame % 3)  # 1..-1

    # Enemy (left/top)
    e_col = Colors.RED
    p_col = Colors.CYAN if player_class == "Seeker" else (Colors.BRIGHT_YELLOW if player_class == "Bouncer" else Colors.MAGENTA)

    enemy = [
        f"{e_col}  .╖ ╓.  {RESET}",
        f"{e_col} ║ ⊚ ⊚ ║ {RESET}",
        f"{e_col}  '—╩—'  {RESET}",
    ]
    # Player variations by class (right/bottom)
    if player_class == "Dancer":
        player = [
            f"{p_col}   _O/   {RESET}",
            f"{p_col}     \\   {RESET}",
            f"{p_col}     /\\_ {RESET}",
        ]
    elif player_class == "Bouncer":
        player = [
            f"{p_col}    [ ]    {RESET}",
            f"{p_col}   / | \\   {RESET}",
            f"{p_col}    / \\    {RESET}",
        ]
    else:
        player = [
            f"{p_col}  .▞▀▀▚. {RESET}",
            f"{p_col} ▐      ▌{RESET}",
            f"{p_col}  ▙▄▄▄▄▟ {RESET}",
        ]

    # Compose in two columns with some animated spacing.
    gap = " " * (max(4, (inner // 2) - 10) + max(0, wob))
    gap2 = " " * (max(4, (inner // 2) - 10) + max(0, wob2))
    rows = []
    rows.append((enemy[0] + gap + player[0]).center(inner))
    rows.append((enemy[1] + gap2 + player[1]).center(inner))
    rows.append((enemy[2] + gap + player[2]).center(inner))
    return rows


def _pokemon_box(inner_w: int, title: str | None = None) -> list[str]:
    """
    Build a Pokémon-style text box (no ANSI), sized to `inner_w`.
    Returns [top, mid_template, bottom] where mid_template expects content fill.
    """
    inner_w = max(24, int(inner_w))
    top = "┌" + ("─" * (inner_w - 2)) + "┐"
    bot = "└" + ("─" * (inner_w - 2)) + "┘"
    if title:
        t = f" {title.strip()} "
        if len(t) < inner_w - 2:
            left = 1
            right = (inner_w - 2) - len(t) - left
            top = "┌" + ("─" * left) + t + ("─" * right) + "┐"
    return [top, "│" + (" " * (inner_w - 2)) + "│", bot]


def _pokemon_status_box(name: str, hp: int, hp_max: int, width: int, align_right: bool) -> list[str]:
    width = max(26, int(width))
    nm = _clamp(name, width - 10)
    hp_ratio = hp / max(1, hp_max)
    bar_w = 10
    bar = _meter(hp, hp_max, bar_w, "█", "░")
    hp_color = Colors.BRIGHT_RED if hp_ratio <= 0.25 else (Colors.BRIGHT_YELLOW if hp_ratio <= 0.5 else Colors.GREEN)
    line1 = f"{Colors.WHITE}{nm}{RESET}"
    line2 = f"{FG_DIM}HP{RESET} {hp_color}{bar}{RESET} {Colors.WHITE}{hp:>3}/{hp_max:<3}{RESET}"
    pad = width - 2
    if align_right:
        line1 = line1.rjust(pad)
        line2 = line2.rjust(pad + 6)  # allow for ANSI
    else:
        line1 = line1.ljust(pad)
        line2 = line2.ljust(pad + 6)
    top, mid, bot = _pokemon_box(width)
    return [
        top,
        "│" + _pad_ansi_line(line1, width - 2) + "│",
        "│" + _pad_ansi_line(line2, width - 2) + "│",
        bot,
    ]


def _pokemon_command_box(options: list[str], width: int) -> list[str]:
    """
    Pokémon-like 2x2 command box. Options are numbered 1-4.
    """
    width = max(34, int(width))
    left_w = (width - 3) // 2
    right_w = (width - 3) - left_w
    opts = [(options[i] if i < len(options) else "") for i in range(4)]
    def fmt(i: int, w: int) -> str:
        label = _clamp(opts[i], w - 6)
        return f"{Colors.BRIGHT_YELLOW}{i+1}.{RESET} {Colors.WHITE}{label}{RESET}"
    r0l = fmt(0, left_w).ljust(left_w + 8)
    r0r = fmt(1, right_w).ljust(right_w + 8)
    r1l = fmt(2, left_w).ljust(left_w + 8)
    r1r = fmt(3, right_w).ljust(right_w + 8)
    top = "┌" + ("─" * (width - 2)) + "┐"
    mid = "├" + ("─" * left_w) + "┬" + ("─" * right_w) + "┤"
    bot = "└" + ("─" * left_w) + "┴" + ("─" * right_w) + "┘"
    return [
        top,
        "│" + _pad_ansi_line(r0l, left_w) + "│" + _pad_ansi_line(r0r, right_w) + "│",
        mid,
        "│" + _pad_ansi_line(r1l, left_w) + "│" + _pad_ansi_line(r1r, right_w) + "│",
        bot,
    ]


def _pokemon_command_box_with_cursor(options: list[str], width: int, selected: int) -> list[str]:
    """
    Same as `_pokemon_command_box` but renders a cursor on `selected` index (0-3).
    """
    width = max(34, int(width))
    selected = int(selected) if selected is not None else 0
    selected = max(0, min(3, selected))

    left_w = (width - 3) // 2
    right_w = (width - 3) - left_w
    opts = [(options[i] if i < len(options) else "") for i in range(4)]

    def fmt(i: int, w: int) -> str:
        label = _clamp(opts[i], w - 8)
        cursor = f"{Colors.BRIGHT_YELLOW}▶{RESET} " if i == selected else "  "
        num = f"{Colors.BRIGHT_YELLOW}{i+1}.{RESET}"
        body = f"{cursor}{num} {Colors.WHITE}{label}{RESET}"
        return body

    r0l = fmt(0, left_w).ljust(left_w + 10)
    r0r = fmt(1, right_w).ljust(right_w + 10)
    r1l = fmt(2, left_w).ljust(left_w + 10)
    r1r = fmt(3, right_w).ljust(right_w + 10)

    top = "┌" + ("─" * (width - 2)) + "┐"
    mid = "├" + ("─" * left_w) + "┬" + ("─" * right_w) + "┤"
    bot = "└" + ("─" * left_w) + "┴" + ("─" * right_w) + "┘"
    return [
        top,
        "│" + _pad_ansi_line(r0l, left_w) + "│" + _pad_ansi_line(r0r, right_w) + "│",
        mid,
        "│" + _pad_ansi_line(r1l, left_w) + "│" + _pad_ansi_line(r1r, right_w) + "│",
        bot,
    ]


def _pokemon_activity_box(lines: list[str], width: int, title: str = "ACTIVITY") -> list[str]:
    """Compact side panel used when controls should be hidden during action resolution."""
    width = max(34, int(width))
    box = _pokemon_box(width, title=title)
    body = []
    content = list(lines or [])[:3]
    while len(content) < 3:
        content.append("")
    for line in content:
        rendered = f"{FG_DIM}»{RESET} {Colors.WHITE}{_clamp(line, width - 6)}{RESET}" if line else ""
        body.append("│" + _pad_ansi_line(rendered, width - 2) + "│")
    return [box[0], *body, box[2]]


def _enemy_art_key(enemy_name: str, enemy_type: str = "", stage: int = 1) -> str:
    token = (enemy_type or "").strip().lower()
    if token in {"weak", "fast", "aggressive", "elite", "boss"}:
        return token

    name = (enemy_name or "").strip().lower()
    if "orlegou" in name or "special grade" in name or stage >= 5:
        return "boss"
    if "elite" in name:
        return "elite"
    if "aggressive" in name:
        return "aggressive"
    if "fast" in name:
        return "fast"
    return "weak"


def _enemy_art(enemy_name: str, enemy_type: str = "", stage: int = 1) -> list[str]:
    art_key = _enemy_art_key(enemy_name, enemy_type, stage)
    art_map = {
        "weak": [
            "     / \\ / \\",
            "    (  0 0  )",
            "     \\  W  /",
            "      /   \\",
            "     (_____)",
        ],
        "fast": [
            '   _,="( _  )"=,_',
            "_,'    \\_>\\_/    ',_",
            ".7,     {  }     ,\\.",
            " '/:,  .m  m.  ,:\\'",
            '   \')",(/  \\),"(\'',
            "      '{'!!'}'",
        ],
        "aggressive": [
            "        __   __",
            "     .-'  \".\"  '-.",
            "   .'   ___,___   '.",
            "  ;__.-; | | | ;-.__;",
            "  | \\  | | | | |  / |",
            "   \\ \\/`\"`\"`\"`\"`\\/ /",
            "    \\_.-,-,-,-,-._/",
            "     \\`-:_|_|_:-'/",
            "      '.       .'",
        ],
        "elite": [
            "              _          _",
            "             _/|    _   |\\_",
            "           _/_ |   _|\\\\ | _\\",
            "         _/_/| /  /   \\|\\ |\\_\\_",
            "       _/_/  |/  /  _  \\/\\|  \\_\\_ ",
            "     _/_/    ||  | | \\o/ ||    \\_\\_",
            "    /_/  | | |\\  | \\_ V  /| | |  \\_\\",
            "   //    ||| | \\_/   \\__/ | |||    \\\\",
            "///    \\\\\\\\/   /        \\   \\////    \\\\\\",
        ],
        "boss": [
            "         __",
            "        /\\/\\  |",
            "       _\\__/  |",
            "      /  \\/`\\<`)",
            "      \\ (  |\\_/",
            "      /)))-(  |",
            "     / /^ ^ \\ |",
            "    /  )^/\\^( |",
            "    )_//`__>> |",
        ],
    }
    return art_map.get(art_key, art_map["weak"])


def _normalize_art_rows(lines: list[str], rows: int, align: str) -> list[str]:
    lines = list(lines or [])[: max(0, rows)]
    padding = max(0, rows - len(lines))
    if align == "bottom":
        return ([""] * padding) + lines
    return lines + ([""] * padding)


def _battle_art(player_class: str, enemy_name: str = "", enemy_type: str = "", stage: int = 1) -> tuple[list[str], list[str], str]:
    """Return denser combat silhouettes for the diagonal battlefield layout.

    Note: player/enemy rows are standardized to equal visible width to prevent
    per-frame spacing jitter.
    """
    enemy = _enemy_art(enemy_name, enemy_type, stage)

    if player_class == "Dancer":
        player = [
            r"      ▄█▀▀▀█▄         ",
            r"    ▄█▀  _  ▀█▄       ",
            r"    █ ▐█▌ ▐█▌ █       ",
            r"    █    ^    █       ",
            r"     ▀█▄▄█▄▄█▀        ",
            r"        /|\           ",
            r"       / | \          ",
        ]
        color = Colors.MAGENTA
    elif player_class == "Bouncer":
        player = [
            r"      ▄█▀▀▀█▄        ",
            r"    ▄█  ( )  █▄      ",
            r"    █   |_|   █      ",
            r"    █  /___\  █      ",
            r"     ▀█▄▄▄▄▄█▀       ",
            r"        / \          ",
            r"      _/___\_        ",
        ]
        color = Colors.BRIGHT_YELLOW
    else:
        player = [
            r"      ▄█▀▀▀█▄         ",
            r"    ▄█  (O)  █▄       ",
            r"    █   /|\   █       ",
            r"    █  _/ \_  █       ",
            r"     ▀█▄▄█▄▄█▀        ",
            r"        / \           ",
            r"       /___\          ",
        ]
        color = Colors.CYAN

    # Normalize widths (visible) for stable diagonal spacing.
    all_rows = list(player) + list(enemy)
    target_w = max((_visible_len(r) for r in all_rows), default=0)

    def _pad_rows(rows: list[str]) -> list[str]:
        out: list[str] = []
        for r in rows:
            r = str(r)
            if _visible_len(r) < target_w:
                r = r + (" " * (target_w - _visible_len(r)))
            elif _visible_len(r) > target_w:
                # Keep left part; truncate for consistent layout.
                r = r[:target_w]
            out.append(r)
        return out

    return _pad_rows(player), _pad_rows(enemy), color



def _pokemon_battlefield(frame: int, width: int, player_class: str, enemy_name: str = "", enemy_type: str = "", stage: int = 1) -> list[str]:
    """
    Battlefield strip using a player-left / enemy-right diagonal perspective.
    """
    width = max(80, int(width))
    player, enemy, player_color = _battle_art(player_class, enemy_name, enemy_type, stage)
    # Keep art placement stable to avoid the “floating/jitter” feel.
    # Any animation should not change lateral spacing.
    drift = 0
    player_pad = 2
    enemy_pad = 1
    lines = []
    field_rows = 9
    has_void_row = max(len(player), len(enemy)) <= (field_rows - 1)
    art_rows = field_rows - 1 if has_void_row else field_rows
    player_rows = _normalize_art_rows(player, art_rows, "bottom")
    enemy_rows = _normalize_art_rows(enemy, art_rows, "top")

    for idx in range(art_rows):
        left = (" " * player_pad) + f"{player_color}{player_rows[idx]}{RESET}" if player_rows[idx] else ""
        right = (" " * enemy_pad) + f"{Colors.RED}{enemy_rows[idx]}{RESET}" if enemy_rows[idx] else ""
        spacing = max(10, width - _visible_len(left) - _visible_len(right))
        lines.append(_pad_ansi_line(left + (" " * spacing) + right, width))

    if has_void_row:
        void_left = f"{FG_DIM}{'_' * 18}{RESET}"
        void_mid = f"{FG_BORDER}~ ~ ~   THE VOID   ~ ~ ~{RESET}"
        void_right = f"{FG_DIM}{'_' * 18}{RESET}"
        spacing = max(4, width - _visible_len(void_left) - _visible_len(void_mid) - _visible_len(void_right))
        left_gap = spacing // 2
        right_gap = spacing - left_gap
        lines.append(
            _pad_ansi_line(
                void_left + (" " * left_gap) + void_mid + (" " * right_gap) + void_right,
                width,
            )
        )
    return lines


def _render_pokemon_combat_panel(
    *,
    buf: str,
    oy: int,
    px: int,
    panel_w: int,
    frame: int,
    parsed: dict,
    message: str,
    cmd_options: list[str] | None = None,
    selected: int = 0,
    menu_start: int = 0,
    side_lines: list[str] | None = None,
    side_title: str = "ACTIVITY",
) -> tuple[str, int]:
    """
    Render combat content directly into the main frame area using a Pokémon-style
    diagonal battlefield and dual footer consoles.
    Returns (buf, row) where row is the next y-offset (relative to oy).
    """
    inner = panel_w
    stage_num = int(parsed.get("stage", 0))
    meta_line = (
        f"{FG_LABEL}STAGE{RESET}: {Colors.WHITE}{stage_num:02d}{RESET} | "
        f"{FG_LABEL}BATTLE TIME{RESET}: {Colors.WHITE}{parsed.get('battle_time', '00:00')}{RESET}"
    )
    # Render meta line aligned with inner content (px already includes left padding)
    buf = _render_at(buf, oy, px, 1, 0, _pad_ansi_line(meta_line, inner))

    enemy_box_w = min(52, inner - 8)
    player_box_w = min(52, inner - 8)
    enemy_box_x = inner - enemy_box_w - 2
    player_box_x = 2

    enemy_lines = [
        f"{FG_DIM}HP{RESET} {_segmented_bar(parsed['enemy_hp'], parsed['enemy_max'], 20, Colors.WHITE)} {Colors.WHITE}{parsed['enemy_hp']}/{parsed['enemy_max']}{RESET}",
    ]
    enemy_box = _box_lines(_enemy_box_title(parsed), enemy_box_w, enemy_lines, title_color=FG_TITLE)
    buf = _render_block(buf, oy, px, 3, enemy_box_x, enemy_box)

    player_lines = [
        f"{FG_DIM}HP{RESET}     {_segmented_bar(parsed['hp'], parsed['hp_max'], 20, Colors.WHITE)} {Colors.WHITE}{parsed['hp']}/{parsed['hp_max']}{RESET}",
        f"{FG_DIM}DOMAIN{RESET} {_segmented_bar(parsed['domain'], 100, 20, Colors.CYAN)} {Colors.WHITE}{parsed['domain']}/100{RESET}",
        f"{FG_DIM}INSTABILITY{RESET} {Colors.WHITE}{parsed['instability']}/5{RESET}"
        + (f" {Colors.BRIGHT_YELLOW}[DEFENDING]{RESET}" if parsed.get("defending") else ""),
    ]
    player_title = f"{parsed.get('player_name', 'PLAYER').upper()} ({parsed.get('player_class', '').upper()})"
    player_box = _box_lines(player_title, player_box_w, player_lines, title_color=FG_LABEL)

    battlefield_lines = _pokemon_battlefield(
        frame,
        inner - 2,
        parsed.get("player_class", "Seeker"),
        parsed.get("enemy_name", "Enemy"),
        parsed.get("enemy_type", ""),
        stage_num,
    )
    buf = _render_block(buf, oy, px, 7, 2, battlefield_lines)
    buf = _render_block(buf, oy, px, 16, player_box_x, player_box)

    # Rebalance the consoles to reduce cramped feel.
    command_box_w = 48
    message_box_w = inner - command_box_w - 4
    command_box_x = 2
    message_box_x = command_box_x + command_box_w + 4

    if cmd_options:
        selection_label = cmd_options[selected] if 0 <= selected < len(cmd_options) else ""
        recent_logs = [line for line in list(side_lines or []) if line.strip()]


        if len(cmd_options) <= 4:
            cell_width = 23

            def _cmd_cell(index: int) -> str:
                label = cmd_options[index] if index < len(cmd_options) else ""
                prefix = f"▶ {index + 1}." if index == selected else f"  {index + 1}."
                return f"{Colors.BRIGHT_YELLOW}{prefix}{RESET} {Colors.WHITE}{_clamp(label, cell_width - 6)}{RESET}"

            command_lines = [
                _pad_ansi_line(_cmd_cell(0), cell_width) + "  " + _pad_ansi_line(_cmd_cell(1), cell_width),
                _pad_ansi_line(_cmd_cell(2), cell_width) + "  " + _pad_ansi_line(_cmd_cell(3), cell_width),
                f"{FG_DIM}READY:{RESET} {Colors.WHITE}{_clamp(selection_label, command_box_w - 12)}{RESET}",
            ]
            recent_logs = recent_logs[-2:]
            log_lines = [f"{FG_DIM}»{RESET} {Colors.WHITE}{_clamp(line, message_box_w - 6)}{RESET}" for line in recent_logs]
            prompt_line = f"{FG_DIM}»{RESET} {Colors.WHITE}{_clamp(message, message_box_w - 6)}{RESET}"
            log_lines.append(prompt_line)
            while len(log_lines) < 3:
                log_lines.insert(0, f"{FG_DIM}»{RESET} {Colors.WHITE}The void waits...{RESET}")
            left_box = _box_lines("COMMANDS", command_box_w, command_lines, title_color=FG_LABEL)
            right_box = _box_lines("MESSAGE LOG", message_box_w, log_lines[:3], title_color=FG_LABEL)
        else:
            visible_slots = 4
            body_width = command_box_w - 4
            start = max(0, min(int(menu_start), max(0, len(cmd_options) - visible_slots)))
            stop = min(len(cmd_options), start + visible_slots)
            command_lines = []
            for index in range(start, stop):
                prefix = f"{Colors.BRIGHT_YELLOW}▶{RESET}" if index == selected else " "
                label = (
                    f"{prefix} {Colors.BRIGHT_YELLOW}{index + 1:>2}.{RESET} "
                    f"{Colors.WHITE}{_clamp(cmd_options[index], body_width - 10)}{RESET}"
                )
                command_lines.append(label)
            while len(command_lines) < visible_slots:
                command_lines.append("")
            command_lines.append(
                f"{FG_DIM}SHOWING {start + 1}-{stop} OF {len(cmd_options)}  LEFT/RIGHT PAGE{RESET}"
            )

            prompt_line = f"{FG_DIM}»{RESET} {Colors.WHITE}{_clamp(message, message_box_w - 6)}{RESET}"
            log_lines = [f"{FG_DIM}»{RESET} {Colors.WHITE}{_clamp(line, message_box_w - 6)}{RESET}" for line in recent_logs[-4:]]
            log_lines.append(prompt_line)
            while len(log_lines) < 5:
                log_lines.insert(0, f"{FG_DIM}»{RESET} {Colors.WHITE}The void watches quietly...{RESET}")

            left_box = _box_lines("COMMANDS", command_box_w, command_lines[:5], title_color=FG_LABEL)
            right_box = _box_lines("MESSAGE LOG", message_box_w, log_lines[:5], title_color=FG_LABEL)
    else:
        activity_lines = [
            f"{FG_DIM}»{RESET} {Colors.WHITE}{_clamp(line, command_box_w - 6)}{RESET}"
            for line in list(side_lines or [])[:3]
        ]
        while len(activity_lines) < 3:
            activity_lines.append("")
        message_lines = [
            f"{FG_DIM}»{RESET} {Colors.WHITE}{_clamp(line, message_box_w - 6)}{RESET}"
            for line in _wrap_plain_text(message, message_box_w - 6, 3)
        ]
        while len(message_lines) < 3:
            message_lines.append("")
        left_box = _box_lines(side_title, command_box_w, activity_lines, title_color=FG_LABEL)
        right_box = _box_lines("MESSAGE LOG", message_box_w, message_lines[:3], title_color=FG_LABEL)

    buf = _render_block(buf, oy, px, 22, command_box_x, left_box)
    buf = _render_block(buf, oy, px, 22, message_box_x, right_box)

    return buf, 27


def _render_help_footer(help_text: str, n_opts: int, allow_escape: bool) -> str:
    hints = (
        f"{FG_DIM}Press {RESET}"
        f"{Colors.BRIGHT_YELLOW}1{RESET}{FG_DIM}–{RESET}{Colors.BRIGHT_YELLOW}{n_opts}{RESET} "
        f"{FG_DIM}to select.{RESET}"
    )
    if allow_escape:
        hints += f"   {FG_DIM}Esc:{RESET} {Colors.WHITE}Back{RESET}"
    rest = (help_text or "").strip()
    if rest:
        hints += f"   {FG_DIM}{_clamp(rest, 70)}{RESET}"
    return hints


def _build_ui_test_menu_lines(
    data: dict,
    options: list[str],
    panel_w: int,
    help_text: str,
    allow_escape: bool,
) -> list[str]:
    """
    Build gameplay HUD/menu lines.
    """
    base = _fmt_hud_lines(data)
    base.append("")
    base.append("Actions:")
    for i, opt in enumerate(options, start=1):
        base.append(f"[{i}] {opt}")
    base.append("")
    base.append(_render_help_footer(help_text, len(options), allow_escape))
    return base


class AnsiGamePresenter:
    """
    Minimal substitute for `TerminalPresenter`: screen, loading, menu, stop,
    and optional combat animation hooks used by `CombatSystem`.
    """

    def __init__(self, window: WindowManager):
        self.window = window
        self.colors = Colors
        self._log_buffer: list[str] = []
        # cached asset modules for domain overlays
        self._asset_modules: dict[str, object] = {}

    def _push_log(self, text: str | None):
        if not text:
            return
        clean = _clamp(str(text), 96)
        if not clean.strip():
            return
        self._log_buffer.append(clean)
        # keep last few lines
        if len(self._log_buffer) > 8:
            self._log_buffer = self._log_buffer[-8:]

    def _last_logs(self, n: int = 3) -> list[str]:
        n = max(0, int(n))
        logs = self._log_buffer[-n:]
        while len(logs) < n:
            logs.insert(0, "")
        return logs

    def _asset_module_filename(self, technique_key: str) -> str | None:
        mapping = {
            "Dancer": "dance.py",
            "Bouncer": "bounce.py",
            "Seeker": "banlag.py",
        }
        return mapping.get(technique_key)

    def _load_asset_module(self, technique_key: str):
        """Load and cache the asset module for a technique key, if present."""
        if technique_key in self._asset_modules:
            return self._asset_modules[technique_key]

        fname = self._asset_module_filename(technique_key)
        if not fname:
            return None

        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "ascii_arts"))
        path = os.path.join(base, fname)
        if not os.path.exists(path):
            return None

        try:
            # Read and execute the asset file in an isolated module namespace.
            # This avoids using importlib utilities while staying within the
            # Python standard library (no external packages).
            with open(path, "r", encoding="utf-8") as f:
                src = f.read()
            module = types.ModuleType(f"domain_asset_{technique_key.lower()}")
            module.__file__ = path
            exec(compile(src, path, "exec"), module.__dict__)
            self._asset_modules[technique_key] = module
            return module
        except Exception:
            return None

    def _render_asset_overlay(self, technique_key: str, frame: int, width: int, height: int = 7) -> list[str] | None:
        """Return a list of ANSI lines from the asset module or None."""
        mod = self._load_asset_module(technique_key)
        if not mod:
            return None
        render_fn = getattr(mod, "render_domain_frame", None)
        if not callable(render_fn):
            return None
        try:
            lines = render_fn(frame, width, height)
            return list(lines) if lines else None
        except Exception:
            return None

    def _sync_offsets(self):
        self.window.update_offsets()
        self.ox = self.window.offset_x
        self.oy = self.window.offset_y

    def color(self, text, color):
        return color_text(text, color)

    def _frame_buffer(self, title: str) -> str:
        self._sync_offsets()
        return self.window.draw_frame(title)

    def _write_full(self, buffer: str):
        sys.stdout.write(f"{ESC}H" + buffer + RESET)
        sys.stdout.flush()

    def _battle_panel_buffer(
        self,
        *,
        title: str,
        parsed: dict,
        message: str,
        cmd_options: list[str] | None = None,
        selected: int = 0,
        menu_start: int = 0,
        footer: str | None = None,
        side_lines: list[str] | None = None,
        side_title: str = "ACTIVITY",
        frame: int = 0,
    ) -> str:

        self._sync_offsets()
        buf = self._frame_buffer(title)
        inner_w = self.window.width - 4
        panel_w = inner_w
        px = self.ox + 2
        buf, _ = _render_pokemon_combat_panel(
            buf=buf,
            oy=self.oy,
            px=px,
            panel_w=panel_w,
            frame=frame,
            parsed=parsed,
            message=message,
            cmd_options=cmd_options,
            selected=selected,
            menu_start=menu_start,
            side_lines=side_lines,
            side_title=side_title,
        )
        footer_text = footer or ""
        # Footer spans full frame width and should start at the left border
        buf += f"{ESC}{self.oy + self.window.height - 1};{self.ox}H{_footer_bar(self.window.width, footer_text)}"
        return buf

    def screen(self, title, lines=None, status_lines=None, footer=None):
        """Full-frame message; wait for Enter."""
        for ln in list(lines or [])[:4]:
            if isinstance(ln, str):
                self._push_log(ln)
        buf = self._frame_buffer(title)
        row = 3
        inner_w = self.window.width - 4

        if status_lines:
            buf += f"{ESC}{self.oy + row};{self.ox + 2}H{FG_LABEL}── STATUS ──{RESET}"
            row += 1
            for sl in status_lines:
                buf += f"{ESC}{self.oy + row};{self.ox + 2}H{FG_DIM}{_clamp(sl, inner_w)}{RESET}"
                row += 1
            row += 1

        for line in lines or []:
            if line is None:
                row += 1
                continue
            buf += f"{ESC}{self.oy + row};{self.ox + 2}H{FG_WHITE}{_clamp(line, inner_w)}{RESET}"
            row += 1

        if footer:
            row = max(row, self.window.height - 4)
            buf += f"{ESC}{self.oy + row};{self.ox + 2}H{FG_DIM}{_clamp(footer, inner_w)}{RESET}"

        self._write_full(buf)
        self.stop(None)

    def stop(self, message):
        """Wait for Enter; `message` None = silent (footer already on screen)."""
        prompt_row = self.window.offset_y + self.window.height - 2
        if message:
            sys.stdout.write(
                f"{ESC}{prompt_row};{self.window.offset_x + 2}H{FG_DIM}{_clamp(message, self.window.width - 4)}{RESET}"
            )
            sys.stdout.flush()
        while True:
            key = get_keypress()
            if key == "ENTER":
                return
            if key == "":
                continue

    def loading(self, title, message, status_lines=None, status_data=None, seconds=1.8, interval=0.35):
        self._push_log(message)
        effective = max(0.35, float(seconds) * 0.75)
        step = max(0.12, float(interval) * 0.85)
        end = time.monotonic() + effective
        dot = 0
        parsed = status_data if status_data is not None else (_parse_combat_status(list(status_lines or [])) if status_lines else None)

        while time.monotonic() < end:
            dots = "." * ((dot % 3) + 1)
            if parsed:
                buf = self._battle_panel_buffer(
                    title=title,
                    parsed=parsed,
                    message=f"{message} {dots}",
                    footer="Processing battle flow. Controls hidden until this resolves.",
                    side_lines=self._last_logs(3),
                    side_title="ACTIVITY",
                    frame=dot,
                )
            else:
                buf = self._frame_buffer(title)
                row = 5
                inner_w = self.window.width - 4
                buf += f"{ESC}{self.oy + row};{self.ox + 2}H{FG_WHITE}{_clamp(message, inner_w)}{RESET}"
                row += 2
                if status_lines:
                    for sl in status_lines:
                        buf += f"{ESC}{self.oy + row};{self.ox + 2}H{FG_DIM}{_clamp(sl, inner_w)}{RESET}"
                        row += 1
                    row += 1
                buf += f"{ESC}{self.oy + row};{self.ox + 2}H{FG_LABEL}Loading{dots}{RESET}"
            self._write_full(buf)
            dot += 1
            time.sleep(step)

    def battle_message(self, title, message, status_lines=None, seconds=1.2, footer=None, side_lines=None, side_title="ACTIVITY"):
        """Inline combat-state message that preserves the battle layout and hides controls."""
        raw_status = list(status_lines or [])
        parsed = _parse_combat_status(raw_status)
        if not parsed:
            self.loading(title, message, status_lines=raw_status, seconds=seconds)
            return

        self._push_log(message)
        buf = self._battle_panel_buffer(
            title=title,
            parsed=parsed,
            message=message,
            footer=footer or "Controls hidden while this action resolves.",
            side_lines=side_lines or self._last_logs(3),
            side_title=side_title,
        )
        self._write_full(buf)
        time.sleep(max(0.35, float(seconds)))

    def menu(self, title, options, status_callback=None, allow_escape=False, help_text=None):
        """Animated menu supporting both 2x2 command grids and scrolling lists."""
        if not options:
            return 0

        default_help = "Press {}–{} — instant select.".format(1, len(options))
        help_text = help_text or default_help

        frame = 0
        last_redraw = 0.0
        redraw_interval = 0.11  # subtle animation while waiting
        # Cursor selection for Pokémon-like 2x2 command box (only when <=4 options).
        selected = 0

        while True:
            now = time.monotonic()
            # non-blocking input so we can animate
            key = get_keypress_nb()
            if key is not None:
                if allow_escape and key == "ESC":
                    return None
                if key in ("LEFT", "RIGHT", "UP", "DOWN"):
                    if len(options) <= 4:
                        # 2x2 grid navigation
                        if key == "LEFT":
                            selected = selected - 1 if (selected % 2 == 1) else selected
                        elif key == "RIGHT":
                            selected = selected + 1 if (selected % 2 == 0) else selected
                        elif key == "UP":
                            selected = selected - 2 if (selected >= 2) else selected
                        elif key == "DOWN":
                            selected = selected + 2 if (selected <= 1) else selected
                        selected = max(0, min(3, selected))
                    else:
                        if key == "UP":
                            selected -= 1
                        elif key == "DOWN":
                            selected += 1
                        elif key == "LEFT":
                            selected -= 4
                        elif key == "RIGHT":
                            selected += 4
                        selected = max(0, min(len(options) - 1, selected))
                elif key == "ENTER":
                    return validate_menu_index(selected, options)
                elif isinstance(key, str) and key.isdigit():
                    try:
                        selected = validate_menu_index(int(key) - 1, options)
                    except ValidationError:
                        # ignore invalid numbers
                        pass

            if now - last_redraw < redraw_interval:
                time.sleep(0.02)
                continue

            last_redraw = now
            frame += 1

            self._sync_offsets()
            buf = self._frame_buffer(title)
            inner_w = self.window.width - 4
            panel_w = inner_w
            px = self.ox + 2

            raw_status: list[str] = []
            if status_callback:
                raw_status = list(status_callback())
            parsed = _parse_combat_status(raw_status)

            if parsed:
                if len(options) <= 4:
                    # Gameplay prompt should not mirror the full option text into the message log (it can become cramped).
                    msg = f"What will {parsed.get('player_name', 'Player')} do?  ({selected + 1})"
                    footer_text = "[ ARROWS ] Move  [ ENTER ] Confirm  [ ESC ] Quit"
                    menu_start = 0
                else:
                    menu_start = _menu_window_start(selected, len(options), 4)
                    msg = f"Selected: {selected + 1}. {options[selected]}"
                    footer_text = "[ UP/DOWN ] Move  [ LEFT/RIGHT ] Page  [ ENTER ] Confirm"
                    if allow_escape:
                        footer_text += "  [ ESC ] Back"

                buf = self._battle_panel_buffer(
                    title=title,
                    parsed=parsed,
                    message=msg,
                    cmd_options=list(options),
                    selected=selected,
                    menu_start=menu_start,
                    side_lines=self._last_logs(3),
                    footer=footer_text,
                    frame=frame,
                )
            else:
                # fallback (non-combat menus)
                hdr = FG_LABEL + "── ACTIONS ──" + RESET
                row = 3
                buf += f"{ESC}{self.oy + row};{px}H{_pad_ansi_line(hdr, panel_w)}"
                row += 1
                for i, opt in enumerate(options):
                    idx = i + 1
                    inner = (
                        f"{Colors.BRIGHT_YELLOW}[{idx}]{RESET} "
                        f"{Colors.WHITE}{_clamp(opt, panel_w - 8)}{RESET}"
                    )
                    buf += f"{ESC}{self.oy + row};{px}H{_pad_ansi_line(inner, panel_w)}"
                    row += 1
                row += 1
                help_rendered = _render_help_footer(help_text, len(options), allow_escape)
                inner = _clamp(help_rendered, panel_w)
                buf += f"{ESC}{self.oy + row};{px}H{_pad_ansi_line(inner, panel_w)}"
                row += 1
            self._write_full(buf)

    def attack_animation(
        self,

        title,
        attacker_name,
        defender_name,
        attack_name,
        defender_defending=False,
        indicator_label=None,
        status_lines=None,
        status_data=None,
        seconds=1.1,
        shake=False,
    ):
        effective = max(0.5, float(seconds))
        frames = max(7, int(effective / 0.08))
        label = (
            str(indicator_label).upper()
            if indicator_label is not None
            else ("DEFENDING" if defender_defending else "ATTACKING")
        )

        for frame in range(frames):
            if frame == 0:
                self._push_log(f"{attacker_name} used {attack_name}.")

            # resolve HUD so the animation matches the Pokémon layout
            if status_data is not None:
                st = status_data() if callable(status_data) else status_data
            else:
                st = status_lines() if callable(status_lines) else status_lines
            parsed = _parse_combat_status(list(st or [])) if st else None

            # prepare base buffers and geometry
            inner_w = self.window.width - 4
            panel_w = inner_w
            px = self.ox + 2

            # projectile line (separate so we don't have to splice ANSI battlefield)
            if parsed:
                inner = panel_w
                travel = int((frame / max(1, frames - 1)) * max(12, inner - 24))
                left_to_right = attacker_name == parsed.get("player_name")
                pos = (4 + travel) if left_to_right else (inner - 12 - travel)
                spark = f"{Colors.BRIGHT_YELLOW}✦{RESET}"
                trail = f"{FG_DIM}{'·' * (2 + (frame % 3))}{RESET}"
                proj_line = (" " * max(0, pos)) + spark + " " + trail

                msg = f"{attacker_name} used {attack_name}!  [{label}]"
                buf = self._battle_panel_buffer(
                    title=title,
                    parsed=parsed,
                    message=msg,
                    footer="Attack resolving. Controls hidden until impact.",
                    side_lines=self._last_logs(3),
                    side_title="COMBAT FEED",
                    frame=frame,
                )
                proj_row = self.oy + 11
                buf += f"{ESC}{proj_row};{px}H{_pad_ansi_line(_clamp(proj_line, inner), inner)}"
            else:
                # fallback: build a minimal parsed HUD so we can overlay the
                # animation without clearing the whole UI.
                minimal_parsed = {
                    "stage": 0,
                    "battle_time": "00:00",
                    "enemy_hp": 0,
                    "enemy_max": 0,
                    "hp": 0,
                    "hp_max": 0,
                    "domain": 0,
                    "instability": 0,
                    "player_name": attacker_name or "PLAYER",
                    "player_class": "Seeker",
                    "enemy_name": defender_name or "ENEMY",
                    "enemy_type": "",
                }

                msg = f"{attacker_name} → {defender_name}  {attack_name} [{label}]"
                buf = self._battle_panel_buffer(
                    title=title,
                    parsed=minimal_parsed,
                    message=msg,
                    footer="Attack resolving. Controls hidden until impact.",
                    side_lines=self._last_logs(3),
                    side_title="COMBAT FEED",
                    frame=frame,
                )
                # small floating box centered near the battlefield
                float_w = min(40, inner_w - 8)
                float_x = px + (inner_w - float_w) // 2
                float_y = self.oy + 9
                box = _box_lines("", float_w, [f"{attacker_name} used {attack_name}", f"[{label}]"], title_color=FG_LABEL)
                for i, ln in enumerate(box):
                    buf += f"{ESC}{float_y + i};{float_x}H{_pad_ansi_line(_clamp(ln, float_w), float_w)}"

            self._write_full(buf)
            time.sleep(0.08)

    def domain_activation_animation(
        self,
        title,
        attacker_name,
        defender_name,
        domain_name,
        technique_key,
        status_lines=None,
        status_data=None,
        seconds=1.1,
        interval=0.09,
    ):
        effective = max(0.6, float(seconds))
        steps = max(6, int(effective / float(interval)))
        glyphs = ["░", "▒", "▓", "█"]
        for i in range(steps):
            if i == 0:
                self._push_log(f"DOMAIN EXPANSION: {domain_name}")

            if status_data is not None:
                st = status_data() if callable(status_data) else status_data
            else:
                st = status_lines() if callable(status_lines) else status_lines
            parsed = _parse_combat_status(list(st or [])) if st else None

            buf = self._frame_buffer(title)
            inner_w = self.window.width - 4
            panel_w = inner_w
            px = self.ox + 2

            g = glyphs[i % len(glyphs)]
            aura = f"{Colors.BRIGHT_RED}{g * (10 + (i % 6))}{RESET}"
            msg = f"DOMAIN EXPANSION!!!  {domain_name}"

            if parsed:
                # Render the regular battle panel and then overlay a shifted
                # battlefield pass to make the Domain feel like it "shifts" the world.
                buf = self._battle_panel_buffer(
                    title=title,
                    parsed=parsed,
                    message=msg,
                    footer="Choose Defend or Attack.",
                    side_lines=[
                        "Reality folds inward.",
                        domain_name,
                        "Choose your stance inside the domain.",
                    ],
                    side_title="DOMAIN SHIFT",
                    frame=i,
                )
                # Overlay a second battlefield with an offset and amplified frame
                # to create a subtle lateral/world-shift effect.
                inner_w = self.window.width - 4
                px = self.ox + 2
                try:
                    bf_lines = _pokemon_battlefield(int(i * 3), inner_w - 2, parsed.get("player_class", "Seeker"), parsed.get("enemy_name", "Enemy"), parsed.get("enemy_type", ""), parsed.get("stage", 1))
                    for idx, ln in enumerate(bf_lines):
                        buf += f"{ESC}{self.oy + 7 + idx};{px + 2}H{_pad_ansi_line(ln, inner_w - 2)}"
                except Exception:
                    # Non-critical: if overlay fails, continue with the base panel.
                    pass
                aura_row = self.oy + 11
                aura_line = _center_ansi_line(aura, panel_w)
                buf += f"{ESC}{aura_row};{px}H{aura_line}"
                # Attempt to overlay technique-specific ASCII art
                asset_lines = self._render_asset_overlay(technique_key, i, inner_w)
                if asset_lines:
                    overlay_w = max((_visible_len(l) for l in asset_lines), default=0)
                    overlay_x = self.ox + (self.window.width - overlay_w) // 2
                    overlay_y = self.oy + 8
                    for idx, ln in enumerate(asset_lines):
                        buf += f"{ESC}{overlay_y + idx};{overlay_x}H{_pad_ansi_line(_clamp(ln, overlay_w), overlay_w)}"
            else:
                buf += f"{ESC}{self.oy + 8};{self.ox + 2}H{color_text(domain_name, Colors.BRIGHT_RED)}{RESET}"
                buf += f"{ESC}{self.oy + 10};{self.ox + 2}H{_clamp(msg, inner_w)}{RESET}"

            self._write_full(buf)
            time.sleep(float(interval))

    def domain_expansion_animation(
        self,
        title,
        attacker_name,
        defender_name,
        domain_name,
        technique_key,
        status_lines=None,
        status_data=None,
        duration_seconds=30.0,
        interval=0.25,
    ):
        """Domain barrier timer.

        UX request:
        - Keep battle HUD visible (no black screen).
        - Render the domain timer as top-center boxed overlay.
        - Use two-layer box: outer stable "DOMAIN TIMER" frame + inner
          live countdown box (updates each tick).
        """
        duration_seconds = max(1.0, float(duration_seconds))
        interval = max(0.08, float(interval))
        start = time.monotonic()
        logged = False

        presets = {
            "Dancer": ("Death Dancing Arena — trap locked", "░▒▓█"),
            "Bouncer": ("Silent Rebound Palace — sound erased", "·•‧"),
            "Seeker": ("Eye of Padullon — copies swarm", "^>*"),
        }
        _, glyph_set = presets.get(technique_key, presets["Seeker"])
        msgs = [
            "Reality distortion intensifies...",
            "Pressure inside the barrier rises...",
            "The curse resists your dominance...",
            "Cursed energy drains without mercy...",
        ]

        # Deterministic integer mapping for timer/barrier
        total_secs_i = int(math.ceil(duration_seconds))
        BAR_WIDTH = 24

        # Snapshot initial parse and compute overlay geometry once to avoid
        # per-tick re-centering or full-panel rebuilds.
        if status_data is not None:
            st0 = status_data() if callable(status_data) else status_data
        else:
            st0 = status_lines() if callable(status_lines) else status_lines

        parsed = _parse_combat_status(list(st0 or [])) if st0 else None

        # compute offsets & overlay geometry once
        self._sync_offsets()
        inner_w = self.window.width - 4

        if parsed:
            # Precompute centered outer/inner box positions based on current window.
            outer_w = min(int(inner_w - 4), 60)
            outer_w = max(50, outer_w)
            outer_y = self.oy + 7
            outer_x = self.ox + (self.window.width - outer_w) // 2

            inner_y = outer_y + 2
            inner_w_box = max(28, outer_w - 10)
            inner_x = outer_x + (outer_w - inner_w_box) // 2

            # Render the stable base once (no per-tick full redraw).
            base_buf = self._battle_panel_buffer(
                title=title,
                parsed=parsed,
                message="",
                footer="Domain active.",
                side_lines=self._last_logs(3),
                side_title="DOMAIN",
                frame=0,
            )
            self._write_full(base_buf)
        else:
            # Fallback layout when HUD parsing is unavailable.
            overlay_w = min(inner_w - 4, 52)
            outer_w = overlay_w
            outer_y = self.oy + 7
            outer_x = self.ox + (self.window.width - outer_w) // 2

            inner_y = outer_y + 2
            inner_w_box = max(26, outer_w - 10)
            inner_x = self.ox + (self.window.width - inner_w_box) // 2

            base_buf = self._frame_buffer(title)
            self._write_full(base_buf)

        # Main overlay-only loop
        while True:
            elapsed = time.monotonic() - start
            if not logged:
                self._push_log(f"Domain active: {domain_name}")
                logged = True

            remaining = max(0.0, duration_seconds - elapsed)
            remaining_i = int(math.ceil(remaining)) if remaining > 0 else 0

            # Deterministic fill mapping using integer seconds -> avoids jitter
            if total_secs_i > 0:
                fill = (remaining_i * BAR_WIDTH + total_secs_i - 1) // total_secs_i
            else:
                fill = 0
            fill = max(0, min(BAR_WIDTH, int(fill)))

            g = glyph_set[int(elapsed * 4) % len(glyph_set)]
            barrier_bar = f"{Colors.BRIGHT_RED}{g * fill}{FG_DIM}{'·' * (BAR_WIDTH - fill)}{RESET}"

            msg = msgs[int(elapsed * 2) % len(msgs)]
            timer_line = f"{Colors.CYAN}T-{remaining_i:02d}s{RESET}"
            duel_line = f"{attacker_name} vs {defender_name}"

            # Build overlay content only (outer + inner boxes) and write in-place.
            overlay_buf = ""

            outer_body = [
                f"{FG_LABEL}DOMAIN TIMER{RESET}",
                f"{Colors.MAGENTA}{domain_name.upper()}{RESET}",
                "",
            ]
            outer_box = _box_lines(title="", width=outer_w, body_lines=outer_body, title_color=FG_LABEL)
            for i, ln in enumerate(outer_box):
                overlay_buf += f"{ESC}{outer_y + i};{outer_x}H{_pad_ansi_line(_clamp(ln, outer_w), outer_w)}"

            inner_box = _box_lines(
                title="",
                width=inner_w_box,
                body_lines=[f"{FG_LABEL}BARRIER{RESET} {barrier_bar}", timer_line, duel_line],
                title_color=Colors.BRIGHT_RED,
            )
            for i, ln in enumerate(inner_box):
                overlay_buf += f"{ESC}{inner_y + i};{inner_x}H{_pad_ansi_line(_clamp(ln, inner_w_box), inner_w_box)}"

            # Write only the overlay to avoid repainting the whole panel.
            sys.stdout.write(overlay_buf)
            sys.stdout.flush()

            if remaining <= 0:
                break

            # Allow interrupt keys during long domain without consuming gameplay state
            deadline = time.monotonic() + interval
            while time.monotonic() < deadline:
                nb = get_keypress_nb()
                if nb is None:
                    time.sleep(0.02)
                    continue
                if nb == "ESC":
                    return
                break


    def domain_attack_animation(
        self,
        title,
        attacker_name,
        defender_name,
        domain_name,
        technique_key,
        status_lines=None,
        status_data=None,
        seconds=1.2,
        shake=False,
        **kwargs,
    ):
        """Domain strike animation (impact pulse + cracks).

        Replaces the prior proxy to `attack_animation()` so domain hits look
        clearly different and more cinematic while still keeping the battle HUD.
        """
        _ = kwargs
        seconds = max(0.6, float(seconds))
        frames = max(7, int(seconds / 0.09))

        tag_map = {
            "Dancer": "TRAP SLAM",
            "Bouncer": "SOUNDLESS IMPACT",
            "Seeker": "EYE STRIKE",
        }
        strike_label = tag_map.get(technique_key, "DOMAIN STRIKE")

        self._push_log(f"{domain_name}: {strike_label}")

        for frame in range(frames):
            # Resolve HUD data for stable battlefield rendering.
            if status_data is not None:
                st = status_data() if callable(status_data) else status_data
            else:
                st = status_lines() if callable(status_lines) else status_lines
            parsed = _parse_combat_status(list(st or [])) if st else None

            if parsed:
                buf = self._battle_panel_buffer(
                    title=title,
                    parsed=parsed,
                    message=f"{domain_name} {strike_label}",
                    footer="Domain impact! (Hit resolving...)",
                    side_lines=self._last_logs(3),
                    side_title="DOMAIN",
                    frame=frame,
                )

                # Center impact box near the top-center region for prominence.
                inner_w = self.window.width - 4
                px = self.ox + 2

                base_w = min(inner_w - 4, 56)
                # quick horizontal "shake" of the box only
                drift = 0
                if shake and frame % 2 == 0:
                    drift = 1 if (frame // 2) % 2 == 0 else -1

                box_w = base_w
                box_x = px + 2 + (inner_w - box_w) // 2 + drift
                box_y = self.oy + 6

                pulse_strength = max(0, frames - frame) / frames  # 1..0
                bar_fill = max(0, min(24, int(round(pulse_strength * 24))))
                pulse_char = "█" if technique_key == "Dancer" else ("▓" if technique_key == "Bouncer" else "◆")
                pulse_bar = f"{Colors.BRIGHT_RED}{pulse_char * bar_fill}{FG_DIM}{'·' * (24 - bar_fill)}{RESET}"

                # Cracks around the impact center (varies per frame)
                crack_sets = [
                    ["╳╳╳", "///", "•••", "╱╲╱╲"],
                    ["╳//╳", "///", "••••", "╲╱╲╱"],
                    ["╳╳╳", "/\\/\\", "•••", "╱╲╱╲"],
                ]
                cracks = crack_sets[frame % len(crack_sets)]

                msg1 = f"{Colors.BRIGHT_YELLOW}{domain_name.upper()}{RESET}"
                msg2 = f"{FG_LABEL}DOMAIN STRIKE{RESET} {pulse_bar}"
                msg3 = f"{strike_label}"
                msg4 = f"CRACK: {cracks[frame % len(cracks)]}"

                impact_box = _box_lines(
                    title="",
                    width=box_w,
                    body_lines=[msg1, msg2, msg3, msg4][:3],  # keep box compact
                    title_color=Colors.BRIGHT_RED,
                )

                # If _box_lines returns 3 lines, align safely; otherwise draw all.
                for i, ln in enumerate(impact_box):
                    buf += f"{ESC}{box_y + i};{box_x}H{_pad_ansi_line(_clamp(ln, box_w), box_w)}"

                # Add a small center "impact glyph" on the battlefield itself.
                # This uses direct placement to avoid relying on projectile animation.
                center_row = self.oy + 13
                center_col = px + (inner_w // 2) - 2
                glyph = "✹" if technique_key == "Seeker" else ("✶" if technique_key == "Bouncer" else "✸")
                intensity = 1 + (frame % 3)
                glyph_line = f"{Colors.BRIGHT_YELLOW}{glyph * intensity}{RESET}"
                buf += f"{ESC}{center_row};{center_col}H{glyph_line}"
                # overlay technique-specified ASCII art (if available)
                asset_lines = self._render_asset_overlay(technique_key, frame, inner_w)
                if asset_lines:
                    overlay_w = max((_visible_len(l) for l in asset_lines), default=0)
                    overlay_x = self.ox + (self.window.width - overlay_w) // 2
                    overlay_y = self.oy + 8
                    for idx, ln in enumerate(asset_lines):
                        buf += f"{ESC}{overlay_y + idx};{overlay_x}H{_pad_ansi_line(_clamp(ln, overlay_w), overlay_w)}"
            else:
                # Fallback: ensure we still render the battle HUD (minimal)
                minimal_parsed = {
                    "stage": 0,
                    "battle_time": "00:00",
                    "enemy_hp": 0,
                    "enemy_max": 0,
                    "hp": 0,
                    "hp_max": 0,
                    "domain": 0,
                    "instability": 0,
                    "player_name": attacker_name or "PLAYER",
                    "player_class": "Seeker",
                    "enemy_name": defender_name or "ENEMY",
                    "enemy_type": "",
                }

                buf = self._battle_panel_buffer(
                    title=title,
                    parsed=minimal_parsed,
                    message=f"{domain_name} {strike_label}",
                    footer="Domain impact! (Hit resolving...)",
                    side_lines=self._last_logs(3),
                    side_title="DOMAIN",
                    frame=frame,
                )

                # small centered impact label overlay for non-parsed state
                inner_w = self.window.width - 4
                px = self.ox + 2
                overlay_w = min(40, inner_w - 8)
                overlay_x = px + (inner_w - overlay_w) // 2
                overlay_y = self.oy + 8
                overlay_lines = _box_lines("", overlay_w, [f"{domain_name} {strike_label}"], title_color=Colors.BRIGHT_RED)
                for i, ln in enumerate(overlay_lines):
                    buf += f"{ESC}{overlay_y + i};{overlay_x}H{_pad_ansi_line(_clamp(ln, overlay_w), overlay_w)}"
                # also try asset overlay for fallback HUD
                asset_lines = self._render_asset_overlay(technique_key, frame, inner_w)
                if asset_lines:
                    overlay_w = max((_visible_len(l) for l in asset_lines), default=0)
                    overlay_x = self.ox + (self.window.width - overlay_w) // 2
                    overlay_y = self.oy + 8
                    for idx, ln in enumerate(asset_lines):
                        buf += f"{ESC}{overlay_y + idx};{overlay_x}H{_pad_ansi_line(_clamp(ln, overlay_w), overlay_w)}"

            self._write_full(buf)
            time.sleep(0.09)

    def prompt_text(self, prompt, title="Cursed Domination"):
        """Optional: free text (not used by combat loop)."""
        buf = self._frame_buffer(title)
        buf += f"{ESC}{self.oy + 10};{self.ox + 2}H{FG_WHITE}{_clamp(prompt, self.window.width - 4)}{RESET}"
        buf += f"{ESC}{self.oy + 12};{self.ox + 2}H{FG_LABEL}> {RESET}"
        self._write_full(buf)
        line = ""
        while True:
            key = get_keypress()
            if key == "ENTER":
                return line.strip()
            if key == "BACKSPACE":
                line = line[:-1]
            elif isinstance(key, str) and len(key) == 1 and key.isprintable():
                line += key

    def collapse_screen(self, title, lines=None, footer=None, flashes=6, delay=0.08):
        """Instability collapse — simplified single screen."""
        self.screen(title, list(lines or []), footer=footer)
