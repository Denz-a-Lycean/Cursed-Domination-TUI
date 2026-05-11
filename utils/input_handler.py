"""Input helpers that centralize safe keyboard handling for the CLI game."""

import sys
import time

try:
    import msvcrt
except ImportError:
    msvcrt = None

try:
    import select
except ImportError:
    select = None

from utils.effects import Colors, color_text, consume_collapse_choice, render_menu, render_screen
from utils.validator import ValidationError, validate_choice, validate_menu_index, validate_non_empty_text

# Optional callback used when the player presses Ctrl+C so the program can
# decide whether to exit immediately or resume the current prompt.
_interrupt_handler = None


class InstabilityCollapseError(Exception):
    """
    Raised when max instability makes the run impossible to continue.
    """


class ProgramExitRequested(Exception):
    """
    Raised when the user confirms program cancellation after Ctrl+C.
    """


def set_interrupt_handler(handler):
    """
    Register a callback that decides whether Ctrl+C should cancel the program.
    """
    global _interrupt_handler
    _interrupt_handler = handler


def _read_input(prompt):
    """Read input while converting Ctrl+C into controlled game flow."""
    while True:
        try:
            return input(prompt)
        except KeyboardInterrupt:
            # User pressed Ctrl+C: allow the registered interrupt handler to
            # decide whether to exit the program or resume the prompt.
            print()
            if _interrupt_handler and _interrupt_handler():
                raise ProgramExitRequested("Program exit confirmed by user.")
            print(color_text("[!] Resuming input.", Colors.YELLOW), flush=True)
            continue
        except EOFError:
            # Input stream closed (non-interactive environment). Treat this as
            # a graceful request to exit so automated runs/tests don't crash.
            raise ProgramExitRequested("Input closed (EOF). Exiting.")


def _timed_read_input(prompt, timeout):
    """Wait for user input with a timeout; return None if timed out."""
    if timeout is None or timeout <= 0:
        return _read_input(prompt)

    sys.stdout.write(prompt)
    sys.stdout.flush()
    buffer = ""
    start = time.monotonic()

    if msvcrt:
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getwch()
                if char in {"\r", "\n"}:
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    return buffer
                if char == "\x03":
                    raise KeyboardInterrupt
                if char == "\x08":
                    if buffer:
                        buffer = buffer[:-1]
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                    continue
                buffer += char
                sys.stdout.write(char)
                sys.stdout.flush()

            if time.monotonic() - start >= timeout:
                sys.stdout.write("\n")
                sys.stdout.flush()
                return None

            time.sleep(0.05)

    if select and sys.stdin is not None:
        while True:
            remaining = timeout - (time.monotonic() - start)
            if remaining <= 0:
                sys.stdout.write("\n")
                sys.stdout.flush()
                return None

            ready, _, _ = select.select([sys.stdin], [], [], remaining)
            if ready:
                line = sys.stdin.readline()
                if not line:
                    raise EOFError
                return line.rstrip("\n")

    return _read_input(prompt)


def choose_from_menu(title, options, status_callback=None, allow_escape=False, help_text=None):
    """
    Interactive menu using numbered text input.
    """
    validate_menu_index(0, options)

    while True:
        status_lines = status_callback() if status_callback else None
        render_menu(title, options, None, status_lines, help_text)
        raw_value = _read_input("> ").strip()

        if allow_escape and raw_value.lower() in {"esc", "exit", "back", "0"}:
            return None

        if not raw_value:
            print(color_text("[!] Enter a menu number.", Colors.RED), flush=True)
            time.sleep(0.7)
            continue

        if not raw_value.isdigit():
            print(color_text("[!] Enter a valid number from the menu.", Colors.RED), flush=True)
            time.sleep(0.8)
            continue

        numeric_index = int(raw_value) - 1
        try:
            choice = validate_menu_index(numeric_index, options)
            if consume_collapse_choice():
                raise InstabilityCollapseError("Game is not stable anymore.")
            return choice
        except ValidationError as exc:
            print(color_text(f"[!] {exc}", Colors.RED), flush=True)
            time.sleep(0.8)


def get_choice(prompt, valid_options):
    """
    Fallback text input for yes/no or typed prompts.
    """
    valid_options = {str(option).lower() for option in valid_options}

    while True:
        choice = _read_input(prompt).strip().lower()
        try:
            return validate_choice(choice, valid_options)
        except ValidationError as exc:
            print(color_text(f"[!] {exc}", Colors.RED), flush=True)


def get_non_empty_text(prompt, title="Cursed Domination"):
    """
    Prompt for text while keeping the screen presentation consistent.
    """
    while True:
        render_screen(title, [prompt], footer="Type your answer and press Enter.")
        value = _read_input("> ").strip()
        try:
            return validate_non_empty_text(value, field_name="Name")
        except ValidationError as exc:
            print(color_text(f"[!] {exc}", Colors.RED), flush=True)
        time.sleep(1)


def pause(message="Press Enter to continue...", title="Cursed Domination", footer="Press Enter.", timeout=None):
    """
    Stop on a simple message screen.
    """
    lines = message if isinstance(message, list) else [message]
    render_screen(title, lines, footer=footer)
    _timed_read_input("", timeout)


def wait_for_enter(prompt="", timeout=None):
    """
    Wait for Enter without replacing the current screen.
    """
    _timed_read_input(prompt, timeout)
