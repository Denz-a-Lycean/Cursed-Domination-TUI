scene_data = {
    "title": "False Victory",
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
        """, # Frame 1: He reappears
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
        """, # Frame 2: Still there, tension building
        r"""
               \ | /
             --  *  --
               / | \
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
        """, # Frame 3: Impact/Strike starts
        r"""
        
        
              STRIKE!!
        
        
        """, # Frame 4: The screen strike itself (blank with text or impact)
    ],
    "dialogues": [
        {"speaker": "Narration", "text": "Then -- the ground shifts.", "speed": 0.04, "pause_after": 0.8},
        {"speaker": "Narration", "text": "The entity stirs. Slowly, without urgency, it rises.", "speed": 0.03},
        {"speaker": "Orlegou", "text": "...Hm. Stronger than I expected. But that was still just a greeting.", "speed": 0.04, "pause_after": 0.7},
        {"speaker": "System", "text": "*THE SCREEN SHUDDERS*", "speed": 0.01, "emphasis": True, "shake": True, "shake_amp": 10},
        {"speaker": "Orlegou", "text": "Find me again... when you're ready to show me something real.", "speed": 0.05, "emphasis": True, "pause_after": 1.5, "shake": True, "shake_amp": 5, "color": "title"}
    ],
    "meta": {
        "text_speed": 0.045,
        "shift_amp": 8, # Heavy screen shake
        "frame_rate": 0.4,
        "max_dialogue_lines": 3,
        "sparkle": True,
        "sparkle_rate": 2.0,
        "sparkle_chars": ["!", "x", "*"],
        "sparkle_ttl": 0.4,
        "sparkle_color": "title",
        "sparkle_max": 15
    },
    "next_state": "SCENE_10_TRUE_FORM"
}
