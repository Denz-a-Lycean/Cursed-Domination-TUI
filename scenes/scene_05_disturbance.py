scene_data = {
    "title": "Disturbance Detected",
    "background_frames": [
        r"""
            /\
           /  \
      .---<    >---.
      |   _\  /_   |
    _,',_|  \/  |_,',_
_.-'     '-./\.-'     '-._
 '-._   _.-'\/'-._   _.-'
     `,` |__/\__| `,`
      |    /  \    |
      '---<    >---'
           \  /
            \/
           """,  # Frame 1 (Base)
        r"""
             /\
           /    \
      .----<      >----.
      |   _\    /_   |
    _,',_|   \/   |_,',_
 _.-'      '-./\.-'      '-._
  '-._    _.-'\/'-._    _.-'
      `,`  |__/\__|  `,`
       |     /  \     |
       '----<      >----'
            \    /
             \/
          """,  # Frame 2 (Expand)
        r"""
             /\
            /  \
       .---<    >---.
       |   _\  /_   |
     _,',_|  \/  |_,',_
 _.-'     '-./\.-'     '-._
  '-._   _.-'\/'-._   _.-'
      `,` |__/\__| `,`
       |    /  \    |
       '---<    >---'
            \  /
             \/
          """,  # Frame 1 (Base)
        r"""
              /\
             /  \
       .--<      >--.
       |  _\    /_  |
     _,',_|  \/  |_,',_
 _.-'      '-/\-'      '-._
  '-._   _.-'\/'-._   _.-'
      `,` |__/\__| `,`
       |    /  \    |
       '--<      >--.
             \  /
              \/
          """,  # Frame 3 (Compress)
        r"""
             /\
            /  \
       .---<    >---.
       |   _\  /_   |
     _,',_|  \/  |_,',_
 _.-'     '-./\.-'     '-._
  '-._   _.-'\/'-._   _.-'
      `,` |__/\__| `,`
       |    /  \    |
       '---<    >---'
            \  /
             \/
          """,  # Frame 1 (Base)
        r"""
             /\
            /  \
       .---<    >---.
       |   _\  /_   |
     _,',_|  /\  |_,',_
 _.-'     '-.\/.-'     '-._
  '-._   _.-'\/'-._   _.-'
      `,` |__\/__| `,`
       |    \  /    |
       '---<    >---'
            \  /
             \/
          """  # Frame 4 (Warp)
    ],
    "dialogues": [
        {"speaker": "Kogane",
            "text": "Ding-dong. Multiple incidents confirmed. The pattern is not normal."},
        {"speaker": "You", "text": "They're grouping up? Good... saves me time."},
        {"speaker": "Kogane", "text": "Analysis complete. They are being pulled."},
        {"speaker": "You", "text": "I wanna see what it is."}
    ],
    "meta": {
        "text_speed": 0.02,
        "shift_amp": 2,
        "frame_rate": 1.2,
        "max_dialogue_lines": 3,
        "sparkle": True,
        "sparkle_rate": 1.6,
        "sparkle_chars": [".", "*"],
        "sparkle_ttl": 0.5,
        "sparkle_color": "white",
        "sparkle_max": 20
    },
    "next_state": "GAMEPLAY_02_DISTURBANCE"
}
