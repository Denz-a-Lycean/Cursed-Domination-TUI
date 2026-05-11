# ANSI_SCREEN

A terminal-based, ANSI-styled text game built in Python.

## Requirements

- Python 3.10+ (works best with a modern Python 3.x)

## Run

From the project root:

```bash
python main.py
```

## Project Structure

- `main.py` — application entry point and main screen/state machine.
- `core/` — engine primitives (screens, UI widgets, ANSI helpers).
- `scenes/` — story scenes and gameplay stage orchestration.
- `systems/` — combat, inventory, saving/loading, tutorial flow, and gameplay presentation.
- `models/` — domain objects (player, enemy, items, skills).
- `utils/` — helper utilities (effects, input handling, randomization, validation).
- `assets/` — ASCII art and other embedded art assets.
- `tests/` — smoke test(s) / automated quick runs.

## Save Data

Game progress is persisted to:

- `data/save.json`

## Notes

- The game is designed for ANSI-capable terminals.
- UI transitions and screen rendering are handled by the engine in `core/`.

## Smoke Test

If available in your environment:

```bash
python -m tests.smoke_playthrough
```

## License

(Add a license file/link if this project is intended to be shared publicly.)

