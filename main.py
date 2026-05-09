import time
import sys
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

# --- Specific Screen Implementations ---

class MainMenuScreen(BaseScreen):
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
            Label(cx - 6,  cy - 6, "v1.0.0 Alpha", FG_BORDER),
            
            Button(cx - 5, cy - 3, "New Game", "SCREEN_NEW_GAME"),
            Button(cx - 5, cy - 1, "Load Game", "SCREEN_LOAD_GAME"),
            Button(cx - 5, cy + 1, "Settings", "SCREEN_SETTINGS"),
            Button(cx - 5, cy + 3, "Scenes", "SCENES_MENU"),
            Button(cx - 3, cy + 5, "Quit", "EXIT")
        ]

class LoadGameScreen(BaseScreen):
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

class SettingsScreen(BaseScreen):
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

class NameEntryScreen(BaseScreen):
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

class SkillSelectionScreen(BaseScreen):
    """Redesigned Step 2 of New Game: Choose Skill Set."""
    def __init__(self, window, state):
        super().__init__(window)
        self.state = state
        self.selected_index = 0
        self.sort_column = -1 # -1 for row labels, 0-2 for characters
        self.sort_descending = False

    def setup_ui(self):
        self.title = "New Journey - Technique"
        cx = self.ox + (self.window.width // 2)
        cy = self.oy + (self.window.height // 2)

        # Heading
        self.widgets = [
            Label(cx - 15, cy - 13, "CHOOSE YOUR SKILL SET", FG_TITLE),
        ]

        # Cards
        card_width = 32
        card_spacing = 4
        start_x = cx - (3 * card_width + 2 * card_spacing) // 2

        # Portraits & Cards
        for i, data in enumerate(SKILL_DATA):
            x = start_x + i * (card_width + card_spacing)
            y = cy - 11
            
            # Cursed Card Border
            border_color = FG_TITLE if self.selected_index == i else FG_BORDER
            self.widgets.append(Label(x, y,     "┏" + "━"*(card_width-2) + "┓", border_color))
            for h in range(1, 8):
                self.widgets.append(Label(x, y + h, "┃" + " "*(card_width-2) + "┃", border_color))
            self.widgets.append(Label(x, y + 8, "┗" + "━"*(card_width-2) + "┛", border_color))

            # Portrait
            portrait_color = FG_WHITE if self.selected_index == i else FG_DIM
            for row_idx, row in enumerate(data["portrait"]):
                self.widgets.append(Label(x + (card_width - len(row))//2, y + 1 + row_idx, row, portrait_color))
            
            # Title & Summary
            self.widgets.append(Label(x + (card_width - len(data['name']))//2, y + 5, f"[{i+1}] {data['name']}", FG_TITLE if self.selected_index == i else FG_LABEL))
            self.widgets.append(Label(x + (card_width - len(data['summary']))//2, y + 6, data['summary'], FG_DIM))
            
            # Select Indicator (Now a Label, not a focusable Button)
            indicator_label = f" {data['name'].split()[0].upper()} " if self.selected_index == i else f" PRESS [{i+1}] "
            self.widgets.append(Label(x + (card_width - len(indicator_label))//2, y + 7, indicator_label, FG_TITLE if self.selected_index == i else FG_DIM))

        # Comparison Table (Redesigned 2-Column Format)
        table_y = cy + 1
        table_x = cx - 50
        
        selected_data = SKILL_DATA[self.selected_index]
        self.widgets.append(Label(table_x, table_y - 2, f"── {selected_data['name'].upper()}: TECHNIQUE DETAILS ──", FG_TITLE))
        
        # Table Headers
        self.widgets.append(Label(table_x,      table_y, "Skill/Technique   ", FG_LABEL))
        self.widgets.append(Label(table_x + 25, table_y, "Description", FG_LABEL))
        
        # Horizontal line
        self.widgets.append(Label(table_x, table_y + 1, "─" * 100, FG_BORDER))

        # Table Rows
        row_labels = ["1st Skill", "2nd Skill", "3rd Skill (SS)", "Domain"]
        techniques = selected_data["techniques"]

        for i, row_label in enumerate(row_labels):
            tech_str = techniques[i]
            # Split "Name – Description"
            if " – " in tech_str:
                tech_name, tech_desc = tech_str.split(" – ", 1)
            else:
                tech_name, tech_desc = tech_str, ""

            # Label (Column 1)
            self.widgets.append(Label(table_x, table_y + 2 + i*2, f"{row_label:<15}", FG_LABEL))
            
            # Technique Name + Description (Column 2)
            # We combine them or show them separately. User wants "Skill/Technique | Description"
            self.widgets.append(Label(table_x + 25, table_y + 2 + i*2, f"{tech_name}", FG_TITLE))
            self.widgets.append(Label(table_x + 55, table_y + 2 + i*2, f"» {tech_desc}", FG_WHITE))
            
            # Separator
            if i < 3:
                self.widgets.append(Label(table_x, table_y + 3 + i*2, "─" * 100, FG_BORDER))

        # Bottom Actions
        self.confirm_btn = Button(cx - 15, cy + 12, "Confirm Selection [Enter]", "EMBARK")
        self.widgets.append(self.confirm_btn)
        self.widgets.append(Button(cx + 10,  cy + 12, "Back", "SCREEN_NEW_GAME"))

    def handle_key(self, key: str):
        # Numeric keys 1, 2, 3 are now the EXCLUSIVE way to select
        if key in ("1", "2", "3"):
            self.selected_index = int(key) - 1
            self.setup_ui()
            return None

        result = super().handle_key(key)
        if result == "EMBARK":
            # Force set the player class based on the CURRENT selected_index
            selected_key = SKILL_DATA[self.selected_index]["id"]
            self.state.player = Player(self.state.player_name, selected_key)
            return "SCENE_01_INTRO"
        return result

class ConfirmExitScreen(BaseScreen):
    """Dedicated screen for exit confirmation."""
    def __init__(self, window: WindowManager):
        super().__init__(window)
        self.previous_state = "SCREEN_MAIN_MENU"
        self.state = None # Will be set by manager

    def setup_ui(self):
        self.title = "Confirmation"
        cx = self.ox + (self.window.width // 2)
        cy = self.oy + (self.window.height // 2)

        self.widgets = [
            Label(cx - 15, cy - 4, "Are you sure you want to exit?", FG_TITLE),
            Button(cx - 12, cy + 1, "Yes, Exit", "EXIT"),
            Button(cx + 2,  cy + 1, "No, Return", "RETURN_TO_PREV")
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


class ScenesMenuScreen(BaseScreen):
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

# ==========================================
# MAIN APPLICATION LOOP
# ==========================================

class GameOverScreen(BaseScreen):
    """Reverse Curse Technique - Checkpoint System."""
    def __init__(self, window, state):
        super().__init__(window)
        self.state = state

    def setup_ui(self):
        self.title = "CURSED COLLAPSE"
        cx = self.ox + (self.window.width // 2)
        cy = self.oy + (self.window.height // 2)

        # HUD glitch uses player instability when available (canonical death flow updates Player).
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
    window = WindowManager()
    window.setup()
    
    # Initialize state locally
    state = GameState()
    
    # Initialize our screen objects and pass state to those that need it
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
    # Pass state to ConfirmExitScreen as well
    screens["SCREEN_CONFIRM_EXIT"].state = state

    # Register story scenes and gameplay anchors from the canonical campaign registry.
    screens.update(build_campaign_screens(window, state))

    # Make battle action labels match Ui_test.py formatting (e.g. "1.PUNCH", "2.SKILL", ...)
    gameplay_action_labels = ["1.PUNCH", "2.SKILL", "3.DOMAIN", "4.ITEM"]
    for key in GAMEPLAY_SCREEN_KEYS:
        screen = screens.get(key)
        if screen:
            # preserve existing behavior but expose nicer labels for rendering logic
            try:
                screen.action_labels = gameplay_action_labels
                # if the scene uses `actions`, update it too for backwards compatibility
                if hasattr(screen, 'actions'):
                    screen.actions = ["PUNCH", "SKILL", "DOMAIN", "ITEM"]
            except Exception:
                pass

    try:
        current_state = "SCREEN_MAIN_MENU"
        
        # Application State Machine
        while current_state != "EXIT":
            # Clear any leftover output before running screen
            sys.stdout.write(f"{ESC}2J{ESC}H")
            sys.stdout.flush()
            
            # Retrieve the appropriate screen class and execute its run loop
            active_screen = screens.get(current_state)
            
            if active_screen:
                # The run() method blocks until the user triggers a state change
                next_state = active_screen.run()
                
                # Emergency Force Exit (bypass confirmation)
                if next_state == "EXIT_NOW":
                    current_state = "EXIT"
                    continue

                # Robust Exit Handling: Any EXIT or ESC attempt (except from the confirmation screen itself)
                # triggers the confirmation dialog.
                if next_state == "EXIT" and current_state != "SCREEN_CONFIRM_EXIT":
                    screens["SCREEN_CONFIRM_EXIT"].previous_state = current_state
                    current_state = "SCREEN_CONFIRM_EXIT"
                    continue # Skip to next loop iteration to show the confirmation screen

                if next_state == "PLAY_ALL_SCENES":
                    abort_sequence = False
                    for sname in STORY_SCENE_SEQUENCE:
                        sscreen = screens.get(sname)
                        if not sscreen:
                            continue
                        while True:
                            result = sscreen.run()
                            # Emergency Force Exit (bypass confirmation)
                            if result == "EXIT_NOW":
                                current_state = "EXIT"
                                abort_sequence = True
                                break
                            # If ESC or EXIT triggered during a scene in the sequence.
                            # Choosing "No" replays the same scene instead of skipping it.
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
            else:
                # Fallback if a route is missing
                current_state = "EXIT"

    finally:
        # Ensures terminal isn't broken if the user quits or the app crashes
        window.teardown()
        print("Safely exited to terminal.", flush=True)

if __name__ == "__main__":
    main()
