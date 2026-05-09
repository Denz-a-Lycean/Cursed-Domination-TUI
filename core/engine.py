import os
import shutil
import time
import sys
import msvcrt
import math
import textwrap
import random
import subprocess
from utils.effects import glitch_text, set_glitch_level, advance_glitch_frame

# Enable Virtual Terminal Processing in Windows CMD/PowerShell for ANSI codes
os.system("")

# --- ANSI Escape Sequence Constants ---
ESC = "\033["
RESET = f"{ESC}0m"
CLEAR_SCREEN = f"{ESC}2J"

# RPG Theme Colors
BG_MAIN = f"{ESC}40m"          # Black Background
FG_BORDER = f"{ESC}90m"        # Dark Grey Borders
FG_TITLE = f"{ESC}91m"         # Bright Red Text
FG_LABEL = f"{ESC}93m"         # Gold/Yellow Text
FG_WHITE = f"{ESC}97m"         # White Text
BG_INPUT = f"{ESC}40m"         # Black Background (Inactive Input)
BG_INPUT_ACTIVE = f"{ESC}100m"  # Dark Grey Background (Active Input)
BG_CURSOR = f"{ESC}47m"        # White Background (Fake Cursor)
FG_BLACK = f"{ESC}30m"         # Black Text (For active buttons/cursors)
FG_DIM = f"{ESC}37m"           # Dim text for inactive/empty slots

# Small Kogane for conditional dialogue rendering
KOGANE_SMALL = [
    r"      _,-d888b-._",
    r"     d88888888888b",
    r"    d88' p88q `88b",
    r"    `d8bod88dob8b'",
    r"      `d888888d'",
    r"        `d88b'",
    r"          `d'"
]

# Simple color name -> escape code map for per-line overrides
COLOR_MAP = {
    "title": FG_TITLE,
    "label": FG_LABEL,
    "white": FG_WHITE,
    "dim": FG_DIM,
    "black": FG_BLACK,
    "red": "\033[91m",
    "cyan": "\033[96m",
    "gray": "\033[90m",
}

