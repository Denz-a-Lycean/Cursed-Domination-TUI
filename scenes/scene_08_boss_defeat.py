scene_data = {
    "title": "Boss Falls",
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
      #   #`  |""", # Frame 1: Alive/Standing
        r"""
              v
         __ v | v
        /\/\\_|_/
       _\__/  |
      /  \/`\<`)
      \ (  |\_/
      /)))-(  |
     / /x x \ |
    /  )^/\^( |
    )_//`__>> |
      #   #`  |""", # Frame 2: Hit/Damaged (Eyes change)
        r"""
               v
          __ v | v
         /\/\\_|_/
        _\__/  |
       /  \/`\<`)
       \ (  |\_/
       /)))-(  |
      / /^ ^ \ |
      \  )^/\^ |
       )_//`_>>|
        #   #` |""", # Frame 3: Starting to tilt
        r"""
             v
          __ | v
         /\/\\_|_
        _\__/  |
       /  \/`\<`)
       \ (  |\_/
        \)))-(  |
         \^ ^\  |
          \/\ \ |
           `__>>|""", # Frame 4: Crumbling
        r"""
            v
          _ | v
         /\/\\_|
        _\__/  |
       /  \/`\<`)
        \ ( |\_/
         \))-(  |
          \^ \  |
           \ \  |
            `>> |  """, # Frame 5: Fading further
        r"""
           _
          /_\
         /   \
         \___/
          \_/
           `    """, # Frame 6: Only a remnant
        r"""
           
           .
          . .
           .
           
            """, # Frame 7: Dissipating particles
        r"""
           
           
           
           
           
           
           
           
           
           
            """ # Frame 8: Gone
    ],
    "dialogues": [
      {"speaker": "System", "text": "The Boss Has Fallen.", "speed": 0.04, "emphasis": True, "pause_after": 1.0, "color": "title"},
      {"speaker": "Orlegou", "text": "Impossible... My domain... shattered...", "speed": 0.05, "shake": True, "color": "title"},
      {"speaker": "Kogane", "text": "Ding-dong Ding-dong It's done. Energy levels are dropping. Let's go home.", "speed": 0.03},
      {"speaker": "You", "text": "Yeah.", "speed": 0.02},
      {"speaker": "", "text": "(The remains of the King of Curses vanish into the wind.)", "speed": 0.03, "pause_after": 0.8}
    ],
      "meta": {
        "text_speed": 0.03,
        "shift_amp": 1,
        "frame_rate": 4.0, # Faster for smoother animation
        "max_dialogue_lines": 3,
        "sparkle": True,
        "sparkle_rate": 1.4,
        "sparkle_chars": [".", "*", "x"],
        "sparkle_color": "title"
      },
    "next_state": "SCENE_09_TWIST"
}
