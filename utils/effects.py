"""Terminal rendering, ANSI styling, and instability glitch visual effects."""

import ctypes
import os
import re
import shutil
import sys
import time
from utils.randomizer import choice, randint, seeded_random


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"
    WHITE = "\033[37m"
    DIM = "\033[2m"
    BLINK = "\033[5m"
    UNDERLINE = "\033[4m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_YELLOW = "\033[93m"
    BG_RED = "\033[41m"
    BG_BLACK = "\033[40m"


ANSI_PATTERN = re.compile(r"(\033\[[0-9;]*m)")

# ── Expanded symbol pool for cursed chaos ────────────────────────────────────
GLITCH_SYMBOLS   = "@#$%&!?/\\|_+-=*"
CURSED_SYMBOLS   = "@#!@#$!$(*(*^#*&#$)#$_!|||~||~||~<>{}[]^`~"
CHAOS_SYMBOLS    = "░▒▓█▀▄■□▪▫◆◇○●◎★☆※†‡§¶"          # block/box chars
SCREAM_SYMBOLS   = "!?!?!?!!!???!?!?!!??!"

# These globals keep the current visual instability state synchronized across
# all rendering helpers without forcing every function to pass around a state
# object. For this CLI project, that tradeoff keeps the UI code simpler.
_glitch_level = 0
_glitch_frame = 0
_collapse_choices_remaining = None


# ── Color palette that cycles on high instability ────────────────────────────
_INSTABILITY_COLORS = [
    Colors.RED,
    Colors.BRIGHT_RED,
    Colors.MAGENTA,
    Colors.BRIGHT_MAGENTA,
    Colors.YELLOW,
    Colors.BRIGHT_YELLOW,
    Colors.CYAN,
    Colors.WHITE,
]


def enable_virtual_terminal():
    """
    Enable ANSI color support on Windows terminals when available.
    """
    if os.name != "nt":
        return
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)
    mode = ctypes.c_uint32()
    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)


def clear_screen():
    # Prefer ANSI cursor control over `os.system("cls")` so redraws happen
    # smoothly and immediately (especially during timed animations).
    import sys
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def color_text(text, color):
    return f"{color}{text}{Colors.RESET}"


def set_glitch_level(instability):
    """
    Keep display instability in sync with the player's mental state.
    """
    global _glitch_level, _glitch_frame, _collapse_choices_remaining
    _glitch_level = max(0, min(5, int(instability)))
    _glitch_frame = 0
    _collapse_choices_remaining = randint(1, 2) if _glitch_level >= 5 else None


def glitch_level():
    return _glitch_level


def consume_collapse_choice():
    """
    At max instability, allow only a couple of menu choices before forced collapse.
    """
    global _collapse_choices_remaining
    if _collapse_choices_remaining is None:
        return False
    _collapse_choices_remaining -= 1
    return _collapse_choices_remaining <= 0


def advance_glitch_frame():
    """
    Move the animated glitch state forward for live menu flicker.
    """
    global _glitch_frame
    _glitch_frame += 1


def format_duration(total_seconds):
    total_seconds = max(0, int(total_seconds))
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def _line(width, char="="):
    return char * max(20, width)


def _terminal_width():
    return shutil.get_terminal_size((80, 24)).columns


def _split_ansi(text):
    return ANSI_PATTERN.split(str(text))


def _glitch_char(char, rng=None, use_chaos=False):
    """
    Replace a character with a random symbol.
    At high instability, pull from the wider cursed/chaos pools.
    """
    pool = CURSED_SYMBOLS if use_chaos else GLITCH_SYMBOLS
    if rng:
        return rng.choice(pool)
    return choice(pool)


# ── NEW: inject a burst of noise characters between words ────────────────────
def _inject_noise_burst(text, rng, intensity=0.0):
    """
    Randomly insert short bursts of cursed symbols between word boundaries.
    Only fires at instability 3+.
    """
    if intensity < 0.05:
        return text
    words = text.split(" ")
    out = []
    for word in words:
        out.append(word)
        if rng.random() < intensity:
            burst_len = rng.randint(2, 6)
            burst = "".join(rng.choice(CURSED_SYMBOLS) for _ in range(burst_len))
            out.append(burst)
    return " ".join(out)


