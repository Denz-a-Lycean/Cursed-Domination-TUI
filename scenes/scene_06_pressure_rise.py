scene_data = {
    "title": "Pressure Rising",
    "background_frames": [
        r"""
                 _  _
               ( `   )_
              (    )    `)
            (_   (_(_ )_  _)
              / / / / / /
             / / / / / /
            / / / / / /
        """,
        r"""
                 _  _
               ( `   )_
              (    )    `)
            (_   (_(_ )_  _)
             / / / / / /
            / / / / / /
           / / / / / /
        """,
        r"""
                 _  _
               ( `   )_
              (    )    `)
            (_   (_(_ )_  _)
              / / / / / /
             / / / / / /
            / / / / / /
        """,
        r"""
                 _  _
               ( `   )_
              (    )    `)
            (_   (_(_ )_  _)
            / / / / / / /
           / / / / / / /
          / / / / / / /
        """  
    ],
    "dialogues": [
        {"speaker": "Kogane", "text": "Ding-dong. Energy spike detected. Cause unknown."},
        {"speaker": "You", "text": "That pressure... finally something worth hitting."},
        {"speaker": "Kogane", "text": "Warning issued. You are pushing too far."},
        {"speaker": "You", "text": "So that's it... you're getting closer, huh. Good."}
    ],
    "meta": {
        "text_speed": 0.03,
        "shift_amp": 0,
        "frame_rate": 0.3,
        "max_dialogue_lines": 3,
        "sparkle": False,
        "sparkle_rate": 3.0,
        "sparkle_chars": ["*", "+", "."],
        "sparkle_ttl": 0.6,
        "sparkle_color": "label",
        "sparkle_max": 18
    },
    "next_state": "GAMEPLAY_03_PRESSURE"
}
