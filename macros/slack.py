# SPDX-FileCopyrightText: 2021 Phillip Burgess for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# MACROPAD Hotkeys example: Microsoft Edge web browser for Windows

from adafruit_hid.keycode import Keycode  # REQUIRED if using Keycode.* values

app = {                      # REQUIRED dict, must be named 'app'
    'name': 'Slack Macro',  # Application name
    'macros': [             # List of button macros...
        # COLOR    LABEL    KEY SEQUENCE
        # 1st row ----------
        (0x004000, 'HOME', [Keycode.CONTROL, Keycode.SHIFT, "1"]),
        (0x004000, 'DM', [Keycode.CONTROL, Keycode.SHIFT, "2"]),
        (0x400000, 'Activity', [Keycode.CONTROL, Keycode.SHIFT, "3"]),
        # 2nd row ----------
        (0x000000, 'File', [Keycode.CONTROL, Keycode.SHIFT, "4"]),
        (0x800000, 'After', [Keycode.CONTROL, Keycode.SHIFT, "5"]),
        (0x101010, '', []),
        # 3rd row ----------
        (0x000040, 'AllREAD', [Keycode.SHIFT, Keycode.ESCAPE]),
        (0x000040, 'UnREAD', [Keycode.CONTROL, Keycode.SHIFT, "a"]),
        (0x000000, '', []),
        # 4th row ----------
        (0x202000, 'Search', [Keycode.CONTROL, "f"]),
        (0x202000, 'READ', [Keycode.ESCAPE]),
        (0x400000, 'Reaction', [Keycode.CONTROL, Keycode.SHIFT, "_"]),
        # Adafruit in new window
        # Encoder button ---
        (0x000000, '', [Keycode.CONTROL, 'k']),
		(0x000000, '', Keycode.UP_ARROW),
		(0x000000, '', Keycode.DOWN_ARROW) 
    ]
}
