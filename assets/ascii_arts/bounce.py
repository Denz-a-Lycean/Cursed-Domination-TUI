import os
import sys
import time
import msvcrt
import random
import math

# --- Constants for ANSI Styling ---
ESC = "\033["
RESET = f"{ESC}0m"
FG_SILVER = f"{ESC}38;5;250m"
FG_DIM = f"{ESC}38;5;238m"
FG_WHITE = f"{ESC}97m"
FG_CYAN = f"{ESC}36m"
BG_DARK = f"{ESC}48;5;232m"
HIDE_CURSOR = f"{ESC}?25l"
SHOW_CURSOR = f"{ESC}?25h"
CLEAR = f"{ESC}2J"
HOME = f"{ESC}H"

class Echo:
    """
    Represents a 'Silent Echo' – a bouncing orb that moves without sound,
    leaving a fading trail.
    """
    def __init__(self, x: float, y: float, dx: float, dy: float, char: str = 'O'):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.char = char
        self.trail = [] # List of (x, y, age)
        self.max_trail = 8

    def move(self, max_x: int, max_y: int):
        # Store current position in trail before moving
        self.trail.insert(0, (int(self.x), int(self.y)))
        if len(self.trail) > self.max_trail:
            self.trail.pop()

        self.x += self.dx
        self.y += self.dy

        # Boundary collision with "silent rebound" effect (slight velocity randomization)
        if self.x <= 2 or self.x >= max_x - 3:
            self.dx *= -1.05 # Slight acceleration on bounce
            self.dx = max(-2.0, min(self.dx, 2.0))
            self.x = max(2, min(self.x, max_x - 3))
            
        if self.y <= 1 or self.y >= max_y - 2:
            self.dy *= -1.05
            self.dy = max(-1.2, min(self.dy, 1.2))
            self.y = max(1, min(self.y, max_y - 2))

class SilentPalaceEngine:
    """
    The 'Silent Rebound Palace' Environment.
    Handles the visual void and the soundless atmosphere.
    """
    def __init__(self):
        os.system("") 
        sys.stdout.write(f"{HIDE_CURSOR}{CLEAR}{BG_DARK}")
        sys.stdout.flush()
        self.width, self.height = self.get_dimensions()

    def get_dimensions(self) -> tuple[int, int]:
        try:
            size = os.get_terminal_size()
            return size.columns, size.lines
        except OSError:
            return 80, 24 

    def draw_domain_expansion(self):
        """Activation sequence for the Domain."""
        cx, cy = self.width // 2, self.height // 2
        
        # 1. Flash
        sys.stdout.write(f"{ESC}48;5;255m{CLEAR}")
        sys.stdout.flush()
        time.sleep(0.1)
        
        # 2. Void Construction
        sys.stdout.write(f"{BG_DARK}{CLEAR}")
        announcement = "DOMAIN EXPANSION: SILENT REBOUND PALACE"
        sys.stdout.write(f"{ESC}{cy};{cx - len(announcement)//2}H{FG_WHITE}{announcement}")
        sys.stdout.flush()
        time.sleep(1.5)
        sys.stdout.write(f"{CLEAR}")

    def draw_borders(self):
        """Draws the ethereal boundaries of the palace."""
        w, h = self.width, self.height
        border_char = "║"
        top_char = "═"
        
        # Top and Bottom
        sys.stdout.write(f"{ESC}1;1H{FG_DIM}{top_char * w}")
        sys.stdout.write(f"{ESC}{h};1H{FG_DIM}{top_char * w}")
        
        # Sides
        for y in range(2, h):
            sys.stdout.write(f"{ESC}{y};1H{FG_DIM}{border_char}")
            sys.stdout.write(f"{ESC}{y};{w}H{FG_DIM}{border_char}")

    def draw_echo(self, echo: Echo):
        """Renders an echo and its fading trail."""
        # Draw Trail
        for i, (tx, ty) in enumerate(echo.trail):
            # Fade color based on age
            shade = 250 - (i * 15)
            shade = max(232, shade)
            trail_color = f"{ESC}38;5;{shade}m"
            sys.stdout.write(f"{ESC}{ty + 1};{tx + 1}H{trail_color}·")

        # Draw Head
        sys.stdout.write(f"{ESC}{int(echo.y) + 1};{int(echo.x) + 1}H{FG_CYAN}{echo.char}")

    def cleanup(self):
        sys.stdout.write(f"{SHOW_CURSOR}{RESET}{CLEAR}{HOME}")
        sys.stdout.flush()

def main():
    engine = SilentPalaceEngine()
    engine.draw_domain_expansion()
    
    # Create multiple echoes representing "erased sounds"
    echoes = [
        Echo(engine.width//2, engine.height//2, 1.2, 0.6, '0'),
        Echo(engine.width//2, engine.height//2, -1.0, 0.8, 'o'),
        Echo(engine.width//2, engine.height//2, 0.8, -0.7, 'O')
    ]

    try:
        while True:
            if msvcrt.kbhit():
                if msvcrt.getch().lower() == b'q':
                    break

            engine.width, engine.height = engine.get_dimensions()
            
            # Use Home instead of Clear to prevent flicker
            sys.stdout.write(HOME)
            engine.draw_borders()

            for echo in echoes:
                # Clear old trail tail
                if echo.trail:
                    tx, ty = echo.trail[-1]
                    sys.stdout.write(f"{ESC}{ty + 1};{tx + 1}H ")

                echo.move(engine.width, engine.height)
                engine.draw_echo(echo)

            # Center Status
            status = "[ SOUND ERASED ]"
            sys.stdout.write(f"{ESC}{engine.height-1};{engine.width//2 - 8}H{FG_DIM}{status}")
            
            sys.stdout.flush()
            time.sleep(0.03)
            
    except KeyboardInterrupt:
        pass
    finally:
        engine.cleanup()

if __name__ == "__main__":
    main()
