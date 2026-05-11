"""Save/load helpers for persisting a run to JSON."""

import json
import os

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


def save_game(player, stage, elapsed_time=0):
    """
    Save player data to JSON file.
    """

    # The Player object owns its own serialization so save logic stays small.
    data = player.serialize_state()
    data.update(
        {
            "stage": stage,
            "play_time_seconds": int(elapsed_time),
        }
    )

    os.makedirs(os.path.dirname(SAVE_FILE) or ".", exist_ok=True)

    with open(SAVE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


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

    return _resolve_save_path() is not None


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

    return {
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
