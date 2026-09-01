import win32gui

import numpy as np
import os

from pathlib import Path
from configparser import ConfigParser


def bgrt(b, g, r, t):
    return np.array([b, g, r, t], dtype=np.int16)


def setup_cwd():
    script_path = Path(__file__).resolve()
    target_dir = script_path.parent.parent

    os.chdir(target_dir)


def get_rods():
    return [rod[:-4] for rod in os.listdir("./rods")]


def get_active_rod():
    path = "./src/temp/rod.txt"

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.readline()

    return "default"


def load_rod(name):
    config = ConfigParser()
    config.read(f"./rods/{name}.ini")

    def write_rod_file(rod):
        path = "./src/temp"
        os.makedirs(path, exist_ok=True)

        with open(path + "/rod.txt", "w", encoding="utf-8") as f:
            f.write(rod)

    def color(section, key):
        values = config.get(section, key).split(",")
        r, g, b, t = (int(v.strip()) for v in values)

        return bgrt(b, g, r, t)

    write_rod_file(name)

    return {
        "fish": (
            color("fish", "color"),
            config.getint("fish", "y"),
        ),
        "arrows": (
            color("arrows", "color"),
            config.getint("arrows", "y"),
        ),
        "bar": (
            color("bar", "color_left"),
            color("bar", "color_right"),
            config.getint("bar", "y"),
        ),
        "click": (
            color("click", "color_off"),
            color("click", "color_on"),
            config.getint("click", "y"),
        ),
    }


def is_roblox_active():
    window = win32gui.GetForegroundWindow()

    return win32gui.GetWindowText(window) == "Roblox"
