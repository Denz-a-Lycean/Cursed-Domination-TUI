
# ANSI_SCREEN

Terminal-based story and combat game built with Python and ANSI screen output.

## Requirements

- Python 3.10+

## Run

```bash
python main.py
```

## Smoke Checks

```bash
python -m tests.smoke_playthrough
python -m tools.smoke_render
```

## Save File

- `data/save.json`

## Project Layout

- `main.py` - entry point
- `core/` - terminal UI engine
- `scenes/` - story and stage flow
- `systems/` - combat, saves, tutorial, presenter
- `models/` - player, enemy, skill, item models
- `utils/` - shared helpers
- `assets/` - ASCII art assets
- `tests/` - smoke tests
- `tools/` - local utility scripts
