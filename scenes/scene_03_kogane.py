scene_data = {
    "title": "Kogane Appears",
    "background_frames": [
        r"""
            _,-ddd88888bbb-._
          d8888888888888888888b
        d88888888888888888888888b
       688888888888888888888888889
       68888b8""8q888888p8""8d88889
       `d8887     p8888q     4888b'
        `d887     p8888q     488b'
            `d8bod888888dob8b'
              `d8888888888d'
                `d888888b'
                  `d888b'
                    `d'
        """,
        r"""
          _,-ddd88888bbb-._
        d8888888888888888888b
      d88888888888888888888888b
     688888888888888888888888889
     68888b8""8q888888p8""8d88889
     `d8887     p8888q     4888b'
      `d887     p8888q     488b'
          `d8bod888888dob8b'
            `d8888888888d'
              `d888888b'
                `d888b'
                  `d'
        """,
        r"""
            _,-ddd88888bbb-._
          d8888888888888888888b
        d88888888888888888888888b
       688888888888888888888888889
       688888b8""8q888888p8""8d88889
       `d88887     p8888q     4888b'
        `d8887     p8888q     488b'
            `d8bod888888dob8b'
              `d8888888888d'
                `d888888b'
                  `d888b'
                    `d'
        """,
        r"""
              _,-ddd88888bbb-._
            d8888888888888888888b
          d88888888888888888888888b
         688888888888888888888888889
         68888b8""8q888888p8""8d88889
         `d8887     p8888q     4888b'
          `d887     p8888q     488b'
              `d8bod888888dob8b'
                `d8888888888d'
                  `d888888b'
                    `d888b'
                      `d'
        """
    ],
    "dialogues": [
        {"speaker": "Kogane", "text": "Ding-dong, ding-dong. I am Kogane, your personal assistant from here on out.", "speed": 0.03, "pause_after": 0.6, "color": "label"},
        {"speaker": "You", "text": "...What?", "speed": 0.02},
        {"speaker": "Kogane", "text": "Ding-dong, bading-dong. Yep, assigned to you. I guide you, update you, and try to keep you alive.", "speed": 0.03, "pause_after": 0.5, "color": "label"},
        {"speaker": "You", "text": "You just popped out of nowhere and started talking like you own the place.", "speed": 0.02},
        {"speaker": "Kogane", "text": "Ding-dong, ding-dong. Not owning, just doing my job. You're a sorcerer now.", "speed": 0.03, "pause_after": 0.6, "color": "label"}
    ],
    "meta": {
        "text_speed": 0.03,
        "shift_amp": 1,
        "frame_rate": 1.0,
        "max_dialogue_lines": 3,
        "sparkle": False,
        "sparkle_rate": 3.0,
        "sparkle_chars": ["*", "+", "."],
        "sparkle_ttl": 0.6,
        "sparkle_color": "label",
        "sparkle_max": 18
    },
    "next_state": "SCENE_04_TUTORIAL"
}