# ── NEW: simulate "shaking" by randomly shifting indent each render ──────────
def _shake_line(text, rng, shake_amount=0):
    """
    Add a random leading-space offset to simulate the line trembling.
    shake_amount controls max characters of horizontal drift.
    """
    if shake_amount <= 0:
        return text
    drift = " " * rng.randint(0, shake_amount)
    return drift + text


# ── NEW: randomly colorize individual words in a line ───────────────────────
def _colorize_chaos(text, rng, probability=0.0):
    """
    Wrap random words in a cycling instability color.
    """
    if probability <= 0:
        return text
    words = text.split(" ")
    out = []
    for word in words:
        if word and rng.random() < probability:
            color = rng.choice(_INSTABILITY_COLORS)
            out.append(f"{color}{word}{Colors.RESET}")
        else:
            out.append(word)
    return " ".join(out)


def _glitch_profile():
    profiles = {
        0: {
            "title": 0.0,   "status": 0.0,  "body": 0.0,   "footer": 0.0,
            "swap": 0.0,    "repeat": 0.0,  "noise": 0.0,  "shake": 0,
            "color_chaos": 0.0, "use_chaos_chars": False,
        },
        1: {
            "title": 0.004, "status": 0.0,  "body": 0.006, "footer": 0.004,
            "swap": 0.35,   "repeat": 0.0,  "noise": 0.0,  "shake": 0,
            "color_chaos": 0.0, "use_chaos_chars": False,
        },
        2: {
            "title": 0.008, "status": 0.002,"body": 0.012, "footer": 0.008,
            "swap": 0.5,    "repeat": 0.02, "noise": 0.0,  "shake": 0,
            "color_chaos": 0.0, "use_chaos_chars": False,
        },
        3: {
            "title": 0.05,  "status": 0.01, "body": 0.06,  "footer": 0.04,
            "swap": 0.24,   "repeat": 0.05, "noise": 0.08, "shake": 2,
            "color_chaos": 0.08, "use_chaos_chars": True,
        },
        4: {
            "title": 0.09,  "status": 0.02, "body": 0.13,  "footer": 0.08,
            "swap": 0.28,   "repeat": 0.10, "noise": 0.18, "shake": 4,
            "color_chaos": 0.20, "use_chaos_chars": True,
        },
        5: {
            "title": 0.18,  "status": 0.05, "body": 0.28,  "footer": 0.16,
            "swap": 0.30,   "repeat": 0.18, "noise": 0.35, "shake": 6,
            "color_chaos": 0.40, "use_chaos_chars": True,
        },
    }
    return profiles[_glitch_level]


def _glitch_text(text, intensity="body"):
    if _glitch_level <= 0:
        return str(text)

    profile = _glitch_profile()
    odds = profile.get(intensity, profile["body"])
    use_chaos = profile["use_chaos_chars"]
    rng = seeded_random((hash(str(text)) ^ (_glitch_frame * 131)) + (_glitch_level * 997))

    # ── 1. Character-level corruption ────────────────────────────────────────
    tokens = _split_ansi(text)
    glitched = []

    for token in tokens:
        if ANSI_PATTERN.fullmatch(token):
            glitched.append(token)
            continue

        chars = list(token)
        for index, char in enumerate(chars):
            if char.isspace():
                continue
            if intensity == "status" and index < 4:
                continue

            if rng.random() < odds:
                roll = rng.random()
                swap_thresh = 1.0 - profile["swap"] - profile["repeat"]
                repeat_thresh = 1.0 - profile["repeat"]

                if roll < swap_thresh:
                    # Replace with a glitch/chaos character
                    chars[index] = _glitch_char(char, rng, use_chaos=use_chaos)
                elif roll < repeat_thresh and index + 1 < len(chars) and not chars[index + 1].isspace():
                    chars[index], chars[index + 1] = chars[index + 1], chars[index]
                else:
                    # Repeat (stutter) the character
                    repeat_count = rng.randint(2, 4) if _glitch_level >= 4 else 2
                    chars[index] = char * repeat_count if intensity != "status" else char

        glitched.append("".join(chars))

    result = "".join(glitched)

    # ── 2. Noise burst injection (level 3+) ───────────────────────────────
    result = _inject_noise_burst(result, rng, intensity=profile["noise"])

    # ── 3. Random word colorization (level 3+) ────────────────────────────
    result = _colorize_chaos(result, rng, probability=profile["color_chaos"])

    # ── 4. Line shake / drift (level 3+) ─────────────────────────────────
    if intensity not in ("status",):
        result = _shake_line(result, rng, shake_amount=profile["shake"])

    return result


