from configparser import ConfigParser

import numpy as np

ACTIVE_ROD = "default"

KP = 0.9
KD = 0.4

REGION = (567, 800, 1353, 945)
BORDERS = (572, 1348)

FPS = 75
GUI_REFRESH = 16


def bgr(b, g, r):
    return np.array([b, g, r], dtype=np.int16)


def load_rod(name):
    config = ConfigParser()
    config.read(f"./rods/{name}.ini")

    def color(section, key):
        values = config.get(section, key).split(",")
        r, g, b = (int(v.strip()) for v in values)

        return bgr(b, g, r)

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
