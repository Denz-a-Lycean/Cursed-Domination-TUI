import os
import sys
import time
import math
import random
import shutil
import ctypes

# USE THIS CLASS TO FIX THE DOMAIN ANIMATION 
# ONLY FOR REFERENCE NOT AS A MODULE
# COPY ITS ASCII ARTS AND USE IT FOR THE DOMAIN ATTACKING ANIMATION

# ============================================================
# WINDOWS ANSI ENABLE
# ============================================================

kernel32 = ctypes.windll.kernel32
handle = kernel32.GetStdHandle(-11)
mode = ctypes.c_ulong()
kernel32.GetConsoleMode(handle, ctypes.byref(mode))
kernel32.SetConsoleMode(handle, mode.value | 0x0004)

# ============================================================
# COLORS
# ============================================================

RESET = "\033[0m"
BOLD = "\033[1m"

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"

DIM = "\033[2m"

# ============================================================
# TERMINAL HELPERS
# ============================================================


def clear():
    os.system("cls")



def move(x, y):
    return f"\033[{y};{x}H"



def hide_cursor():
    print("\033[?25l", end="")



def show_cursor():
    print("\033[?25h", end="")



def terminal_size():
    return shutil.get_terminal_size((120, 40))



def center_x(text, width):
    return max(1, (width // 2) - (len(text) // 2))


# ============================================================
# UI DRAWING
# ============================================================


def draw_box(buffer, x, y, w, h, color=WHITE):
    top = "╔" + ("═" * (w - 2)) + "╗"
    mid = "║" + (" " * (w - 2)) + "║"
    bot = "╚" + ("═" * (w - 2)) + "╝"

    buffer.append(move(x, y) + color + top)

    for i in range(1, h - 1):
        buffer.append(move(x, y + i) + color + mid)

    buffer.append(move(x, y + h - 1) + color + bot)



def progress_bar(value, max_value, width, color):
    ratio = max(0.0, min(1.0, value / max_value))
    filled = int(ratio * width)

    return (
        color
        + "█" * filled
        + DIM
        + "░" * (width - filled)
        + RESET
    )


# ============================================================
# DOMAIN VISUAL EFFECT
# ============================================================

DOMAIN_TEXT = [
    "██████╗  ██████╗ ███╗   ███╗ █████╗ ██╗███╗   ██╗",
    "██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██║████╗  ██║",
    "██║  ██║██║   ██║██╔████╔██║███████║██║██╔██╗ ██║",
    "██║  ██║██║   ██║██║╚██╔╝██║██╔══██║██║██║╚██╗██║",
    "██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║██║██║ ╚████║",
    "╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝",
]


# ============================================================
# PARTICLES
# ============================================================


class Particle:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.reset()

    def reset(self):
        x_min = 3
        x_max = max(x_min, self.width - 3)
        y_min = 3
        y_max = max(y_min, self.height - 3)

        self.x = random.randint(x_min, x_max)
        self.y = random.randint(y_min, y_max)
        self.dx = random.choice([-1, 1])
        self.dy = random.choice([-1, 1])
        self.char = random.choice(["·", "•", "*", "+"])
        self.life = random.randint(20, 80)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1

        if self.life <= 0:
            self.reset()


# ============================================================
# MAIN RENDER
# ============================================================


def render_frame(elapsed, total_time, attack, defend, particles):
    width, height = terminal_size()

    pulse = (math.sin(elapsed * 3) + 1) / 2

    domain_color = MAGENTA if pulse > 0.5 else CYAN

    # use float-safe timer and show tenths of a second
    timer_left = max(0.0, total_time - elapsed)

    mins = int(timer_left // 60)
    secs_float = timer_left % 60.0

    timer_str = f"{mins:02}:{secs_float:04.1f}"

    buffer = []

    # ========================================================
    # BACKGROUND ENERGY WAVES
    # ========================================================

    for row in range(1, height):
        wave_x = int((math.sin((elapsed * 2) + row * 0.2) * 8) + (width // 2))

        if 1 < wave_x < width:
            buffer.append(move(wave_x, row) + DIM + MAGENTA + "│")

    # ========================================================
    # MAIN PANEL
    # ========================================================

    panel_w = 92
    panel_h = 26

    panel_x = (width - panel_w) // 2
    panel_y = (height - panel_h) // 2

    draw_box(buffer, panel_x, panel_y, panel_w, panel_h, CYAN)

    # ========================================================
    # DOMAIN TITLE
    # ========================================================

    start_y = panel_y + 2

    for i, line in enumerate(DOMAIN_TEXT):
        x = center_x(line, width)
        buffer.append(move(x, start_y + i) + BOLD + domain_color + line)

    # ========================================================
    # TIMER
    # ========================================================

    timer_y = start_y + 9

    timer_display = f"[ DOMAIN TIMER : {timer_str} ]"

    tx = center_x(timer_display, width)

    buffer.append(
        move(tx, timer_y)
        + BOLD
        + YELLOW
        + timer_display
    )

    # ========================================================
    # STATUS BARS
    # ========================================================

    bar_width = 48

    attack_bar = progress_bar(attack, 100, bar_width, RED)
    defend_bar = progress_bar(defend, 100, bar_width, GREEN)

    left = panel_x + 6

    buffer.append(
        move(left, timer_y + 4)
        + BOLD
        + RED
        + "ATTACK ENERGY"
    )

    buffer.append(
        move(left, timer_y + 5)
        + attack_bar
    )

    buffer.append(
        move(left, timer_y + 8)
        + BOLD
        + GREEN
        + "DEFENSE STABILITY"
    )

    buffer.append(
        move(left, timer_y + 9)
        + defend_bar
    )

    # ========================================================
    # DOMAIN STATUS
    # ========================================================

    phase = "STABLE"
    phase_color = GREEN

    if timer_left < 20:
        phase = "COLLAPSING"
        phase_color = RED
    elif timer_left < 40:
        phase = "UNSTABLE"
        phase_color = YELLOW

    status_text = f"DOMAIN STATUS : {phase}"

    sx = center_x(status_text, width)

    buffer.append(
        move(sx, panel_y + panel_h - 4)
        + BOLD
        + phase_color
        + status_text
    )

    # ========================================================
    # PARTICLES
    # ========================================================

    for p in particles:
        p.update()

        if 0 < p.x < width and 0 < p.y < height:
            color = random.choice([MAGENTA, CYAN, BLUE])
            buffer.append(move(p.x, p.y) + color + p.char)

    # ========================================================
    # FOOTER
    # ========================================================

    footer = "BUILT-IN PYTHON ONLY  |  WINDOWS TERMINAL"

    fx = center_x(footer, width)

    buffer.append(
        move(fx, height - 2)
        + DIM
        + WHITE
        + footer
    )

    # ========================================================
    # FINAL DRAW
    # ========================================================

    print("\033[H", end="")
    print("".join(buffer), end="", flush=True)


# ============================================================
# MAIN LOOP
# ============================================================


def main():
    clear()
    hide_cursor()

    total_time = 90

    # use a monotonic clock for robust elapsed timing
    start = time.monotonic()

    # initialize particles to current terminal size
    width, height = terminal_size()
    particles = [Particle(width, height) for _ in range(80)]

    try:
        while True:
            elapsed = time.monotonic() - start

            if elapsed >= total_time:
                break

            attack = 50 + (math.sin(elapsed * 1.5) * 50)
            defend = 50 + (math.cos(elapsed * 1.1) * 50)

            render_frame(elapsed, total_time, attack, defend, particles)

            time.sleep(1 / 30)

        clear()

        width, height = terminal_size()

        end_text = "DOMAIN COLLAPSED"

        x = center_x(end_text, width)
        y = height // 2

        print(move(x, y) + BOLD + RED + end_text)

        print(RESET)

    finally:
        show_cursor()


if __name__ == "__main__":
    main()
