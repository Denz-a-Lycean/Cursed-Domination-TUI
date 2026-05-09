scene_data = {
    "title": "Orlegou Appears",
    "background_frames": [
        r"""
              v
         __ v | v
        /\/\\_|_/
       _\__/  |
      /  \/`\<`)
      \ (  |\_/
      /)))-(  |
     / /^ ^ \ |
    /  )^/\^( |
    )_//`__>> |
      #   #`  |
        """,
        r"""
               v
          __ v | v
         /\/\\_|_/
        _\__/  |
       /  \/`\<`)
       \ (  |\_/
       /)))-(  |
      / /^ ^ \ |
     /  )^/\^( |
     )_//`__>> |
       #   #`  |
        """,
        r"""
             v
        __ v | v
        /\/\\_|_/
       _\__/  |
      /  \/`\<`)
      \ (  |\/
      /)))-\  |
     / /^ ^ \ |
    /  )^/\^( |
    )_//`_>>  |
      #   #`  |
        """,
        r"""
              v
         __ v | v
        /\/\\_|_/
       _\__/  |
      /  \/`\<`)
      \ (  |\_/
      /)))-(  |
     / /^ ^ \ |
    /  )^/\^ \|
    )_//`__>> |
      #   #`  |
        """,
        r"""
              v
         __ v | v
        /\/\\_|_/
       _\__/  |
      /  \/`\<`)
      \ (  |\_/
      /)))-(  |
     / /^ ^ \ |
    /  )^/\^( |
    )_//`__>> |
      #   #`  |
        """,
        r"""
              v
         __ v | v
        /\/\\_|_/
       _\__/  |
      /  \/`\<`)
      \ (  |\_/
      /)))-(  |
     / /^ ^ \ |
    /  )^/\^( |
    )_//`__>> |
      #   #`  |
        """
    ],
    "dialogues": [
        {"speaker": "You", "text": "There you are.", "speed": 0.025},
        {"speaker": "Orlegou", "text": "And this is what they sent to face me?", "speed": 0.03, "pause_after": 0.6},
        {"speaker": "Kogane", "text": "Ding-dong. Ding-dong. Emergency alert. Special Grade detected.", "speed": 0.02, "color": "label"},
        {"speaker": "You", "text": "That's the kind of energy I've been waiting for.", "speed": 0.025},
        {"speaker": "Orlegou", "text": "How disappointing. I expected something... worth my time.", "speed": 0.035, "emphasis": True, "pause_after": 1.2, "shake": True, "shake_amp": 2, "color": "title"}
    ],
    "meta": {
        "text_speed": 0.035,
        "shift_amp": 5,
        "frame_rate": 0.6,
        "max_dialogue_lines": 3,
        "sparkle": True,
        "sparkle_rate": 1.0,
        "sparkle_chars": ["*", "+"],
        "sparkle_ttl": 0.5,
        "sparkle_color": "title",
        "sparkle_max": 10
    },
    "next_state": "GAMEPLAY_05_BOSS"
}
