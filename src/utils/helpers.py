import os
from pathlib import Path

import numpy as np
import win32gui


def clamp(num, minimum, maximum):
    return max(minimum, min(num, maximum))


def bgrt(b, g, r, t):
    return np.array([b, g, r, t], dtype=np.int16)


def setup_cwd():
    script_path = Path(__file__).resolve()
    target_dir = script_path.parent.parent.parent

    os.chdir(target_dir)


def is_roblox_active():
    window = win32gui.GetForegroundWindow()

    return win32gui.GetWindowText(window) == "Roblox"
