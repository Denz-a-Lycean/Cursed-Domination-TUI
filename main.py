import os
import time
import sys
import random
try:
    # When used as a package
    from core.engine import BaseScreen, Label, FG_TITLE, FG_BORDER, FG_LABEL, Button, TextBox, WindowManager, FG_DIM, ESC, FG_WHITE
    from scenes.campaign_registry import (
        build_campaign_screens,
        gameplay_state_for_stage,
        GAMEPLAY_SCREEN_KEYS,
        STORY_SCENE_MENU_ENTRIES,
        STORY_SCENE_SEQUENCE,
    )
except ImportError:
    # Fallback for running the script directly
    from core.engine import BaseScreen, Label, FG_TITLE, FG_BORDER, FG_LABEL, Button, TextBox, WindowManager, FG_DIM, ESC, FG_WHITE
    from scenes.campaign_registry import (
        build_campaign_screens,
        gameplay_state_for_stage,
        GAMEPLAY_SCREEN_KEYS,
        STORY_SCENE_MENU_ENTRIES,
        STORY_SCENE_SEQUENCE,
    )

from models.player import Player
from systems.save_manager import load_game, save_exists
import re

from utils.effects import set_glitch_level


# Global state
class GameState:
    def __init__(self):
        self.player = None
        self.current_stage = 1
        self.player_name = ""
        self.save_data = None
        self.instability = 0
        self.death_count = 0
        self.checkpoint_stage = 1
        self.start_time = time.monotonic()
        self.elapsed_time_before_session = 0
        # Serialized checkpoint from last stage prep (for optional revive UI).
        self.last_checkpoint_payload = None

    @property
    def total_elapsed_time(self):
        return self.elapsed_time_before_session + (time.monotonic() - self.start_time)


# --- Debug autopilot (TUI/UI-UX verification helper) ---
# Purpose: Provide a lightweight, deterministic simulation of high-level user
# actions so automated agents (human or AI) can traverse TUI screens to
# collect rendered output frames, verify layout, and test UI/UX flows without
# emulating low-level keyboard input. This is strictly a debugging aid for
# TUI/UI-UX verification and NOT a gameplay agent.
# Usage: enable by running `python main.py -copilot` only. Do NOT enable this
# via environment variables or in production runs.
# Behavior summary:
#  - Autopilot discovers actionable widgets by attribute (presence of
#    `action_name`) and only selects widgets that are `is_enabled` (truthy).
#  - Preferred widgets are chosen if their visible label contains common
#    affirming keywords (e.g. continue/confirm/next/embark/load). Selection is
#    deterministic (shortest label first, then lexicographic) to aid repeatable
#    captures for automated analysis.
#  - Simple `TextBox` widgets are autofilled with minimal safe defaults (e.g.
#    a fallback player name) to allow flows that require string entry to
#    proceed. This assignment is conservative and limited to UI traversal.
#  - If no actionable widget is found within the attempt window, autopilot
#    returns the high-level action "EXIT" so the application moves to a safe
#    exit flow rather than blocking indefinitely.
# Safety and scope:
#  - Autopilot is intended for debugging and output capture only; it should
#    not perform or validate complex game logic. It intentionally avoids
#    emulating hardware/OS-level input and does not attempt to reproduce human
#    timing nuances. Use other testing infrastructure for gameplay QA.
#  - To make a widget visible to autopilot, ensure it exposes `action_name`
#    and that `is_enabled` reflects its availability when `setup_ui()` runs.
# Extensibility:
#  - Screens or widgets may add attributes such as `copilot_hint` or
#    `copilot_priority` and modify `_auto_choose_action()` to honor them for
#    more fine-grained control.
AUTO_PILOT = '-copilot' in sys.argv
try:
    AUTO_PILOT_DELAY = float(os.environ.get('COPILOT_DELAY', '0.25'))
except Exception:
    AUTO_PILOT_DELAY = 0.25

# NOTE: core.engine uses direct keyboard reads, so autopilot is implemented
# by auto-navigating focus/state at the screen level (no real keyboard).
# We keep this lightweight: when enabled, we try to confirm/advance using
# deterministic choices based on widget labels and current screen title.