def glitch_text(text, intensity="body"):
    return _glitch_text(text, intensity)


def render_screen(title, lines=None, status_lines=None, footer=None, disable_glitch=False):
    """
    Render a full terminal screen with a header, body, and status section.
    At high instability the border chars also cycle and the title flickers.
    """
    clear_screen()
    width = _terminal_width()

    # Cursed border: at level 4-5 the separator char itself becomes unstable.
    # Menus can opt out of this behavior so input choices remain stable.
    if (not disable_glitch) and _glitch_level >= 4:
        rng = seeded_random(_glitch_frame * 77 + _glitch_level)
        border_char = rng.choice(["=", "#", "%", "~", "|", "*"])
    else:
        border_char = "="

    separator = color_text(_line(width, border_char), Colors.MAGENTA if _glitch_level < 4 else Colors.BRIGHT_RED)

    print(separator, flush=True)
    title_text = title.center(width) if disable_glitch else _glitch_text(title.center(width), "title")
    print(color_text(title_text, Colors.BOLD + Colors.CYAN), flush=True)
    print(separator, flush=True)
    print(flush=True)

    if status_lines:
        label = " STATUS " if _glitch_level < 5 else " STATUS ? "
        label_border = _line(min(width, max(20, len(label) + 4)), "-")
        print(color_text(label.center(min(width, len(label_border))), Colors.BRIGHT_YELLOW), flush=True)
        print(color_text(label_border, Colors.DIM), flush=True)
        for line in status_lines:
            print(color_text(f"  {line}", Colors.YELLOW), flush=True)
        print(color_text(label_border, Colors.DIM), flush=True)
        print(flush=True)

    if lines:
        for line in lines:
            if line is None:
                print(flush=True)
                continue
            formatted_line = str(line) if disable_glitch else _glitch_text(line, "body")
            print(f"  {formatted_line}", flush=True)

    if footer:
        print(flush=True)
        footer_text = str(footer) if disable_glitch else _glitch_text(footer, "footer")
        print(color_text(footer_text, Colors.DIM + Colors.WHITE), flush=True)

    advance_glitch_frame()
    # Ensure the terminal repaints instantly during fast animations.
    import sys
    sys.stdout.flush()


def loading_transition(title, message, status_lines=None, seconds=1.8, interval=0.35):
    """
    Show a readable loading state. At high instability the loading dots
    glitch and the message itself flickers between renders.
    """
    effective_seconds = max(0.8, seconds * 0.75)
    effective_interval = max(0.18, interval * 0.9)

    render_screen(
        title=title,
        lines=[color_text(message, Colors.CYAN), None, "Loading"],
        status_lines=status_lines,
        footer="Please wait...",
    )

    start_time = time.monotonic()
    dot_count = 0
    while time.monotonic() - start_time < effective_seconds:
        dots = "." * ((dot_count % 3) + 1)
        loading_text = f"Loading{dots}"

        # At high instability, the loading line itself can glitch
        if _glitch_level >= 3:
            rng = seeded_random(dot_count * 53 + _glitch_level)
            if rng.random() < 0.25:
                noise = "".join(rng.choice(CURSED_SYMBOLS) for _ in range(rng.randint(2, 5)))
                sys.stdout.write(f"\r{noise} {loading_text} {noise}   ")
                sys.stdout.flush()
                try:
                    time.sleep(effective_interval)
                except KeyboardInterrupt:
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    return
                dot_count += 1
                continue

        sys.stdout.write(f"\r{loading_text.ljust(18)}")
        sys.stdout.flush()
        try:
            time.sleep(effective_interval)
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            sys.stdout.flush()
            return
        dot_count += 1

    sys.stdout.write("\rLoading... done\n")
    sys.stdout.flush()