def get_asset_path(filename):
    """Helper to get the absolute path of an asset."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "assets", filename)

def get_ascii_art(filename):
    """Reads an ASCII art file from assets/ascii_arts."""
    path = os.path.join(get_asset_path("ascii_arts"), filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    return []

# ==========================================
# WIDGET CLASSES
# ==========================================


class Widget:
    """Base class for all UI components."""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.is_focusable = True

    def render(self, is_focused: bool) -> str:
        return ""

    def handle_key(self, key: str):
        return None


class Label(Widget):
    """Non-interactive text display."""

    def __init__(self, x: int, y: int, text: str, color: str = FG_WHITE):
        super().__init__(x, y)
        self.text = text
        self.color = color
        self.is_focusable = False

    def render(self, is_focused: bool) -> str:
        return f"{ESC}{self.y};{self.x}H{BG_MAIN}{self.color}{self.text}"


class TextBox(Widget):
    """Interactive text input field."""

    def __init__(
        self,
        x: int,
        y: int,
        label: str,
        input_x_offset: int,
        max_len: int = 20,
        cell_span: int = 1,
    ):
        super().__init__(x, y)
        self.label = label
        self.value = ""
        self.input_x_offset = input_x_offset
        self.max_len = max_len
        # Columns per character (1 = normal; 2 = gap after each glyph for legibility on some Windows fonts).
        self.cell_span = max(1, int(cell_span))

    def _field_width_cols(self) -> int:
        return self.max_len * self.cell_span

    def _paint_cell(self, y: int, col: int, bg: str, fg: str, ch: str) -> str:
        return f"{ESC}{y};{col}H{bg}{fg}{ch}"

    def render(self, is_focused: bool) -> str:
        # Terminate label styling before the input cell so colors cannot bleed across terminals.
        out = f"{ESC}{self.y};{self.x}H{BG_MAIN}{FG_LABEL}{self.label}{RESET}"
        input_x = self.x + self.input_x_offset
        y = self.y
        span = self.cell_span
        field_w = self._field_width_cols()

        if is_focused:
            cell_bg, cell_fg = BG_INPUT_ACTIVE, FG_BLACK
            cur_bg, cur_fg = BG_CURSOR, FG_BLACK
        else:
            cell_bg, cell_fg = BG_INPUT, FG_WHITE
            cur_bg = BG_INPUT

        # Paint field background first (avoids glyphs visually crowding on some hosts).
        out += f"{ESC}{y};{input_x}H{cell_bg}{cell_fg}" + (" " * field_w)

        for i, ch in enumerate(self.value):
            col = input_x + i * span
            if col + span > input_x + field_w:
                break
            out += self._paint_cell(y, col, cell_bg, cell_fg, ch)
            for j in range(1, span):
                out += self._paint_cell(y, col + j, cell_bg, cell_fg, " ")

        text_cols = len(self.value) * span
        if is_focused and len(self.value) < self.max_len:
            ccol = input_x + text_cols
            out += self._paint_cell(y, ccol, cur_bg, cur_fg, " ")
            fill_start = text_cols + 1
        else:
            fill_start = text_cols

        if fill_start < field_w:
            for col in range(input_x + fill_start, input_x + field_w):
                out += self._paint_cell(y, col, cell_bg, cell_fg, " ")

        return out + RESET

    def handle_key(self, key: str):
        if key == "UP":
            return "PREV"
        elif key in ("DOWN", "TAB"):
            return "NEXT"
        elif key == "BACKSPACE":
            self.value = self.value[:-1]
        elif len(key) == 1 and len(self.value) < self.max_len:
            self.value += key
        return None


class Button(Widget):
    """Interactive clickable button."""

    def __init__(self, x: int, y: int, label: str, action_name: str, is_enabled: bool = True):
        super().__init__(x, y)
        self.label = label
        self.action_name = action_name
        self.is_enabled = is_enabled

    def render(self, is_focused: bool) -> str:
        out = f"{ESC}{self.y};{self.x}H"
        if not self.is_enabled:
            out += f"{BG_MAIN}{FG_DIM} [ {self.label} ] "
        elif is_focused:
            out += f"{BG_CURSOR}{FG_BLACK} {self.label} {RESET}{BG_MAIN}"
        else:
            out += f"{BG_MAIN}{FG_WHITE} {self.label} "
        return out

    def handle_key(self, key: str):
        if key in ("UP", "LEFT"):
            return "PREV"
        elif key in ("DOWN", "RIGHT", "TAB"):
            return "NEXT"
        elif key == "ENTER" and self.is_enabled:
            return self.action_name
        return None


# ==========================================
# INPUT & DISPLAY MANAGEMENT
# ==========================================

def get_keypress():
    """Reads a single keypress from Windows msvcrt safely."""
    key = msvcrt.getch()
    if key in (b'\x00', b'\xe0'):
        key = msvcrt.getch()
        if key == b'H':
            return "UP"
        if key == b'P':
            return "DOWN"
        if key == b'K':
            return "LEFT"
        if key == b'M':
            return "RIGHT"
    elif key == b'\r':
        return "ENTER"
    elif key == b'\x08':
        return "BACKSPACE"
    elif key == b'\t':
        return "TAB"
    elif key == b'\x1b':
        return "ESC"
    else:
        try:
            char = key.decode('utf-8')
            if char.isprintable():
                return char
        except UnicodeDecodeError:
            pass
    return ""


def get_keypress_nb():
    """Non-blocking key read. Returns None when no key is available."""
    if not msvcrt.kbhit():
        return None
    key = msvcrt.getch()
    if key in (b'\x00', b'\xe0'):
        key = msvcrt.getch()
        if key == b'H':
            return "UP"
        if key == b'P':
            return "DOWN"
        if key == b'K':
            return "LEFT"
        if key == b'M':
            return "RIGHT"
    elif key == b'\r':
        return "ENTER"
    elif key == b'\x08':
        return "BACKSPACE"
    elif key == b'\t':
        return "TAB"
    elif key == b'\x1b':
        return "ESC"
    else:
        try:
            char = key.decode('utf-8')
            if char.isprintable():
                return char
        except UnicodeDecodeError:
            pass
    return None


class WindowManager:
    """Handles the terminal setup, teardown, and border drawing."""

    def __init__(self):
        # horizontal phone style: exactly 140 wide, 30 high
        self.width = 140  
        self.height = 30 
        self.offset_x = 0
        self.offset_y = 0

    def update_offsets(self):
        """Calculates offsets to keep the 140x30 design centered if the window is larger."""
        current_size = shutil.get_terminal_size()
        # Design target is 140x30
        design_w = 140
        design_h = 30
        
        self.offset_x = max(1, (current_size.columns - design_w) // 2)
        self.offset_y = max(1, (current_size.lines - design_h) // 2)
        
        # Internal dimensions including borders
        self.width = 140
        self.height = 30

    def setup(self):
        # Enable Alt Buffer (\033[?1049h), Hide Cursor (\033[?25l), Clear Screen (\033[2J)
        sys.stdout.write(f"{ESC}?1049h{ESC}?25l{ESC}2J")
        sys.stdout.flush()
        
        # Disable QuickEdit mode to prevent mouse clicks from freezing the game
        disable_qe = (
            "$api = '[DllImport(\"kernel32.dll\")] public static extern bool GetConsoleMode(IntPtr hConsoleHandle, out uint lpMode); "
            "[DllImport(\"kernel32.dll\")] public static extern bool SetConsoleMode(IntPtr hConsoleHandle, uint dwMode); "
            "[DllImport(\"kernel32.dll\")] public static extern IntPtr GetStdHandle(int nStdHandle);'; "
            "Add-Type -MemberDefinition $api -Name WinUtilEngine -Namespace Win32; "
            "$hStdin = [Win32.WinUtilEngine]::GetStdHandle(-10); "
            "$mode = 0; [Win32.WinUtilEngine]::GetConsoleMode($hStdin, [ref]$mode); "
            "$mode = $mode -band -not 0x0040 -band -not 0x0010; "
            "[Win32.WinUtilEngine]::SetConsoleMode($hStdin, $mode) | Out-Null;"
        )
        subprocess.run(["powershell.exe", "-Command", disable_qe], capture_output=True)

    def teardown(self):
        # Disable Alt Buffer (\033[?1049l), Show Cursor (\033[?25h), Reset Colors (\033[0m)
        sys.stdout.write(f"{RESET}{ESC}?25h{ESC}?1049l")
        sys.stdout.flush()

    def draw_frame(self, title: str) -> str:
        out = ""
        for y in range(self.height):
            out += f"{ESC}{self.offset_y + y};{self.offset_x}H{BG_MAIN}" + \
                (" " * self.width)

        title_str = f" {title} "
        dash_count = (self.width - 2 - len(title_str)) // 2
        top_border = "+" + ("=" * dash_count) + f"{FG_WHITE}{title_str}{FG_BORDER}" + (
            "=" * (self.width - 2 - dash_count - len(title_str))) + "+"
        out += f"{ESC}{self.offset_y};{self.offset_x}H{FG_BORDER}{top_border}"

        for y in range(1, self.height - 1):
            out += f"{ESC}{self.offset_y + y};{self.offset_x}H|"
            out += f"{ESC}{self.offset_y + y};{self.offset_x + self.width - 1}H|"

        bottom_border = "+" + ("=" * (self.width - 2)) + "+"
        out += f"{ESC}{self.offset_y + self.height - 1};{self.offset_x}H{bottom_border}"

        return out


# ==========================================
# SCREEN ARCHITECTURE
# ==========================================

class BaseScreen:
    """
    Blueprint for all game screens. 
    Handles focus management and rendering loops internally.
    """

    def __init__(self, window: WindowManager):
        self.window = window
        self.ox = window.offset_x
        self.oy = window.offset_y
        self.title = "Screen"
        self.widgets = []
        self.focus_index = 0

    def _update_layout_from_window(self):
        """Syncs screen offsets with window manager's current centering."""
        self.window.update_offsets()
        self.ox = self.window.offset_x
        self.oy = self.window.offset_y

    def _get_next_focus(self, current: int, direction: int) -> int:
        n = len(self.widgets)
        for _ in range(n):
            current = (current + direction) % n
            if self.widgets[current].is_focusable:
                return current
        return current

    def setup_ui(self):
        """Override this method to populate self.widgets in child classes."""
        pass

    def update(self):
        """Override this method to perform logic every frame (e.g., validation)."""
        pass

    def handle_key(self, key: str) -> str:
        """Processes input keys, delegating to the focused widget."""
        if not self.widgets:
            return None
        return self.widgets[self.focus_index].handle_key(key)

    def run(self) -> str:
        """Executes the screen's main loop and returns the next state identifier."""
        self._update_layout_from_window()
        self.setup_ui()
        self.focus_index = self._get_next_focus(-1, 1)  # Find first focusable

        # Cinematic Clear & Glitch Transition
        sys.stdout.write(f"{ESC}2J{ESC}H")
        for _ in range(3):
            # Flash random symbols
            glitch_str = "".join(random.choice("@#$%&!?") for _ in range(100))
            sys.stdout.write(f"{ESC}{self.oy + 15};{self.ox + 20}H{FG_TITLE}{glitch_str}{RESET}")
            sys.stdout.flush()
            time.sleep(0.04)
            sys.stdout.write(f"{ESC}2J")
        
        sys.stdout.write(f"{ESC}2J{ESC}H")
        sys.stdout.flush()

        while True:
            # Real-time size monitoring: Wait until fixed instead of exiting
            current_size = shutil.get_terminal_size()
            if current_size.columns < 140 or current_size.lines < 30:
                # Force a full clear of the alternate buffer to prevent ghosting
                sys.stdout.write(f"{ESC}H{ESC}J")
                sys.stdout.write(f"{FG_TITLE}ERROR: Terminal too small!{RESET}\n")
                sys.stdout.write(f"Current: {current_size.columns}x{current_size.lines}\n")
                sys.stdout.write(f"Required: 140x30\n\n")
                sys.stdout.write("Please resize or maximize the window to continue...\n")
                sys.stdout.write("\033[91mPress [X] to Force Close Game\033[0m")
                sys.stdout.flush()
                
                # Check for exit input multiple times during the wait to improve responsiveness
                for _ in range(10):
                    if msvcrt.kbhit():
                        if msvcrt.getch().lower() == b'x':
                            return "EXIT_NOW"
                    time.sleep(0.05)
                continue

            # Check if layout needs re-syncing due to size change
            old_ox, old_oy = self.ox, self.oy
            self._update_layout_from_window()
            
            # If the screen was moved or resized, we MUST clear the entire buffer
            # to prevent ghosting from previous positions.
            if self.ox != old_ox or self.oy != old_oy:
                sys.stdout.write(f"{ESC}2J")
                # Re-run setup_ui to ensure widgets are repositioned relative to new ox/oy
                self.setup_ui()

            # Logic update
            self.update()

            # Apply Cursed Distortion if instability > 0
            instability = 0
            if hasattr(self, "state") and self.state:
                instability = getattr(self.state, "instability", 0)
            
            set_glitch_level(instability)
            advance_glitch_frame()
            
            # Draw to a string buffer then write all at once (double buffering)
            buffer = self.window.draw_frame(self.title)

            # Apply glitching to the entire buffer
            if instability > 0:
                lines = buffer.split("\n")
                new_lines = []
                for i, line in enumerate(lines):
                    # Header/Footer glitching
                    intensity = "title" if i < 3 or i > len(lines)-4 else "body"
                    new_lines.append(glitch_text(line, intensity))
                buffer = "\n".join(new_lines)

            for i, widget in enumerate(self.widgets):
                rendered = widget.render(is_focused=(i == self.focus_index))
                if instability > 0:
                    rendered = glitch_text(rendered, "body")
                buffer += rendered

            # Move cursor to top-left and overwrite (prevents scrolling/flicker)
            buffer = f"{ESC}H" + buffer 
            # Move cursor out of the way before printing
            buffer += f"{RESET}{ESC}{self.window.offset_y + self.window.height + 1};0H"
            
            sys.stdout.write(buffer)
            sys.stdout.flush()

            key = get_keypress()
            if key == "ESC":
                return "EXIT"

            result = self.handle_key(key)

            if result == "NEXT":
                self.focus_index = self._get_next_focus(self.focus_index, 1)
            elif result == "PREV":
                self.focus_index = self._get_next_focus(self.focus_index, -1)
            elif result:
                return result


