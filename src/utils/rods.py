import os

from dataclasses import dataclass
from configparser import ConfigParser

from utils.helpers import bgrt


@dataclass
class Color:
    color: object
    y: int


@dataclass
class Bar:
    left_color: object
    right_color: object
    y: int


@dataclass
class Click:
    off_color: object
    on_color: object
    y: int


class Rod:
    def __init__(self, name):
        self.name = name

        rod_config = ConfigParser()
        rod_config.read(f"./rods/{name}.ini")

        self.fish = Color(
            color=self._color(rod_config, "fish", "color"),
            y=rod_config.getint("fish", "y"),
        )
        self.arrow = Color(
            color=self._color(rod_config, "arrows", "color"),
            y=rod_config.getint("arrows", "y"),
        )
        self.bar = Bar(
            left_color=self._color(rod_config, "bar", "color_left"),
            right_color=self._color(rod_config, "bar", "color_right"),
            y=rod_config.getint("bar", "y"),
        )
        self.click = Click(
            off_color=self._color(rod_config, "click", "color_off"),
            on_color=self._color(rod_config, "click", "color_on"),
            y=rod_config.getint("click", "y"),
        )

        save_rod(name)

    @staticmethod
    def _color(rod_config, section, key):
        values = rod_config.get(section, key).split(",")
        r, g, b, tol = (int(value.strip()) for value in values)

        return bgrt(b, g, r, tol)


def get_rods():
    return [rod[:-4] for rod in os.listdir("./rods")]


def get_active_rod():
    path = "./src/temp/rod.txt"

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            return file.readline()

    return "default"


def save_rod(name):
    path = "./src/temp"
    os.makedirs(path, exist_ok=True)

    with open(path + "/rod.txt", "w", encoding="utf-8") as file:
        file.write(name)