def _build_progress_bar(progress, width=24, fill_char="#", empty_char="-"):
    """Return a fixed-width progress bar string."""
    clamped = max(0.0, min(1.0, float(progress)))
    filled = int(round(clamped * width))
    empty = max(0, width - filled)
    return f"[{fill_char * filled}{empty_char * empty}] {int(clamped * 100):3d}%"


def attack_transition(
    title,
    attacker_name,
    defender_name,
    attack_name,
    defender_defending=False,
    indicator_label=None,
    status_lines=None,
    seconds=1.1,
    shake=False,
):
    """
    Show a short attack animation with indicator and progress bar.

    When `shake` is True, the body lines jitter horizontally to emphasize impact.
    """
    effective_seconds = max(0.6, float(seconds))
    frame_delay = 0.09
    frame_total = max(6, int(effective_seconds / frame_delay))
    markers = [">", ">>", ">>>", ">>>>", ">>>>>", ">>>>>>"]

    def _resolve_status_lines():
        return status_lines() if callable(status_lines) else status_lines

    attack_label = str(attack_name)
    if len(attack_label) > 18:
        attack_label = attack_label[:18] + "..."

    for frame in range(frame_total):
        progress = (frame + 1) / frame_total
        marker = markers[frame % len(markers)]
        stance_label = (
            str(indicator_label).upper()
            if indicator_label is not None
            else ("DEFENDING" if defender_defending else "ATTACKING")
        )
        indicator = color_text(f"{marker} {stance_label}", Colors.BRIGHT_YELLOW)
        progress_line = _build_progress_bar(progress, width=26, fill_char="#", empty_char="-")
        spark_count = (frame % 4) + 1
        impact = "*" * spark_count

        lines = [
            f"{attacker_name} uses {attack_label}!",
            f"Target: {defender_name}",
            "",
            indicator,
            f"Impact: {impact}",
            progress_line,
        ]

        if shake:
            rng = seeded_random((frame + 1) * 97 + len(attack_name))
            shaken = []
            # Shake only the impact/progress area to keep the header readable.
            shake_indices = {3, 4, 5}
            for idx, line in enumerate(lines):
                if not line:
                    shaken.append(line)
                    continue
                if idx in shake_indices:
                    offset = " " * rng.randint(0, 2)
                    shaken.append(f"{offset}{line}")
                else:
                    shaken.append(line)
            lines = shaken

        render_screen(
            title=title,
            lines=lines,
            status_lines=_resolve_status_lines(),
            footer="Resolving attack...",
        )
        # Extra flush for Windows terminals that buffer redraws.
        import sys
        sys.stdout.flush()
        try:
            time.sleep(frame_delay)
        except KeyboardInterrupt:
            break


def domain_expansion_transition(
    title,
    attacker_name,
    defender_name,
    domain_name,
    technique_key,
    status_lines=None,
    duration_seconds=30.0,
    interval=0.25,
):
    """
    Animate domain expansion with a countdown progress bar.

    technique_key: "Dancer" | "Bouncer" | "Seeker"
    """
    duration_seconds = max(1.0, float(duration_seconds))
    interval = max(0.05, float(interval))

    presets = {
        "Dancer": {
            "label": "TRAP: Death Dancing Arena",
            "glyphs": ["░", "▒", "▓", "█"],
        },
        "Bouncer": {
            "label": "SILENCE: Silent Rebound Palace",
            "glyphs": [".", "·", "•", "‧"],
        },
        "Seeker": {
            "label": "EYE: Eye of Padullon",
            "glyphs": ["^", ">", "<", "*"],
        },
    }
    preset = presets.get(technique_key, presets["Seeker"])

    start = time.monotonic()
    frame = 0
    while True:
        def _resolve_status_lines():
            return status_lines() if callable(status_lines) else status_lines

        elapsed = time.monotonic() - start
        remaining = max(0.0, duration_seconds - elapsed)
        progress = 1.0 - (remaining / duration_seconds)
        pct = int(progress * 100)

        glyph = preset["glyphs"][frame % len(preset["glyphs"])]
        if technique_key == "Dancer":
            arena = f"{glyph * 10} D.D.A {glyph * 10}"
            mid_a = arena
            mid_b = f"Draining cursed energy... ({pct}%)"
        elif technique_key == "Bouncer":
            silence = f"{glyph * 26} SILENCE {glyph * 26}"
            mid_a = silence
            mid_b = "No footsteps. No breath. No sound."
        else:  # Seeker
            copies = f"{glyph} {glyph} {glyph}  {glyph} {glyph} {glyph}  {glyph} {glyph}"
            mid_a = copies
            mid_b = "Multiple copies attack from all directions."

        lines = [
            color_text("DOMAIN EXPANSION!!!", Colors.BRIGHT_RED + Colors.BOLD),
            domain_name,
            "",
            preset["label"],
            f"Inside the domain: {attacker_name} vs {defender_name}",
            "",
            mid_a,
            mid_b,
            "",
            _build_progress_bar(progress, width=34, fill_char="=", empty_char=" "),
            f"DOMAIN TIME: {remaining:04.1f}s",
        ]

        render_screen(
            title=title,
            lines=lines,
            status_lines=_resolve_status_lines(),
            footer="Domain active. Enemy turn after timer ends.",
        )
        # Extra flush for redraw reliability.
        import sys
        sys.stdout.flush()

        frame += 1
        if remaining <= 0:
            break

        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            break


