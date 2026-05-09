scene_data = {
    "title": "Funeral",
    "background_frames": [
        r"""
              ______________________________
             /                              \
            /    IN MEMORY OF GRANDFATHER   \
           /__________________________________\
                  ||                ||
                  ||                ||
                  ||________________||
                 /____________________\
        """,
        r"""
                  ______________________________
                 /                              \
                /    IN MEMORY OF GRANDFATHER   \
               /__________________________________\
                      ||                ||
                      ||                ||
                      ||________________||
                     /____________________\
        """,
    ],
    "dialogues": [
        {"speaker": "Narration", "text": "Your grandfather died quietly, leaving behind words you never fully understood.", "speed": 0.03, "pause_after": 0.6, "color": "dim"},
        {"speaker": "Narration", "text": "He told you to stay strong no matter what happens.", "speed": 0.03, "pause_after": 0.5, "color": "dim"},
        {"speaker": "You", "text": "I guess I'm really doing this now.", "speed": 0.025, "pause_after": 0.7},
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
    "next_state": "SCENE_02_TIMESKIP"
}
