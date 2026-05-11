"""Validation helpers for player input and saved JSON data."""


class ValidationError(ValueError):
    """
    Raised when input or loaded data fails validation.
    """


def validate_non_empty_text(value, field_name="Input", max_length=30):
    """
    Validate free-text input such as player names.
    """
    text = str(value).strip()

    if not text:
        raise ValidationError(f"{field_name} cannot be empty.")

    if len(text) > max_length:
        raise ValidationError(f"{field_name} must be {max_length} characters or fewer.")

    return text


def validate_choice(value, valid_options, field_name="Choice"):
    """
    Validate a typed menu choice against allowed values.
    """
    normalized = str(value).strip().lower()
    allowed = {str(option).strip().lower() for option in valid_options}

    if normalized not in allowed:
        raise ValidationError(f"Invalid {field_name.lower()}.")

    return normalized


def validate_menu_index(index, options):
    """
    Validate an index returned from keyboard menu selection.
    """
    if not isinstance(options, (list, tuple)) or not options:
        raise ValidationError("Menu options cannot be empty.")

    if not isinstance(index, int) or not (0 <= index < len(options)):
        raise ValidationError("Selected menu index is out of range.")

    return index


def validate_int(value, field_name, minimum=None, maximum=None):
    """
    Validate numeric values from save data.
    """
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid integer.") from exc

    if minimum is not None and number < minimum:
        raise ValidationError(f"{field_name} must be at least {minimum}.")

    if maximum is not None and number > maximum:
        raise ValidationError(f"{field_name} must be at most {maximum}.")

    return number


def validate_player_class(value, valid_classes=None):
    """
    Restrict save data and selection to known player classes.
    """
    classes = valid_classes or {"Dancer", "Bouncer", "Seeker"}
    normalized = str(value).strip()

    if normalized not in classes:
        raise ValidationError("Invalid player class.")

    return normalized


def validate_inventory_names(items, allowed_names):
    """
    Filter inventory names from save data to supported item classes.
    """
    if not isinstance(items, list):
        raise ValidationError("Inventory data must be a list.")

    valid_items = []
    for item in items:
        item_name = str(item).strip()
        if item_name in allowed_names:
            valid_items.append(item_name)

    return valid_items
