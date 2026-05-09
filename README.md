# Cursed-Domination-TUI

A terminal-based adventure game built around a custom ANSI/ASCII UI engine.

The project combines story scenes, character selection, combat, and save/load support into a retro-inspired text UI experience.

## Features

- Story-driven campaign with scene progression and boss battles
- Custom TUI engine using ANSI escape sequences
- Player selection and skill-based combat
- Save/load support via `data/save.json`
- Simple settings menu and scene browser

## Requirements

- Python 3.10+ recommended
- Windows is the primary supported platform due to `msvcrt` usage in the core input engine
- ANSI-compatible terminal or console window

> Note: this repository does not include a `requirements.txt`; it uses only Python standard library modules.

## Getting Started

1. Clone the repository:

```bash
git clone https://github.com/Denz-a-Lycean/Cursed-Domination-TUI.git
cd Cursed-Domination-TUI
```

2. Run the game from the repository root:

```bash
python main.py
```

3. Use the keyboard to navigate menus, enter choices, and progress through the game.

## Game Controls

- Use arrow keys / menu navigation to select options
- Press `Enter` to confirm selections
- Enter text when prompted for player name or menu input
- Use `ESC` or the Quit option to exit through the confirmation screen

## Project Structure

- `main.py` - game entry point and state machine
- `core/engine.py` - terminal UI rendering, screen widgets, and input handling
- `scenes/` - story scenes and campaign progression
- `models/` - player, enemy, item, and skill data models
- `systems/` - combat, game flow, inventory, saving, and tutorial logic
- `utils/` - input helpers, effects, randomizer, and validation utilities
- `data/save.json` - default save file location

## Notes

- The game is designed for a text-based terminal experience.
- If rendering looks misaligned, try a wider terminal window and a monospaced font.
- Save data is persisted to `data/save.json` when a save exists.