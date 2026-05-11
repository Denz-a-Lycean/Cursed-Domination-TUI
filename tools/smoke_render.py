from core.engine import WindowManager, ESC, RESET
from systems.ansi_game_presenter import AnsiGamePresenter, _render_at, _pad_ansi_line, _build_ui_test_menu_lines
import re

ANSI_RE = re.compile(r"\033\[[0-9;]*m")
ESC_RE = re.compile(r"\033\[(\d+);(\d+)H")


def print_separator(name):
    print("\n" + "=" * 80)
    print(name)
    print("=" * 80 + "\n")


def render_frame_with_lines(window, title, lines):
    win = window
    win.update_offsets()
    oy = win.offset_y
    ox = win.offset_x
    buf = win.draw_frame(title)
    inner_w = win.width - 4
    px = ox + 2
    row = 3
    for ln in lines:
        buf += f"{ESC}{oy + row};{px}H{ln}{RESET}"
        row += 1
    print(buf)


def render_and_show_grid(buf, window):
    # Build an empty grid for the design area
    h = window.height
    w = window.width
    oy = window.offset_y
    ox = window.offset_x
    grid = [[" " for _ in range(w)] for _ in range(h)]

    # Iterate ESC sequences and place visible text
    matches = list(ESC_RE.finditer(buf))
    for idx, m in enumerate(matches):
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(buf)
        text = buf[start:end]
        try:
            row = int(m.group(1))
            col = int(m.group(2))
        except Exception:
            continue
        visible = ANSI_RE.sub('', text)
        r = row - oy
        c = col - ox
        if 0 <= r < h:
            for j, ch in enumerate(visible):
                if 0 <= c + j < w:
                    grid[r][c + j] = ch

    # Print grid lines
    for row in grid:
        print(''.join(row))


if __name__ == '__main__':
    w = WindowManager()
    w.update_offsets()
    p = AnsiGamePresenter(w)

    # 1) Main Menu (non-combat fallback)
    main_lines = []
    main_lines.append('\x1b[97mWelcome to Cursed Domination\x1b[0m')
    main_lines.append('')
    opts = ['Start Campaign', 'Load Game', 'Options', 'Quit']
    for i, o in enumerate(opts, 1):
        main_lines.append(f"\x1b[93m[{i}]\x1b[0m \x1b[97m{o}\x1b[0m")
    print_separator('Main Menu')
    buf_main = w.draw_frame('MAIN MENU')
    # add lines
    oy = w.offset_y
    ox = w.offset_x
    px = ox + 2
    row = 3
    for ln in main_lines:
        buf_main += f"{ESC}{oy + row};{px}H{ln}{RESET}"
        row += 1
    render_frame_with_lines(w, 'MAIN MENU', main_lines)
    print_separator('Main Menu Grid (stripped)')
    render_and_show_grid(buf_main, w)

    # 2) Gameplay HUD (use _build_ui_test_menu_lines)
    parsed = {
        'game_time': '00:00',
        'battle_time': '00:20',
        'player_name': 'ALICE',
        'player_class': 'Seeker',
        'hp': 12,
        'hp_max': 20,
        'domain': 34,
        'instability': 2,
        'defending': False,
        'enemy_name': 'GOBLIN',
        'enemy_type': 'fast',
        'stage': 2,
        'enemy_hp': 40,
        'enemy_max': 50,
    }
    opts = ['Strike', 'Defend', 'Item', 'Escape']
    hud_lines = _build_ui_test_menu_lines(parsed, opts, panel_w=w.width - 4, help_text=None, allow_escape=True)
    print_separator('Gameplay HUD')
    buf_hud = w.draw_frame('GAMEPLAY')
    oy = w.offset_y
    ox = w.offset_x
    px = ox + 2
    row = 3
    for ln in hud_lines:
        buf_hud += f"{ESC}{oy + row};{px}H{ln}{RESET}"
        row += 1
    render_frame_with_lines(w, 'GAMEPLAY', hud_lines)
    print_separator('Gameplay Grid (stripped)')
    render_and_show_grid(buf_hud, w)

    # 3) Combat panel
    combat_buf = p._battle_panel_buffer(
        title='COMBAT',
        parsed=parsed,
        message='An attack approaches...',
        cmd_options=opts,
        selected=0,
        menu_start=0,
        footer='[ENTER] Confirm',
        side_lines=['You struck for 5', 'Enemy prepares'],
        side_title='FEED',
        frame=2,
    )
    print_separator('Combat Panel')
    # Print raw combat buffer (ansi)
    print(combat_buf)
    print_separator('Combat Grid (stripped)')
    render_and_show_grid(combat_buf, w)
