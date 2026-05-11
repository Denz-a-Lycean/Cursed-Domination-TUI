# Engineering Review: Cursed Domination: ANSI Edition
## DCSN03C Finals Project Assessment

This review evaluates the "Cursed Domination: ANSI Edition" codebase against the requirements specified in the DCSN03C Finals Project Documentation. The project implements a terminal-based RPG with a focus on cinematic immersion, adhering to the "built-in modules only" constraint.

## 1. Requirement Compliance Audit

The project was audited for compliance with the mandatory functional and technical requirements. The following table summarizes the status of each core requirement:

| Requirement ID | Description | Status | Evidence |
| :--- | :--- | :--- | :--- |
| **FR-01** | Character Creation | **Pass** | `main.py` implements `NameEntryScreen` and `SkillSelectionScreen` for name and class choice [1]. |
| **FR-02** | Turn-Based Combat | **Pass** | `systems/combat.py` manages a turn-based loop with Attack, Defend, and Item actions [2]. |
| **FR-03** | Inventory System | **Pass** | `systems/inventory.py` uses a Python list to manage `Item` objects [3]. |
| **FR-04** | Enemy Encounters | **Pass** | `models/enemy.py` provides stage-aware AI for 5 distinct enemy types [4]. |
| **FR-05** | Level Progression | **Pass** | `models/player.py` implements `gain_exp` and `level_up` with stat increases [5]. |
| **FR-06** | Game Loop | **Pass** | `main.py` and `WindowManager` drive the screen-based navigation and exploration [1] [6]. |
| **FR-07** | Win/Lose Logic | **Pass** | `scenes/gameplay_stage_runner.py` handles stage completion and death/retry loops [7]. |
| **Tech-01** | Built-in Only | **Pass** | Audit confirmed only `random`, `time`, `os`, `abc`, `json`, `sys`, `shutil`, `re`, and `textwrap` are used [8]. |
| **OOD-01** | OOP Design | **Pass** | Uses `abc.ABC` for `Character`, `Item`, and `Skill`. Implements inheritance and polymorphism [9] [10]. |

## 2. Architectural Analysis

### 2.1. Object-Oriented Design (OOD) Quality

The project demonstrates a strong understanding of OOP principles, exceeding the minimum requirements.

*   **Abstraction:** The use of `abc.ABC` in `models/character.py` and `models/item.py` ensures a strict contract for subclasses, facilitating polymorphic behavior in the combat system [9] [10].
*   **Inheritance:** The hierarchy of `Player(Character)` and `Enemy(Character)` is clean and leverages `super().__init__` correctly [4] [5].
*   **Encapsulation:** Protected attributes (e.g., `self._hp`, `self._items`) are used consistently, with access controlled via `@property` decorators [9] [3].

### 2.2. Technical Debt and Resolution

Several architectural weaknesses were identified during the initial review and have since been addressed:

*   **State Desynchronization:** ✅ **Resolved.** Checkpoint authority has been centralized within `systems/game.py`’s `death_system()`. The manual "bridging" logic in `scenes/gameplay_stage_runner.py` has been removed to ensure a single source of truth during retries [7].
*   **Brittle HUD Parsing:** ✅ **Resolved (Step 1).** `CombatSystem` now exposes structured data via `_status_data()`, and `AnsiGamePresenter` methods have been updated to accept this data directly, reducing reliance on fragile regex parsing [11].
*   **Input Handling Efficiency:** ✅ **Resolved.** The main render loop in `core/engine.py` now uses non-blocking input (`get_keypress_nb()`) and includes a `time.sleep(0.01)` call when idle, successfully preventing 100% CPU utilization [6].

## 3. Gameplay Feel and Terminal Immersion

### 3.1. Cinematic Presentation

The project excels in creating a "cinematic terminal experience" through several unique systems:

*   **Mental Instability (Glitch System):** The `utils/effects.py` module implements a sophisticated glitching effect that scales with the player's instability, enhancing the psychological pressure theme [12].
*   **Domain Expansion:** The combat system features a "Domain Expansion" mechanic with custom animations and a timed selection window, providing a high-stakes, interactive phase [2].

### 3.2. UX and Alignment Improvements

Post-review refinements have further improved the game's presentation:

*   **Visual Consistency:** Alignment and padding inconsistencies across combat and non-combat screens have been corrected. The HUD, command boxes, and message areas now use standardized padding for a more professional look [11].
*   **Presenter Maintainability:** Unused technical debt, such as the `Ui_test.py` dependency and placeholder comments, has been removed from the presenter layer to simplify the codebase [11].

## 4. Recommendations for Future Polish

While the critical issues have been resolved, the following experiential improvements are recommended for future development:

1.  **Non-Blocking Animations:** Transition combat animations from `time.sleep()` to a tick-based system to allow for interruptible effects and a snappier game feel.
2.  **Performance Optimization:** Pre-calculate glitch masks in `utils/effects.py` to further reduce the computational overhead of the instability system.
3.  **Graceful Terminal Resizing:** Improve the UI engine to handle terminal resizing dynamically without requiring a hard-halt error screen.

## Addendum — Post-review fixes (UI alignment and presenter cleanup)

Since the initial engineering review, the following changes were made to improve presenter maintainability and visual alignment across screens:

- **Removed `Ui_test.py` dependency**: The presenter formerly attempted to import an external `Ui_test` helper. This dependency was removed and `_build_ui_test_menu_lines` now consistently uses the presenter's internal formatting. This simplifies the codepath and eliminates a missing-file runtime branch.

- **Presenter cleanup and comment removal**: Leftover comments and the `CursedDominationUI` placeholder were removed from `systems/ansi_game_presenter.py` to reduce confusion and technical debt.

- **Alignment fixes**: Several alignment and padding inconsistencies were corrected across combat and non-combat screens:
	- Combat meta/header line, battlefield, player box, and command/message boxes were standardized to use the same inner content padding.
	- Footer rendering was adjusted to span the full frame width and align with the frame border.
	- Small column nudges were applied to provide consistent breathing space inside boxes.

- **Smoke-render tool**: Added `tools/smoke_render.py` — a development helper that renders representative main menu, gameplay HUD, and combat buffers and prints a stripped-grid view for visual inspection. This was used to validate the alignment changes.

- **Verification**: After each change the presenter file (`systems/ansi_game_presenter.py`) was syntax-checked with `python -m py_compile` and the smoke-render outputs reviewed to confirm improved alignment.

These changes are primarily cosmetic and maintainability-focused; they do not alter core gameplay logic. They address the "Brittle HUD Parsing" and alignment concerns noted in section 2.2 by simplifying the presenter and making its outputs more predictable.

## References

1.  `main.py` - Application entry point and UI screen definitions.
2.  `systems/combat.py` - Turn-based combat logic and Domain Expansion.
3.  `systems/inventory.py` - List-based item management.
4.  `models/enemy.py` - Stage-aware enemy AI and behavior pools.
5.  `models/player.py` - Player progression and class profiles.
6.  `core/engine.py` - TUI engine, rendering, and input handling.
7.  `scenes/gameplay_stage_runner.py` - Stage orchestration and death logic.
8.  `grep` audit of codebase imports - Verification of built-in module constraint.
9.  `models/character.py` - Abstract base class for combat units.
10. `models/item.py` - Abstract base class for usable items.
11. `systems/ansi_game_presenter.py` - Presenter logic and HUD parsing.
12. `utils/effects.py` - ANSI glitch and color effects.
13. `tools/smoke_render.py` - Smoke-render helper that produces representative frame buffers and a stripped-grid view for visual verification.