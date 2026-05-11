scene_data = {
    "title": "True Form",
    "background_frames": [
        r"""
           (       )
          (         )
           (       )
        """, # Frame 1: Forming
        r"""
            _..._
          .'     '.
         (         )
          `._   _.'
        """, # Frame 2: Shape
        r"""
            _..._
          .' .-. '.
         (  (   )  )
          `._'-'_.'
        """, # Frame 3: Pupil appearing
        r"""
            _..._
          .' .-. '.
         (  ( o )  )
          `._'-'_.'
        """, # Frame 4: The Eye (Final)
        r"""
            _..._
          .' .-. '.
         (  ( O )  )
          `._'-'_.'
        """, # Frame 5: Eye Dilating
        r"""
            _..._
          .' .-. '.
         (  ( o )  )
          `._'-'_.'
        """, # Frame 6: Eye back to normal
    ],
    "dialogues": [
        {"speaker": "You", "text": "...he let me win.", "speed": 0.025},
        {"speaker": "Kogane", "text": "...What just happened out there?", "speed": 0.02},
        {"speaker": "System", "text": "The entity's presence expands...", "speed": 0.03, "emphasis": True, "color": "title"},
        {"speaker": "Narration", "text": "It is simply gone. But the gaze remains.", "speed": 0.04}
    ],
    "meta": {
        "text_speed": 0.04,
        "shift_amp": 1,
        "frame_rate": 0.8,
        "max_dialogue_lines": 3,
        "sparkle": True,
        "sparkle_rate": 1.5,
        "sparkle_chars": [".", "*"],
        "sparkle_ttl": 0.6,
        "sparkle_color": "title",
        "sparkle_max": 12
    },
    "next_state": "SCENE_11_ENDING"
}