def domain_activation_transition(
    title,
    attacker_name,
    defender_name,
    domain_name,
    technique_key,
    status_lines=None,
    seconds=1.1,
    interval=0.09,
):
    """Short "DOMAIN EXPANSION!!!" flash before the action menu."""
    seconds = max(0.6, float(seconds))
    interval = max(0.05, float(interval))
    frame_total = max(6, int(seconds / interval))

    presets = {
        "Dancer": {"label": "Death Dancing Arena", "glyphs": ["░", "▒", "▓", "█"]},
        "Bouncer": {"label": "Silent Rebound Palace", "glyphs": [".", "·", "•", "‧"]},
        "Seeker": {"label": "Eye of Padullon", "glyphs": ["^", ">", "<", "*"]},
    }
    preset = presets.get(technique_key, presets["Seeker"])
    frame = 0

    def _resolve_status_lines():
        return status_lines() if callable(status_lines) else status_lines

    while frame < frame_total:
        glyph = preset["glyphs"][frame % len(preset["glyphs"])]
        if technique_key == "Dancer":
            mid = f"{glyph * 12} TRAP LOCK {glyph * 12}"
        elif technique_key == "Bouncer":
            mid = f"{glyph * 14} SOUND ERASED {glyph * 14}"
        else:
            mid = f"{glyph} COPIES  {glyph} {glyph}  {glyph} COPIES"

        lines = [
            color_text("DOMAIN EXPANSION!!!", Colors.BRIGHT_RED + Colors.BOLD),
            domain_name,
            "",
            f"{preset['label']}",
            f"{attacker_name} vs {defender_name}",
            "",
            mid,
            "",
            "Reality folds inward...",
        ]

        render_screen(
            title=title,
            lines=lines,
            status_lines=_resolve_status_lines(),
            footer="Choose Defend or Attack.",
        )

        frame += 1
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            break


def domain_attack_transition(
    title,
    attacker_name,
    defender_name,
    domain_name,
    technique_key,
    status_lines=None,
    seconds=1.2,
    shake=False,
):
    """Single domain hit animation."""
    label_map = {
        "Dancer": "TRAP SLAM",
        "Bouncer": "SOUNDLESS IMPACT",
        "Seeker": "EYE STRIKE",
    }
    domain_label = label_map.get(technique_key, "DOMAIN STRIKE")

    return attack_transition(
        title=title,
        attacker_name=attacker_name,
        defender_name=defender_name,
        attack_name=f"{domain_name}: {domain_label}",
        status_lines=status_lines,
        seconds=seconds,
        shake=shake,
    )


