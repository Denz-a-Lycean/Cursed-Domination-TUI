scene_data = {
    "title": "Tutorial Begins",
    "background_frames": [
        r"""
                 _ _.-'`-._ _
                ;.'________'.;
     _________n.|____________|.n_________
    |""_""_""_""||==||==||==||""_""_""_""|
    |LI LI LI LI||LI||LI||LI||LI LI LI LI|
    |.. .. .. ..||..||..||..||.. .. .. ..|
    |LI LI LI LI||LI||LI||LI||LI LI LI LI|
 ,,;;,;;;,;;;,;;;,;;;,;;;,;;;,;;,;;;,;;;,;;,,
        """,
        r"""
               _ _.-'`-._ _
              ;.'________'.;
   _________n.|____________|.n_________
  |""_""_""_""||==||==||==||""_""_""_""|
  |LI LI LI LI||LI||LI||LI||LI LI LI LI|
  |.. .. .. ..||..||..||..||.. .. .. ..|
  |LI LI LI LI||LI||LI||LI||LI LI LI LI|
,,;;,;;;,;;;,;;;,;;;,;;;,;;;,;;,;;;,;;;,;;,,
        """,
        r"""
                 _ _.-'`-._ _
                ;.'________'.;
     _________n.|____________|.n_________
    |""_""_""_""||==||[]||==||""_""_""_""|
    |LI LI LI LI||LI||LI||LI||LI LI LI LI|
    |.. .. .. ..||..||..||..||.. .. .. ..|
    |LI LI LI LI||LI||LI||LI||LI LI LI LI|
 ,,;;,;;;,;;;,;;;,;;;,;;;,;;;,;;,;;;,;;;,;;,,
        """,
        r"""
                   _ _.-'`-._ _
                  ;.'________'.;
       _________n.|____________|.n_________
      |""_""_""_""||==||==||==||""_""_""_""|
      |LI LI LI LI||LI||LI||LI||LI LI LI LI|
      |.. .. .. ..||..||..||..||.. .. .. ..|
      |LI LI LI LI||LI||LI||LI||LI LI LI LI|
   ,,;;,;;;,;;;,;;;,;;;,;;;,;;;,;;,;;;,;;;,;;,,
        """
    ],
    "dialogues": [
        {"speaker": "Kogane", "text": "Ding-dong. Simple cleanup mission assigned. Stay alert. Stay alert."},
        {"speaker": "You", "text": "Yeah... something feels off."},
        {"speaker": "Kogane", "text": "Ding-dong. Ding-dong. Update detected. Same disturbances in other areas."},
        {"speaker": "You", "text": "That's it? I was just getting started."}
    ],
    "meta": {
        "text_speed": 0.02,
        "shift_amp": 1,
        "frame_rate": 1.0,
        "max_dialogue_lines": 2,
        "sparkle": True,
        "sparkle_rate": 1.2,
        "sparkle_chars": ["*", "."],
        "sparkle_ttl": 0.5,
        "sparkle_color": "label",
        "sparkle_max": 12
    },
    "next_state": "GAMEPLAY_01_TUTORIAL"
}
