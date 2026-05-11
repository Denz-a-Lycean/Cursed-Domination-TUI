scene_data = {
    "title": "Timeskip",
    "background_frames": [
        r"""
                     .-=================-.
                    /                     \
                   /   THREE YEARS LATER   \
                   \                       /
                    '=-=================-'
                        ...night falls...
        """
    ],
    "dialogues": [
        {"speaker": "Narration", "text": "Three years later...", "speed": 0.03, "pause_after": 0.9, "color": "label"}
    ],
    "meta": {
        "text_speed": 0.03,
        "shift_amp": 1,
        "frame_rate": 0.8,
        "max_dialogue_lines": 3,
        "sparkle": False,
        "sparkle_rate": 1.0,
        "sparkle_chars": [".", "*"],
        "sparkle_ttl": 0.6,
        "sparkle_color": "dim",
        "sparkle_max": 8
    },
    "next_state": "SCENE_03_KOGANE"
}