def render_menu(title, options, selected_index, status_lines=None, help_text=None):
    """
    Render an interactive menu.
    At level 5 the options are shuffled; at level 3-4 their labels also glitch.
    """
    display_options = list(options)
    if _glitch_level >= 5 and len(display_options) > 1:
        # The shuffled visual order is intentional: max instability should make
        # the interface feel unreliable while still remaining technically usable.
        rng = seeded_random((_glitch_frame * 257) + (len(display_options) * 17))
        rng.shuffle(display_options)

    lines = []
    number_width = len(str(len(display_options)))
    for index, option in enumerate(display_options):
        prefix = f"{index + 1:{number_width}d}."
        lines.append(color_text(f"  {prefix} {option}", Colors.WHITE))

    help_text = help_text or "Enter a number, then press Enter."

    render_screen(
        title=title,
        lines=lines,
        status_lines=status_lines,
        footer=help_text,
        disable_glitch=True,
    )


# ── Collapse screen (game over) ───────────────────────────────────────────────

def _collapse_corrupt_text(text, intensity="body", seed=None):
    """
    Maximum corruption used for the terminal-collapse game over screen.
    Now includes noise bursts, multi-color word painting, and heavy drift.
    """
    rng = seeded_random(seed if seed is not None else time.monotonic_ns())
    odds = {
        "title": 0.55,
        "body":  0.42,
        "footer": 0.28,
    }.get(intensity, 0.42)

    tokens = _split_ansi(text)
    glitched = []

    for token in tokens:
        if ANSI_PATTERN.fullmatch(token):
            glitched.append(token)
            continue

        chars = list(token)
        index = 0
        while index < len(chars):
            char = chars[index]
            if not char.isspace() and rng.random() < odds:
                roll = rng.random()
                if roll < 0.35:
                    # Replace with cursed/chaos char
                    chars[index] = rng.choice(CURSED_SYMBOLS)
                elif roll < 0.55:
                    # Replace with block/box art char for eerie look
                    chars[index] = rng.choice(CHAOS_SYMBOLS)
                elif roll < 0.72 and index + 1 < len(chars) and not chars[index + 1].isspace():
                    chars[index], chars[index + 1] = chars[index + 1], chars[index]
                elif roll < 0.88:
                    # Stutter repeat
                    chars[index] = char * rng.randint(2, 4)
                else:
                    # Scream punctuation insert
                    chars[index] = rng.choice(SCREAM_SYMBOLS)
            index += 1

        line = "".join(chars)

        # Noise burst injection
        line = _inject_noise_burst(line, rng, intensity=0.45)

        # Random word colorization — very aggressive on collapse
        line = _colorize_chaos(line, rng, probability=0.55)

        # Heavy drift
        if intensity != "footer":
            drift = " " * rng.randint(0, 14)
            line = f"{drift}{line}"

        glitched.append(line)

    return "".join(glitched)


def render_collapse_screen(title, lines=None, footer=None, flashes=6, delay=0.08):
    """
    Dedicated unstable game-over presentation for total mental collapse.
    Each flash redraws with fresh random corruption so it looks alive.
    """
    width = _terminal_width()
    body_lines = list(lines or [])
    border_chars = ["=", "#", "%", "~", "!", "|", "*", "@"]

    for flash_index in range(max(1, flashes)):
        clear_screen()

        seed = time.monotonic_ns() + flash_index * 9973

        # Chaotic top border — character changes every flash
        rng_b = seeded_random(seed)
        bc = rng_b.choice(border_chars)
        print(color_text(_line(width, bc), Colors.BRIGHT_RED), flush=True)

        # Corrupted title — colors cycle flash by flash
        title_color = _INSTABILITY_COLORS[flash_index % len(_INSTABILITY_COLORS)]
        corrupted_title = _collapse_corrupt_text(title.center(width), "title", seed=seed)
        print(color_text(corrupted_title, Colors.BOLD + title_color), flush=True)

        # Second separator with a different char
        bc2 = rng_b.choice(border_chars)
        print(color_text(_line(width, bc2), Colors.MAGENTA), flush=True)
        print(flush=True)

        for line in body_lines:
            print(_collapse_corrupt_text(line, "body", seed=seed + randint(1, 9999)), flush=True)

        if footer:
            print(flush=True)
            print(color_text(_collapse_corrupt_text(footer, "footer", seed=seed), Colors.DIM + Colors.WHITE), flush=True)

        time.sleep(delay)
