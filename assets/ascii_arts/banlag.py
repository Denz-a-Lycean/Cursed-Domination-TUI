import os
import sys
import time
import math
import random

# --- ANSI Constants ---
ESC = "\033["
RESET = f"{ESC}0m"
FG_CYAN = f"{ESC}36m"
FG_WHITE = f"{ESC}97m"
FG_DIM = f"{ESC}38;5;238m"
FG_BLUE = f"{ESC}34m"
CLEAR = f"{ESC}2J"
HOME = f"{ESC}H"
HIDE_CURSOR = f"{ESC}?25l"
SHOW_CURSOR = f"{ESC}?25h"

class Clone:
    def __init__(self, angle, distance, speed):
        self.angle = angle
        self.distance = distance
        self.speed = speed
        self.char = "G" # Gaudenz copy

    def update(self):
        self.distance -= self.speed
        if self.distance < 2:
            self.distance = 25 # Reset distance
            self.angle = random.uniform(0, 2 * math.pi)

def draw_eye(cx, cy, frame):
    """Draws the central Eye of Padullon."""
    blink = (frame % 20) < 2
    color = FG_WHITE if not blink else FG_DIM
    eye_frames = [
        r"   .---.   ",
        r"  / (O) \  ",
        r"   '---'   "
    ] if not blink else [
        r"   .---.   ",
        r"  / --- \  ",
        r"   '---'   "
    ]
    for i, line in enumerate(eye_frames):
        sys.stdout.write(f"{ESC}{cy + i - 1};{cx - 5}H{color}{line}")


def render_domain_frame(frame: int, width: int, height: int) -> list[str]:
    """Return a compact Eye overlay for domain animations.

    Non-blocking: returns ANSI-colored lines representing the central eye.
    """
    blink = (frame % 20) < 2
    if not blink:
        eye_frames = [
            r"   .---.   ",
            r"  / (O) \  ",
            r"   '---'   ",
        ]
    else:
        eye_frames = [
            r"   .---.   ",
            r"  / --- \  ",
            r"   '---'   ",
        ]

    # Return with color; presenter will position/pad as needed.
    return [f"{FG_CYAN}{ln}{RESET}" for ln in eye_frames]

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

    clones = [Clone(random.uniform(0, 2*math.pi), random.randint(10, 30), 0.5) for _ in range(12)]
    
    sys.stdout.write(f"{HIDE_CURSOR}{CLEAR}")
    
    # Activation
    announcement = "DOMAIN EXPANSION: EYE OF PADULLON"
    sys.stdout.write(f"{ESC}{cy};{cx - len(announcement)//2}H{FG_CYAN}{announcement}")
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
            
            # Draw Background "Eye" Grid
            for i in range(5):
                y = random.randint(1, lines-1)
                x = random.randint(1, cols-1)
                sys.stdout.write(f"{ESC}{y};{x}H{FG_DIM}.")

            # Update and Draw Clones (Attacking from all directions)
            for c in clones:
                c.update()
                # Polar to Cartesian
                px = int(cx + (c.distance * 2) * math.cos(c.angle))
                py = int(cy + c.distance * math.sin(c.angle))
                
                if 1 < px < cols and 1 < py < lines:
                    color = FG_BLUE if c.distance > 10 else FG_CYAN
                    sys.stdout.write(f"{ESC}{py};{px}H{color}{c.char}")
                    # Trail
                    tx = int(cx + ((c.distance+1) * 2) * math.cos(c.angle))
                    ty = int(cy + (c.distance+1) * math.sin(c.angle))
                    if 1 < tx < cols and 1 < ty < lines:
                        sys.stdout.write(f"{ESC}{ty};{tx}H{FG_DIM}·")

            # Draw Central Eye
            draw_eye(cx, cy, frame_count)
            
            # Status Text
            msg = "[ MULTIPLE SIGNATURES DETECTED ]"
            sys.stdout.write(f"{ESC}{lines-1};{cx - len(msg)//2}H{FG_CYAN}{msg}")

            sys.stdout.flush()
            frame_count += 1
            time.sleep(0.04)

    finally:
        sys.stdout.write(f"{SHOW_CURSOR}{RESET}{CLEAR}{HOME}")

if __name__ == "__main__":
    main()
