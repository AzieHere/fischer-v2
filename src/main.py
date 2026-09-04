import tkinter as tk

import dxcam

import config

from services.fishing import FishingController
from services.state import State
from ui import UI
from utils.helpers import setup_cwd
from utils.rods import get_active_rod


def main():
    setup_cwd()

    root = tk.Tk()
    state = State()

    camera = dxcam.create(output_color="BGRA", region=config.REGION)

    fishing = FishingController(camera=camera, state=state, rod_name=get_active_rod())
    ui = UI(root=root, state=state, fishing=fishing)

    camera.start(target_fps=config.FPS, video_mode=True)
    ui.start()

    try:
        root.mainloop()
    finally:
        fishing.stop()
        camera.stop()
        camera.release()


if __name__ == "__main__":
    main()