class AutoPilotMixin:
    """Mixin to make `BaseScreen.run()` effectively non-interactive for debug captures.

    Intended audience: other automated agents (AI copilots, test harnesses) using
    this runtime to exercise and capture TUI output. This mixin provides a
    conservative, deterministic pathway through UI screens by choosing actionable
    widgets at the screen level rather than simulating raw keystrokes.

    Key guarantees for AI consumers:
    - Deterministic selection: picks the shortest, most-semantic label first.
    - Attribute-driven discovery: relies on `action_name` and `is_enabled`.
    - Low blast radius: only writes minimal autofill to `TextBox.value` and
      returns high-level action keys (strings) to let the main loop decide the
      next state.
    - Predictable failure mode: returns "EXIT" when no suitable action is
      found, enabling safe exit flows.
    """

    def _auto_choose_action(self):
        # Attribute-driven discovery:
        # Accept any widget that exposes an `action_name` attribute and is
        # enabled (`is_enabled` truthy). This avoids fragile `isinstance` checks
        # across import paths and keeps the detection simple for automated
        # consumers.
        if not getattr(self, 'widgets', None):
            return None

        preferred = []
        fallback = []
        # Keywords that indicate an ENTER/CONFIRM-like action. Tuned for UX.
        preferred_keys = ['continue', 'confirm', 'embark', 'next', 'revive', 'apply', 'play all', 'load', 'yes']

        for w in self.widgets:
            # Only consider widgets that declare a high-level action key.
            if not hasattr(w, 'action_name'):
                continue
            # Respect explicit disabled state; default to enabled when missing.
            if not getattr(w, 'is_enabled', True):
                continue
            action = getattr(w, 'action_name', None)
            if not action:
                continue

            # Some widgets use `label`, others `text`. Use either for keyword matching.
            lab_attr = getattr(w, 'label', None) or getattr(w, 'text', None) or ''
            lab = str(lab_attr).strip()

            # Fallback candidate in case no preferred labels are present.
            fallback.append((lab, action, w))

            # If the visible text contains a preferred keyword, mark it preferred.
            if any(k in lab.lower() for k in preferred_keys):
                preferred.append((lab, action, w))

        # Prefer semantic choices but fall back to any actionable widget.
        pick_list = preferred if preferred else fallback
        if not pick_list:
            return None
        # If this looks like an exit/confirmation dialog, prefer 'No'/cancel.
        title = getattr(self, 'title', '') or ''
        tl = str(title).lower()
        if any(k in tl for k in ('confirm', 'confirmation', 'are you sure', 'exit')):
            no_candidates = [p for p in pick_list if 'no' in p[0].lower() or 'cancel' in p[0].lower() or 'return' in str(p[1]).lower()]
            if no_candidates:
                pick_list = no_candidates
            else:
                not_yes = [p for p in pick_list if 'yes' not in p[0].lower()]
                if not_yes:
                    pick_list = not_yes

        # Deterministic selection: shortest label first (reduces ambiguity),
        # then lexicographic to make selection stable across runs.
        pick_list.sort(key=lambda t: (len(t[0]), t[0]))
        _, action, _ = pick_list[0]
        return action

    def _auto_keypress(self):
        # Not used directly (core.engine loop reads get_keypress_nb); instead we
        # override run() to bypass key loop entirely.
        return None

    def run(self) -> str:
        # If autopilot is disabled, use normal BaseScreen.run() from core.engine.
        if not getattr(self, 'autopilot_enabled', False):
            return super().run()

        # For autopilot mode, repeatedly: setup_ui, then apply auto actions until state changes.
        # To avoid infinite loops in menus that require numeric typing, we also support
        # TextBox autofill for NameEntry.
        self._update_layout_from_window()
        self.setup_ui()

        # Auto-fill common TextBoxes.
        for w in getattr(self, 'widgets', []):
            if isinstance(w, TextBox):
                if 'name' in str(getattr(w, 'label', '')).lower() and hasattr(self, 'state'):
                    w.value = str(getattr(self.state, 'player_name', '') or 'Gaudenz')[: getattr(w, 'max_len', 16)]

        # Try to advance using auto-selected action.
        # If no Button action exists, fall back to using focus cycling by simulating NEXT.
        for _ in range(50):
            action = self._auto_choose_action()
            if action:
                # Throttle autopilot actions to avoid overwhelming the UI loop
                # (prevents racing where screens immediately accept/confirm).
                if AUTO_PILOT:
                    time.sleep(AUTO_PILOT_DELAY)
                return action

        # If we cannot decide an action, do what the user would: exit.
        if AUTO_PILOT:
            time.sleep(AUTO_PILOT_DELAY)
        return "EXIT"


