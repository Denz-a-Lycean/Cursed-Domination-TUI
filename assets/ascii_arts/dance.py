import os
import sys
import time
import math
import random

# --- ANSI Constants ---
ESC = "\033["
RESET = f"{ESC}0m"
FG_RED = f"{ESC}31m"
FG_PURPLE = f"{ESC}35m"
FG_DIM = f"{ESC}38;5;240m"
FG_GOLD = f"{ESC}38;5;220m"
CLEAR = f"{ESC}2J"
HOME = f"{ESC}H"
HIDE_CURSOR = f"{ESC}?25l"
SHOW_CURSOR = f"{ESC}?25h"

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.8, -0.2)
        self.char = random.choice(["*", ".", "o"])
        self.life = 1.0

    def move(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 0.05

def draw_dancer(cx, cy, frame):
    """Draws a rhythmic dancing silhouette."""
    # 4-frame dance cycle using JC the Dancer ASCII
    dance_frames = [
        [
            r"   _O/      ",
            r"     \      ",
            r"     /\_    ",
            r"     \  `   ",
            r"     `      ",
            r"            "
        ],
        [
            r"            ",
            r"            ",
            r"            ",
            r"      ,     ",
            r"   O/ /     ",
            r"   /\|/\.   "
        ],
        [
            r"     ,      ",
            r"    /       ",
            r" `\_\       ",
            r"     \      ",
            r"    /O\     ",
            r"            "
        ],
        [
            r"            ",
            r"    \O_     ",
            r" ,/\/       ",
            r"   /        ",
            r"   \        ",
            r"            "
        ]
    ]
    f = dance_frames[frame % 4]
    for i, line in enumerate(f):
        # Adjusted cx offset to better center the wider JC art
        sys.stdout.write(f"{ESC}{cy + i};{cx - 6}H{FG_PURPLE}{line}")


def render_domain_frame(frame: int, width: int, height: int) -> list[str]:
    """Return a small dancer-frame overlay for domain animations.

    This is a non-blocking renderer used by the presenter. It returns
    ANSI-colored lines (no terminal cursor moves) which the presenter can
    overlay onto the battle UI.
    """
    dance_frames = [
        [
            r"   _O/      ",
            r"     \      ",
            r"     /\_    ",
            r"     \  `   ",
            r"     `      ",
            r"            ",
        ],
        [
            r"            ",
            r"            ",
            r"            ",
            r"      ,     ",
            r"   O/ /     ",
            r"   /\|/\.   ",
        ],
        [
            r"     ,      ",
            r"    /       ",
            r" `\_\       ",
            r"     \      ",
            r"    /O\     ",
            r"            ",
        ],
        [
            r"            ",
            r"    \O_     ",
            r" ,/\/       ",
            r"   /        ",
            r"   \        ",
            r"            ",
        ],
    ]

    frame_idx = int(frame) % len(dance_frames)
    chosen = dance_frames[frame_idx]
    # Return ANSI-colored lines; presenter will position/pad them.
    return [f"{FG_PURPLE}{ln}{RESET}" for ln in chosen]

def main():
    os.system("")
    cols, lines = os.get_terminal_size()
    cx, cy = cols // 2, lines // 2
    # Import msvcrt lazily so this module can be loaded on non-Windows hosts
    try:
        import msvcrt as _msv
        msvcrt = _msv
    except Exception:
        msvcrt = None

    particles = []
    start_time = time.time()
    
    sys.stdout.write(f"{HIDE_CURSOR}{CLEAR}")
    
    # Activation
    announcement = "DOMAIN EXPANSION: DEATH DANCING ARENA"
    sys.stdout.write(f"{ESC}{cy};{cx - len(announcement)//2}H{FG_RED}{announcement}")
    sys.stdout.flush()
    time.sleep(1.5)
    sys.stdout.write(CLEAR)

    try:
        frame_count = 0
        while True:
            if msvcrt and msvcrt.kbhit():
                if msvcrt.getch().lower() == b'q':
                    break

            sys.stdout.write(HOME)
            
            # Draw Arena Borders (Rhythmic pulsing)
            pulse = (math.sin(time.time() * 5) + 1) / 2
            border_color = f"{ESC}38;5;{int(50 + pulse * 100)}m"
            sys.stdout.write(f"{border_color}{'#' * cols}")
            sys.stdout.write(f"{ESC}{lines};1H{'#' * cols}")

            # Drain Particles (Rising from bottom)
            if len(particles) < 40:
                particles.append(Particle(random.randint(5, cols-5), lines-2))
            
            for p in particles[:]:
                p.move()
                if p.life <= 0:
                    particles.remove(p)
                else:
                    color = FG_GOLD if random.random() > 0.5 else FG_DIM
                    sys.stdout.write(f"{ESC}{int(p.y)};{int(p.x)}H{color}{p.char}")

            # Draw Central Dancer
            if frame_count % 5 == 0:
                draw_dancer(cx, cy - 2, frame_count // 5)

            # Energy Drain UI
            drain_percent = min(100, int((time.time() - start_time) * 5))
            sys.stdout.write(f"{ESC}{lines-2};{cx-15}H{FG_RED}CURSED ENERGY DRAINED: {drain_percent}%")
            
            sys.stdout.flush()
            frame_count += 1
            time.sleep(0.05)

    finally:
        sys.stdout.write(f"{SHOW_CURSOR}{RESET}{CLEAR}{HOME}")

if __name__ == "__main__":
    main()