class SceneScreen(BaseScreen):
    """Scene rendering with non-blocking typing, wrapping/paging, and
    a subtle background animation to keep static ASCII alive.
    """

    def __init__(
        self,
        window: WindowManager,
        scene_data: dict,
        next_state=None,
        text_speed: float = 0.02,
        state=None,
    ):
        super().__init__(window)
        self.scene_data = scene_data
        self.dialogue_index = 0
        # Optional shared run state (player name, stage, etc.) for scripted scenes.
        self.state = state
        # Priority: constructor arg > scene_data['next_state'] > default
        self.next_state = next_state or scene_data.get("next_state") or "SCREEN_MAIN_MENU"
        self.title = scene_data.get("title", "Scene")
        self.text_speed = text_speed

    def _paginate(self, text: str, width: int, max_lines: int):
        """Wrap text to `width` and split into pages each having up to
        `max_lines` lines. Returns list of page strings."""
        wrapped = textwrap.wrap(text, width=width) or [""]
        pages = ["\n".join(wrapped[i:i+max_lines]) for i in range(0, len(wrapped), max_lines)]
        return pages

    def _normalize_ascii_lines(self, bg: str):
        """Trim only outer blank lines and normalize common left padding."""
        if not bg:
            return []
        raw_lines = bg.splitlines()
        while raw_lines and not raw_lines[0].strip():
            raw_lines.pop(0)
        while raw_lines and not raw_lines[-1].strip():
            raw_lines.pop()
        if not raw_lines:
            return []
        indents = [len(line) - len(line.lstrip(" ")) for line in raw_lines if line.strip()]
        min_indent = min(indents) if indents else 0
        return [line[min_indent:] if len(line) >= min_indent else "" for line in raw_lines]

    def run(self) -> str:
        self._update_layout_from_window()
        # Scene-level settings (meta overrides constructor defaults)
        meta = self.scene_data.get("meta", {}) or {}
        text_speed_default = meta.get("text_speed", self.text_speed)
        shift_amp_default = meta.get("shift_amp", 2)
        frame_rate = float(meta.get("frame_rate", 1.0) or 1.0)
        max_dialogue_lines = meta.get("max_dialogue_lines", 3)

        # backgrounds: support either a single background or a list of frames
        bg_static = self.scene_data.get("background", "")
        bg_frames = self.scene_data.get("background_frames") or meta.get("background_frames")

        dialogues = self.scene_data.get("dialogues", [])

        self.dialogue_index = 0
        self.page_index = 0
        self.char_index = 0
        reveal_acc = 0.0

        # layout metrics (initialized here, updated inside loop)
        left = self.ox + 2
        top = self.oy + 2
        content_width = self.window.width - 4
        dialog_width = self.window.width - 6

        last_time = time.perf_counter()

        # per-page/dialog state
        current_line_key = (None, None)
        emph_deadline = 0.0
        shake_deadline = 0.0
        pause_deadline = 0.0
        # sparkle overlay state
        sparkles = []
        sparkle_enabled = meta.get("sparkle", False)
        sparkle_rate = meta.get("sparkle_rate", 1.5)
        sparkle_chars = meta.get("sparkle_chars", ["*", "+", "."])
        if isinstance(sparkle_chars, str):
            sparkle_chars = list(sparkle_chars)
        sparkle_ttl = meta.get("sparkle_ttl", 0.6)
        sparkle_max = meta.get("sparkle_max", 30)
        sparkle_color = meta.get("sparkle_color", "label")
        sparkle_color_code = COLOR_MAP.get(sparkle_color, FG_LABEL)

        while True:
            # Real-time size monitoring: Wait until fixed instead of exiting
            current_size = shutil.get_terminal_size()
            if current_size.columns < 140 or current_size.lines < 30:
                # Force a full clear of the alternate buffer to prevent ghosting
                sys.stdout.write(f"{ESC}H{ESC}J")
                sys.stdout.write(f"{FG_TITLE}ERROR: Terminal too small!{RESET}\n")
                sys.stdout.write(f"Current: {current_size.columns}x{current_size.lines}\n")
                sys.stdout.write(f"Required: 140x30\n\n")
                sys.stdout.write("Please resize or maximize the window to continue...\n")
                sys.stdout.write("\033[91mPress [X] to Force Close Game\033[0m")
                sys.stdout.flush()
                
                # Check for exit input multiple times during the wait to improve responsiveness
                for _ in range(10):
                    if msvcrt.kbhit():
                        if msvcrt.getch().lower() == b'x':
                            return "EXIT_NOW"
                    time.sleep(0.05)
                continue

            # Update centering and handle layout shifts
            old_ox, old_oy = self.ox, self.oy
            self._update_layout_from_window()
            if self.ox != old_ox or self.oy != old_oy:
                sys.stdout.write(f"{ESC}2J") # Clear ghosting on move/resize
            
            left = self.ox + 2
            top = self.oy + 2

            now = time.perf_counter()
            dt = now - last_time
            last_time = now

            # bounds check
            if self.dialogue_index >= len(dialogues):
                return self.next_state

            current = dialogues[self.dialogue_index]
            speaker = current.get("speaker", "")
            text = current.get("text", "")

            # per-line overrides
            line_speed = current.get("speed", text_speed_default)
            pause_after = current.get("pause_after", 0.0) or 0.0
            emphasis = bool(current.get("emphasis", False))
            emph_duration = current.get("emphasis_duration", 0.6)
            shake = bool(current.get("shake", False))
            shake_amp = int(current.get("shake_amp", shift_amp_default))
            color_name = current.get("color")
            line_color = COLOR_MAP.get(color_name, FG_WHITE)

            pages = self._paginate(text, dialog_width, max_dialogue_lines)
            if self.page_index >= len(pages):
                self.page_index = 0

            page_text = pages[self.page_index]

            # reset per-line state if switched page/dialogue
            key = (self.dialogue_index, self.page_index)
            if key != current_line_key:
                current_line_key = key
                emph_deadline = 0.0
                shake_deadline = 0.0
                pause_deadline = 0.0
                self.char_index = 0
                reveal_acc = 0.0

            # timed typing using line_speed
            reveal_acc += dt
            if self.char_index < len(page_text):
                to_reveal = int(reveal_acc / line_speed)
                if to_reveal > 0:
                    self.char_index = min(len(page_text), self.char_index + to_reveal)
                    reveal_acc -= to_reveal * line_speed

            # if fully revealed, set emphasis/shake/pause deadlines if present
            if self.char_index >= len(page_text):
                if emphasis and emph_deadline == 0.0:
                    emph_deadline = now + emph_duration
                if shake and shake_deadline == 0.0:
                    shake_deadline = now + (emph_duration if emph_duration > 0 else 0.6)
                # schedule auto-advance if pause_after provided
                if pause_after and pause_deadline == 0.0:
                    pause_deadline = now + pause_after

            # build frame buffer
            buffer = self.window.draw_frame(self.title)

            # --- Render Background (manual frame sequence, no drift) ---
            if bg_frames and isinstance(bg_frames, (list, tuple)) and len(bg_frames) > 0:
                frame_idx = int(now * frame_rate) % len(bg_frames)
                bg = bg_frames[frame_idx]
            else:
                bg = bg_static

            bg_lines = self._normalize_ascii_lines(bg)
            # Background area limited to 18 lines to leave space for dialogue area
            max_bg_lines = min(18, max(0, self.window.height - (max_dialogue_lines + 6)))
            # Center background as a block so all frame lines stay aligned.
            bg_start_y = top + 1
            visible_bg_lines = bg_lines[:max_bg_lines]
            bg_block_width = max((len(line) for line in visible_bg_lines), default=0)
            bg_block_x = left + max(0, (content_width - bg_block_width) // 2)
            for i, line in enumerate(visible_bg_lines):
                draw_y = bg_start_y + i
                padded = line + (" " * max(0, bg_block_width - len(line)))
                buffer += f"{ESC}{draw_y};{bg_block_x}H{FG_BORDER}{padded}"

            # Sparkle overlay: spawn & render
            if sparkle_enabled and visible_bg_lines:
                # spawn new sparkles probabilistically (rate per second)
                # we may spawn multiple per frame depending on rate*dt
                spawn_prob = sparkle_rate * dt
                while random.random() < spawn_prob and len(sparkles) < sparkle_max:
                    li = random.randrange(len(visible_bg_lines))
                    row = bg_start_y + li
                    padded_line = visible_bg_lines[li] + (" " * max(0, bg_block_width - len(visible_bg_lines[li])))
                    empty_cols = [idx for idx, ch in enumerate(padded_line) if ch == " "]
                    if not empty_cols:
                        continue
                    col = bg_block_x + random.choice(empty_cols)
                    ch = random.choice(sparkle_chars)
                    sparkles.append({"row": row, "col": col, "char": ch, "ttl": sparkle_ttl})

                # render sparkles (over background, behind dialogue)
                for s in sparkles:
                    buffer += f"{ESC}{s['row']};{s['col']}H{sparkle_color_code}{s['char']}"

                # update TTLs
                for s in list(sparkles):
                    s['ttl'] -= dt
                    if s['ttl'] <= 0:
                        try:
                            sparkles.remove(s)
                        except ValueError:
                            pass

            # --- Conditional Kogane Render ---
            # Only if speaker is Kogane or dialogue mentions Kogane
            current_dialogue = dialogues[self.dialogue_index] if self.dialogue_index < len(dialogues) else {}
            speaker_lower = current_dialogue.get("speaker", "").lower()
            text_lower = current_dialogue.get("text", "").lower()

            if "kogane" in speaker_lower or "ding-dong" in text_lower or "ding dong" in text_lower:
                 k_y = self.oy + 16 # Positioned just above the dialogue divider
                 k_x = self.ox + 2  # Fixed left anchor
                 for i, kline in enumerate(KOGANE_SMALL):
                     # Use the kline as is, we've updated the constants to have correct leading spaces
                     buffer += f"{ESC}{k_y + i};{k_x}H{FG_TITLE}{kline}"

            # --- Dialogue Box Area ---
            sep_y = self.oy + self.window.height - (max_dialogue_lines + 3)
            buffer += f"{ESC}{sep_y};{left}H{FG_BORDER}" + ("-" * (self.window.width - 4))

            visible = page_text[:self.char_index]
            visible_lines = visible.split("\n")

            # speaker
            buffer += f"{ESC}{sep_y + 1};{left}H{FG_LABEL}[{speaker}]"

            # dialogue lines (paged) — apply emphasis coloring if active
            for i in range(max_dialogue_lines):
                line_y = sep_y + 2 + i
                text_line = visible_lines[i] if i < len(visible_lines) else ""
                padded = text_line + (" " * max(0, dialog_width - len(text_line)))

                # choose color: if emphasis active, blink between white and title color
                if now < emph_deadline:
                    # simple blink based on time
                    if int(now * 6) % 2 == 0:
                        color = COLOR_MAP.get("title", FG_TITLE)
                    else:
                        color = line_color
                else:
                    color = line_color

                # apply shake to dialogue left when shaking
                left_display = left
                if now < shake_deadline:
                    left_display = max(1, left + random.randint(-shake_amp, shake_amp))

                buffer += f"{ESC}{line_y};{left_display}H{color}{padded}"

            # hint
            hint = "[ENTER/→/SPACE] Next  [ESC] Exit"
            buffer += f"{ESC}{sep_y + max_dialogue_lines + 2};{left}H{FG_DIM}{hint}"

            buffer += f"{RESET}{ESC}{self.window.offset_y + self.window.height + 1};0H"
            print(buffer, end="", flush=True)

            # Auto-advance when pause_after elapsed (non-blocking)
            if self.char_index >= len(page_text) and pause_deadline and now >= pause_deadline:
                # behave like user pressed Next
                if self.page_index + 1 < len(pages):
                    self.page_index += 1
                    self.char_index = 0
                    reveal_acc = 0.0
                    # reset deadlines for the new page
                    current_line_key = (self.dialogue_index, self.page_index)
                    pause_deadline = 0.0
                    emph_deadline = 0.0
                    shake_deadline = 0.0
                    continue
                else:
                    self.dialogue_index += 1
                    self.page_index = 0
                    self.char_index = 0
                    reveal_acc = 0.0
                    current_line_key = (self.dialogue_index, self.page_index)
                    pause_deadline = 0.0
                    emph_deadline = 0.0
                    shake_deadline = 0.0
                    continue

            # Non-blocking key handling
            key = get_keypress_nb()
            if key is None:
                time.sleep(0.02)
                continue

            if key == "ESC":
                esc_result = self.handle_key(key)
                if esc_result:
                    return esc_result
                return "EXIT"

            # Next (ENTER / RIGHT / SPACE)
            if key in ("ENTER", "RIGHT", " "):
                if self.char_index < len(page_text):
                    # finish revealing current page immediately
                    self.char_index = len(page_text)
                    reveal_acc = 0.0
                    continue
                else:
                    # advance page or dialogue
                    if self.page_index + 1 < len(pages):
                        self.page_index += 1
                        self.char_index = 0
                        reveal_acc = 0.0
                        continue
                    else:
                        self.dialogue_index += 1
                        self.page_index = 0
                        self.char_index = 0
                        reveal_acc = 0.0
                        continue

            # Standalone helpers and second constructor were removed to keep the class
            # consistent and avoid accidental overrides.