# --- Specific Screen Implementations ---

class MainMenuScreen(AutoPilotMixin, BaseScreen):
    """The central hub of the application."""
    def __init__(self, window, state):
        super().__init__(window)
        self.state = state

    def setup_ui(self):
        self.title = "Main Menu"
        # Center coordinates based on content area
        cx = self.ox + (self.window.width // 2)
        cy = self.oy + (self.window.height // 2)

        self.widgets = [
            Label(cx - 20, cy - 9, "┌──────────────────────────────────────┐", FG_BORDER),
            Label(cx - 20, cy - 8, "│          CURSED DOMINATION           │", FG_TITLE),
            Label(cx - 20, cy - 7, "└──────────────────────────────────────┘", FG_BORDER),
            Label(cx - 6,  cy - 6, "v1.67", FG_BORDER),

            Button(cx - 5, cy - 3, "New Game", "SCREEN_NEW_GAME"),
            Button(cx - 5, cy - 1, "Load Game", "SCREEN_LOAD_GAME"),
            Button(cx - 5, cy + 1, "Quit", "EXIT")
        ]


class LoadGameScreen(AutoPilotMixin, BaseScreen):
    """Dedicated class to handle saved game slots and loading logic."""
    def __init__(self, window, state):
        super().__init__(window)
        self.state = state

    def setup_ui(self):
        self.title = "Load Journey"
        cx = self.ox + (self.window.width // 2)
        cy = self.oy + (self.window.height // 2)

        has_save = save_exists()
        save_label = "Slot 1: Continue Journey" if has_save else "Slot 1: [ No Save Found ]"

        load_button = Button(cx - 20, cy - 5, save_label, "LOAD_SAVE", is_enabled=has_save)
        load_button.is_focusable = has_save

        self.widgets = [
            Label(cx - 10, cy - 10, "Select a Save File", FG_TITLE),
            load_button,
            Label(cx - 20, cy + 3, "Press Enter to load selected journey." if has_save else "No saved data available.", FG_DIM),
            Button(cx - 4, cy + 8, "Return", "SCREEN_MAIN_MENU")
        ]

    def handle_key(self, key: str):
        result = super().handle_key(key)
        if result == "LOAD_SAVE":
            data = load_game()
            if data:
                self.state.player = Player.from_save_data(data)
                self.state.current_stage = data.get("stage", 1)
                self.state.elapsed_time_before_session = data.get("play_time_seconds", 0)
                self.state.start_time = time.monotonic()
                return gameplay_state_for_stage(self.state.current_stage)
        return result


class SettingsScreen(AutoPilotMixin, BaseScreen):
    """Dedicated class for handling configuration changes."""
    def setup_ui(self):
        self.title = "Game Settings"
        cx = self.ox + (self.window.width // 2)
        cy = self.oy + (self.window.height // 2)

        self.widgets = [
            Label(cx - 6, cy - 10, "Configuration", FG_TITLE),

            TextBox(cx - 20, cy - 6, "Master Volume (0-100):", 25, 4),
            TextBox(cx - 20, cy - 4, "Difficulty (1-5):", 25, 2),
            TextBox(cx - 20, cy - 2, "Auto-Save (Y/N):", 25, 2),

            Button(cx - 25, cy + 5, "Apply Changes", "SCREEN_MAIN_MENU"),
            Button(cx + 5,  cy + 5, "Discard", "SCREEN_MAIN_MENU")
        ]


class NameEntryScreen(AutoPilotMixin, BaseScreen):
    """Step 1 of New Game: Enter Player Name."""
    def __init__(self, window, state):
        super().__init__(window)
        self.state = state

    def setup_ui(self):
        self.title = "New Journey - Identity"
        cx = self.ox + (self.window.width // 2)
        cy = self.oy + (self.window.height // 2)

        # cell_span=2: wider letter spacing so Windows terminals don’t crowd glyphs together.
        self.name_input = TextBox(cx - 16, cy - 2, "Enter Your Name: ", 17, 16, cell_span=2)
        self.name_input.value = (self.state.player_name or "").strip()

        self.continue_btn = Button(cx - 10, cy + 4, "Continue", "NEXT_STEP", is_enabled=False)
        self.widgets = [
            Label(cx - 10, cy - 10, "┌────────────────────┐", FG_BORDER),
            Label(cx - 10, cy - 9,  "│   NAME ENTRY       │", FG_TITLE),
            Label(cx - 10, cy - 8,  "└────────────────────┘", FG_BORDER),

            Label(cx - 6, cy - 5, "WHO ARE YOU?", FG_TITLE),
            Label(cx - 28, cy - 3, "A new soul enters the void. Alphanumeric only (Max 16).", FG_DIM),

            self.name_input,
            self.continue_btn,
            Button(cx + 4,  cy + 4, "Back", "SCREEN_MAIN_MENU")
        ]
        self.update()

    def is_valid_name(self, name):
        if not name or len(name) > 16:
            return False
        return bool(re.match(r"^[a-zA-Z0-9 ]+$", name))

    def update(self):
        name = self.name_input.value.strip()
        self.continue_btn.is_enabled = self.is_valid_name(name)

    def handle_key(self, key: str):
        result = super().handle_key(key)
        if result == "NEXT_STEP":
            name = self.name_input.value.strip()
            self.state.player_name = name
            return "CHARACTER_SELECTION"
        return result


# --- Skill Data for Redesign ---
SKILL_DATA = [
    {
        "id": "Dancer",
        "name": "JC the Dancer",
        "summary": "Fluid & Fast",
        "portrait": [
            r"   _O/   ",
            r"     \   ",
            r"     /\_ ",
            r"     \  `"
        ],
        "techniques": [
            "Punch – straight power strike",
            "Rhythmic: Hawak mo ang beat – fluid tempo boost",
            "Skaddle: The Death Dancing – 50 s power & speed surge",
            "D.D.A: Death Dancing Arena – cursed-energy drain"
        ]
    },
    {
        "id": "Bouncer",
        "name": "Joem the Bouncer",
        "summary": "Heavy Hitter",
        "portrait": [
            r"    [ ]    ",
            r"   / | \   ",
            r"  |  |  |  ",
            r"   \ _ /   "
        ],
        "techniques": [
            "Bounce – gap-closing leap",
            "Daily press! – rapid punch flurry",
            "Appeal to Bloattary – instant size & speed boost",
            "Silent Rebound Palace – total sound erase"
        ]
    },
    {
        "id": "Seeker",
        "name": "Gaudenz the Seeker",
        "summary": "Mystic Control",
        "portrait": [
            r"    (O)    ",
            r"   / | \   ",
            r"  /  |  \  ",
            r"     |     "
        ],
        "techniques": [
            "Glare – potential stun",
            "Battle cry – self-buff & enemy debuff",
            "Time Stop – skip enemy turn",
            "Eye of Padullon – multi-copy assault"
        ]
    }
]


class SkillSelectionScreen(AutoPilotMixin, BaseScreen):
    """Redesigned Step 2 of New Game: Choose Skill Set."""
    def __init__(self, window, state):
        super().__init__(window)
        self.state = state
        self.selected_index = 0
        self.sort_column = -1
        self.sort_descending = False

    def setup_ui(self):
        self.title = "New Journey - Technique"
        cx = self.ox + (self.window.width // 2)
        cy = self.oy + (self.window.height // 2)

        self.widgets = [
            Label(cx - 15, cy - 13, "CHOOSE YOUR SKILL SET", FG_TITLE),
        ]

        card_width = 32
        card_spacing = 4
        start_x = cx - (3 * card_width + 2 * card_spacing) // 2

        for i, data in enumerate(SKILL_DATA):
            x = start_x + i * (card_width + card_spacing)
            y = cy - 11

            border_color = FG_TITLE if self.selected_index == i else FG_BORDER
            self.widgets.append(Label(x, y,     "┏" + "━"*(card_width-2) + "┓", border_color))
            for h in range(1, 8):
                self.widgets.append(Label(x, y + h, "┃" + " "*(card_width-2) + "┃", border_color))
            self.widgets.append(Label(x, y + 8, "┗" + "━"*(card_width-2) + "┛", border_color))

            portrait_color = FG_WHITE if self.selected_index == i else FG_DIM
            for row_idx, row in enumerate(data["portrait"]):
                self.widgets.append(Label(x + (card_width - len(row))//2, y + 1 + row_idx, row, portrait_color))

            self.widgets.append(Label(x + (card_width - len(data['name']))//2, y + 5, f"[{i+1}] {data['name']}", FG_TITLE if self.selected_index == i else FG_LABEL))
            self.widgets.append(Label(x + (card_width - len(data['summary']))//2, y + 6, data['summary'], FG_DIM))

            indicator_label = f" {data['name'].split()[0].upper()} " if self.selected_index == i else f" PRESS [{i+1}] "
            self.widgets.append(Label(x + (card_width - len(indicator_label))//2, y + 7, indicator_label, FG_TITLE if self.selected_index == i else FG_DIM))

        table_y = cy + 1
        table_x = cx - 50

        selected_data = SKILL_DATA[self.selected_index]
        self.widgets.append(Label(table_x, table_y - 2, f"── {selected_data['name'].upper()}: TECHNIQUE DETAILS ──", FG_TITLE))
        self.widgets.append(Label(table_x,      table_y, "Skill/Technique   ", FG_LABEL))
        self.widgets.append(Label(table_x + 25, table_y, "Description", FG_LABEL))
        self.widgets.append(Label(table_x, table_y + 1, "─" * 100, FG_BORDER))

        row_labels = ["1st Skill", "2nd Skill", "3rd Skill (SS)", "Domain"]
        techniques = selected_data["techniques"]

        for i, row_label in enumerate(row_labels):
            tech_str = techniques[i]
            if " – " in tech_str:
                tech_name, tech_desc = tech_str.split(" – ", 1)
            else:
                tech_name, tech_desc = tech_str, ""

            self.widgets.append(Label(table_x, table_y + 2 + i*2, f"{row_label:<15}", FG_LABEL))
            self.widgets.append(Label(table_x + 25, table_y + 2 + i*2, f"{tech_name}", FG_TITLE))
            self.widgets.append(Label(table_x + 55, table_y + 2 + i*2, f"» {tech_desc}", FG_WHITE))

            if i < 3:
                self.widgets.append(Label(table_x, table_y + 3 + i*2, "─" * 100, FG_BORDER))

        self.confirm_btn = Button(cx - 15, cy + 12, "Confirm [Enter]", "EMBARK")
        self.widgets.append(self.confirm_btn)
        self.widgets.append(Button(cx + 10,  cy + 12, "Back", "SCREEN_NEW_GAME"))

    def handle_key(self, key: str):
        if key in ("1", "2", "3"):
            self.selected_index = int(key) - 1
            self.setup_ui()
            return None

        result = super().handle_key(key)
        if result == "EMBARK":
            selected_key = SKILL_DATA[self.selected_index]["id"]
            self.state.player = Player(self.state.player_name, selected_key)
            return "SCENE_01_INTRO"
        return result


class ConfirmExitScreen(AutoPilotMixin, BaseScreen):
    """Dedicated screen for exit confirmation."""
    def __init__(self, window):
        super().__init__(window)
        self.previous_state = "SCREEN_MAIN_MENU"
        self.state = None

    def setup_ui(self):
        self.title = "Confirmation"
        cx = self.ox + (self.window.width // 2)
        cy = self.oy + (self.window.height // 2)

        self.widgets = [
            Label(cx - 15, cy - 4, "Are you sure you want to exit?", FG_TITLE),
            Button(cx - 12, cy + 1, "Yes", "EXIT"),
            Button(cx + 2, cy + 1, "No", "RETURN_TO_PREV")
        ]

    def handle_key(self, key: str):
        if key == "ESC":
            return "RETURN_TO_PREV"
        return super().handle_key(key)

    def run(self) -> str:
        result = super().run()
        if result == "RETURN_TO_PREV":
            return self.previous_state
        return result


class ScenesMenuScreen(AutoPilotMixin, BaseScreen):
    """Menu to pick individual scenes or play them all in sequence."""
    def __init__(self, window, state):
        super().__init__(window)
        self.state = state

    def setup_ui(self):
        self.title = "Scenes"
        cx = self.ox + (self.window.width // 2)
        cy = self.oy + (self.window.height // 2)

        self.widgets = [
            Label(cx - 8, cy - 12, "Scene Showcase", FG_TITLE),
            Button(cx - 30, cy - 7, "Play All Scenes", "PLAY_ALL_SCENES"),
        ]

        left_x = cx - 30
        right_x = cx + 10
        base_y = cy - 5
        left_entries = STORY_SCENE_MENU_ENTRIES[:5]
        right_entries = STORY_SCENE_MENU_ENTRIES[5:]

        for index, (label, key) in enumerate(left_entries):
            self.widgets.append(Button(left_x, base_y + (index * 2), label, key))
        for index, (label, key) in enumerate(right_entries):
            self.widgets.append(Button(right_x, base_y + (index * 2), label, key))

        self.widgets.append(Button(cx - 6, cy + 9, "Return", "SCREEN_MAIN_MENU"))


class GameOverScreen(AutoPilotMixin, BaseScreen):
    """Reverse Curse Technique - Checkpoint System."""
    def __init__(self, window, state):
        super().__init__(window)
        self.state = state

    def setup_ui(self):
        self.title = "CURSED COLLAPSE"
        cx = self.ox + (self.window.width // 2)
        cy = self.oy + (self.window.height // 2)

        pi = self.state.player.mental_instability if self.state.player else self.state.instability
        self.state.instability = pi

        messages = [
            "Your soul flickers in the void...",
            "The Reverse Curse Technique is straining your mind.",
            "Reality begins to warp. You are losing yourself.",
            "ERROR: IDENTITY CORRUPTION DETECTED.",
            "THE VOID CONSUMES. THE VOID PROVIDES.",
            "MAXIMUM INSTABILITY REACHED. SYSTEM FAILURE IMMINENT.",
        ]
        msg = messages[min(pi, len(messages) - 1)]

        self.widgets = [
            Label(cx - 20, cy - 8, "┌──────────────────────────────────────┐", FG_TITLE),
            Label(cx - 20, cy - 7, "│           GAME OVER                  │", FG_TITLE),
            Label(cx - 20, cy - 6, "└──────────────────────────────────────┘", FG_TITLE),

            Label(cx - len(msg)//2, cy - 2, msg, FG_WHITE if pi < 3 else FG_TITLE),
            Label(cx - 15, cy + 1, f"INSTABILITY LEVEL: {pi}/5", FG_TITLE),

            Label(cx - 15, cy + 4, "Want to start again?", FG_WHITE),
            Button(cx - 15, cy + 6, "Revive (Checkpoint)", "REVIVE"),
            Button(cx + 5,  cy + 6, "Give Up", "SCREEN_MAIN_MENU")
        ]

    def handle_key(self, key: str):
        result = super().handle_key(key)
        if result == "REVIVE":
            if self.state.player and getattr(self.state, "last_checkpoint_payload", None):
                self.state.player.load_state(dict(self.state.last_checkpoint_payload))
            elif self.state.player:
                self.state.player.hp = self.state.player.max_hp
                self.state.player.domain_meter = 0
            return gameplay_state_for_stage(self.state.checkpoint_stage)
        return result


def main():
    import os as _os
    global AUTO_PILOT
    # Re-evaluate args at runtime: only enable autopilot with the CLI flag.
    AUTO_PILOT = '-copilot' in sys.argv

    window = WindowManager()
    window.setup()

    state = GameState()

    screens = {
        "SCREEN_MAIN_MENU": MainMenuScreen(window, state),
        "SCREEN_LOAD_GAME": LoadGameScreen(window, state),
        "SCREEN_SETTINGS": SettingsScreen(window),
        "SCREEN_NEW_GAME": NameEntryScreen(window, state),
        "CHARACTER_SELECTION": SkillSelectionScreen(window, state),
        "SCREEN_CONFIRM_EXIT": ConfirmExitScreen(window),
        "SCREEN_GAME_OVER": GameOverScreen(window, state),
        "SCENES_MENU": ScenesMenuScreen(window, state)
    }

    screens["SCREEN_CONFIRM_EXIT"].state = state

    screens.update(build_campaign_screens(window, state))

    gameplay_action_labels = ["1.PUNCH", "2.SKILL", "3.DOMAIN", "4.ITEM"]
    for key in GAMEPLAY_SCREEN_KEYS:
        screen = screens.get(key)
        if screen:
            try:
                screen.action_labels = gameplay_action_labels
                if hasattr(screen, 'actions'):
                    screen.actions = ["PUNCH", "SKILL", "DOMAIN", "ITEM"]
            except Exception as exc:
                print(f"[ERROR] Failed to set gameplay action labels for {key}: {exc}", file=sys.stderr, flush=True)

    # Enable autopilot only for non-gameplay UI screens in this file.
    # Gameplay screens are handled by their own key loops; we do not interfere.
    for k in list(screens.keys()):
        if k in {
            "SCREEN_MAIN_MENU",
            "SCREEN_LOAD_GAME",
            "SCREEN_SETTINGS",
            "SCREEN_NEW_GAME",
            "CHARACTER_SELECTION",
            "SCREEN_CONFIRM_EXIT",
            "SCREEN_GAME_OVER",
            "SCENES_MENU",
        }:
            if AUTO_PILOT:
                setattr(screens[k], 'autopilot_enabled', True)

    try:
        current_state = "SCREEN_MAIN_MENU"
        set_glitch_level(0)

        while current_state != "EXIT":
            if current_state in {
                "SCREEN_MAIN_MENU",
                "SCREEN_LOAD_GAME",
                "SCREEN_SETTINGS",
                "SCENES_MENU",
                "SCREEN_NEW_GAME",
                "CHARACTER_SELECTION",
                "SCREEN_CONFIRM_EXIT",
            }:
                set_glitch_level(0)

            sys.stdout.write(f"{ESC}2J{ESC}H")
            sys.stdout.flush()

            active_screen = screens.get(current_state)
            if not active_screen:
                current_state = "EXIT"
                continue

            next_state = active_screen.run()

            if next_state == "EXIT_NOW":
                current_state = "EXIT"
                continue

            if next_state == "EXIT" and current_state != "SCREEN_CONFIRM_EXIT":
                screens["SCREEN_CONFIRM_EXIT"].previous_state = current_state
                current_state = "SCREEN_CONFIRM_EXIT"
                continue

            if next_state == "PLAY_ALL_SCENES":
                abort_sequence = False
                for sname in STORY_SCENE_SEQUENCE:
                    sscreen = screens.get(sname)
                    if not sscreen:
                        continue
                    while True:
                        result = sscreen.run()
                        if result == "EXIT_NOW":
                            current_state = "EXIT"
                            abort_sequence = True
                            break
                        if result == "EXIT":
                            screens["SCREEN_CONFIRM_EXIT"].previous_state = sname
                            confirm_result = screens["SCREEN_CONFIRM_EXIT"].run()
                            if confirm_result == "EXIT":
                                current_state = "EXIT"
                                abort_sequence = True
                                break
                            continue
                        break
                    if abort_sequence:
                        break
                else:
                    current_state = "SCREEN_MAIN_MENU"
            else:
                current_state = next_state

    finally:
        window.teardown()
        print("Safely exited to terminal.", flush=True)


if __name__ == "__main__":
    main()

