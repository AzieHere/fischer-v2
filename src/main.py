import ctypes
import tkinter as tk

import dxcam

from config import ACTIVE_ROD, REGION, FPS
from fishing import FishingController
from state import State
from ui import UI


def main():
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("azie.fischer")

    root = tk.Tk()

    state = State()

    camera = dxcam.create(
        output_color="BGRA",
        region=REGION,
    )

    fishing = FishingController(
        camera=camera,
        state=state,
        rod_name=ACTIVE_ROD,
    )

    ui = UI(
        root=root,
        state=state,
        fishing=fishing,
    )

    camera.start(
        target_fps=FPS,
        video_mode=True,
    )

    ui.start()

    try:
        root.mainloop()
    finally:
        fishing.stop()
        camera.stop()
        camera.release()


if __name__ == "__main__":
    main()
