"""Save/load helpers for persisting a run to JSON.

Improvements:
- Atomic writes (write to a temp file then replace) to avoid corrupted saves.
- Adds `save_version` and `saved_at` metadata to saves.
- Keeps backward compatibility when loading legacy saves.
"""

import json
import os
import datetime

from utils.validator import (
    ValidationError,
    validate_int,
    validate_inventory_names,
    validate_non_empty_text,
    validate_player_class,
)

# Resolve relative to this package so saves land under ANSI_SCREEN/data regardless of cwd.
_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_FILE = os.path.join(_PKG_ROOT, "data", "save.json")
LEGACY_SAVE_FILE = os.path.join(_PKG_ROOT, "saves", "save.json")

# Increment this if the save schema changes incompatibly.
SAVE_VERSION = 1


def save_game(player, stage, elapsed_time=0, last_scene=None, notes=None):
    """Save player data to JSON file atomically.

    `stage` is the stage index the player will resume at next launch (usually
    the next stage after a win). `elapsed_time` should be the accumulated
    play time in seconds.
    """

    # The Player object owns its own serialization so save logic stays small.
    data = player.serialize_state()
    data.update(
        {
            "stage": int(stage),
            "play_time_seconds": int(elapsed_time),
            "save_version": SAVE_VERSION,
            "saved_at": datetime.datetime.utcnow().isoformat() + "Z",
            "last_scene": str(last_scene) if last_scene is not None else "",
            "notes": str(notes) if notes is not None else "",
        }
    )

    os.makedirs(os.path.dirname(SAVE_FILE) or ".", exist_ok=True)

    tmp_path = SAVE_FILE + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
            file.flush()
            try:
                os.fsync(file.fileno())
            except OSError:
                # Not critical on some platforms; best-effort.
                pass
        # Atomic replace
        os.replace(tmp_path, SAVE_FILE)
    except Exception:
        # Clean up temp file on failure
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        raise


def clear_save():
    """Remove any existing save files (primary + legacy).

    Returns True if at least one file was removed, False otherwise.
    """
    removed = False
    for p in (SAVE_FILE, LEGACY_SAVE_FILE):
        try:
            if os.path.exists(p):
                os.remove(p)
                removed = True
        except OSError:
            # ignore errors, attempt to continue removing other paths
            continue
    return removed


def load_game():
    """
    Load player data from JSON file.
    Returns: player_data (dict)
    """

    save_path = _resolve_save_path()
    if save_path is None:
        return None

    try:
        with open(save_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return None

    try:
        return validate_save_data(data)
    except ValidationError:
        return None


def save_exists():
    """
    Check if save file exists.
    """

    path = _resolve_save_path()
    if not path:
        return False
    try:
        return os.path.getsize(path) > 0
    except OSError:
        return False


def _resolve_save_path():
    """
    Prefer the README-aligned data path, with one legacy fallback so old saves still load.
    """
    if os.path.exists(SAVE_FILE):
        return SAVE_FILE
    if os.path.exists(LEGACY_SAVE_FILE):
        return LEGACY_SAVE_FILE
    return None


def validate_save_data(data):
    """
    Normalize and validate loaded save data.
    """
    if not isinstance(data, dict):
        raise ValidationError("Save data must be a JSON object.")

    # Core player fields validated and returned; include metadata when present.
    out = {
        "name": validate_non_empty_text(data.get("name", "Player"), field_name="Player name"),
        "class": validate_player_class(data.get("class", "Seeker")),
        "hp": validate_int(data.get("hp", 100), "HP", minimum=0, maximum=9999),
        "max_hp": validate_int(data.get("max_hp", 100), "Max HP", minimum=1, maximum=9999),
        "attack": validate_int(data.get("attack", 10), "Attack", minimum=1, maximum=9999),
        "level": validate_int(data.get("level", 1), "Level", minimum=1, maximum=999),
        "exp": validate_int(data.get("exp", 0), "EXP", minimum=0, maximum=99999),
        "domain_meter": validate_int(data.get("domain_meter", 0), "Domain Meter", minimum=0, maximum=100),
        "mental_instability": validate_int(data.get("mental_instability", 0), "Mental Instability", minimum=0, maximum=5),
        "death_count": validate_int(data.get("death_count", 0), "Death Count", minimum=0, maximum=999),
        "stage": validate_int(data.get("stage", 1), "Stage", minimum=1, maximum=999),
        "play_time_seconds": validate_int(data.get("play_time_seconds", 0), "Play Time", minimum=0),
        "inventory": validate_inventory_names(
            data.get("inventory", []),
            {"HealItem", "DomainChargeItem", "AttackBoostItem"},
        ),
    }

    # Optional metadata preserved for consumers that want to show it.
    out["save_version"] = int(data.get("save_version", SAVE_VERSION))
    out["saved_at"] = data.get("saved_at", "")
    return out
