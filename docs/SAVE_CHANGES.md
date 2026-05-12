Save System Improvements
=========================

Summary
-------
This change improves how game progression is persisted to disk:

- Atomic saves: writes go to a temporary file and then are replaced, preventing partially-written or corrupted save files.
- Metadata: each save now includes `save_version` and `saved_at` (UTC ISO timestamp) for easier debugging and future migration.
- Clearer semantics: the `stage` field represents the stage index the player will resume at next launch (normally the next stage after a clear).
- Safer `save_exists()`: now checks file size and presence to avoid false positives from empty files.
- Backwards compatible: `load_game()` accepts legacy save files and `validate_save_data()` fills missing metadata with sensible defaults.

Why this change
----------------
Previously saves could be partially written (e.g. interrupted while writing), which could cause load failures and loss of progression. The new atomic write strategy (`tmp` file + `os.replace`) guarantees either the old save or the new one is present. Adding `save_version` and `saved_at` makes diagnosing unexpected save/load behavior easier and prepares the project for future save-schema migrations.

What changed (technical)
------------------------
- `systems/save_manager.py`
  - `save_game()` now writes to `data/save.json.tmp` and atomically replaces `data/save.json`.
  - Adds `save_version` (currently `1`) and `saved_at` (UTC ISO timestamp) to the saved JSON payload.
  - `save_exists()` now verifies file size is greater than zero.
  - `validate_save_data()` returns the validated player fields plus `save_version` and `saved_at` (if present).
    - `save_game()` accepts optional `last_scene` and `notes` parameters and these fields are persisted in the save payload.
    - `clear_save()` was added and the game clears the saved file automatically when the final stage is completed.

Compatibility notes
-------------------
- Old saves without `save_version` / `saved_at` will still load. The validator supplies defaults.
- The `stage` semantics are unchanged (still called `stage`) but intended to represent the next stage index to resume at.

Operational notes for maintainers
---------------------------------
- If you plan to change the save schema in the future, bump `SAVE_VERSION` and add migration code in `load_game()` or the game startup flow.
- If you want to clear the player's progression (for QA or testing), delete `data/save.json`.

Example JSON (excerpt)
----------------------
{
    "name": "Gaudenz",
    "class": "Seeker",
    "hp": 120,
    "max_hp": 120,
    "attack": 15,
    "level": 3,
    "exp": 40,
    "domain_meter": 0,
    "mental_instability": 1,
    "death_count": 0,
    "inventory": ["HealItem"],
    "stage": 3,
    "play_time_seconds": 540,
    "save_version": 1,
    "saved_at": "2026-05-12T15:00:00Z"
}

Questions / Next steps
---------------------
- Both `last_scene` and `notes` fields are now supported and can be passed to `save_game()` when saving progress.
- The game now clears the saved progression automatically after the final stage is beaten. If you prefer a different behavior (e.g. keep an end-of-run snapshot), I can change it.

