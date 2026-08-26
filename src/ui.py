import tkinter as tk
import matplotlib.pyplot as plt

from config import GUI_REFRESH, REGION, BORDERS
from input import setup_hotkeys, remove_hotkeys


class UI:
    def __init__(self, root, state, fishing):
        self.root = root
        self.state = state
        self.fishing = fishing

        self.trackers = {}

        self.setup_window()
        self.setup_hotkeys()

    def setup_window(self):
        self.root.title("azie's fischer")
        self.root.geometry("320x240")
        self.root.resizable(False, False)

        try:
            self.root.iconbitmap(r"src/images/azwald.ico")
        except tk.TclError:
            pass

        self.root.attributes("-topmost", True)

    def setup_hotkeys(self):
        setup_hotkeys(self.toggle, self.show_graph, self.exit)

    def start(self):
        self.update()

    def update(self):
        if not self.root.winfo_exists():
            return

        data = self.state.get_data()

        for win, key, y in self.trackers.values():
            win.geometry(f"+{int(data[key] - 10)}+{y}")

        self.root.after(GUI_REFRESH, self.update)

    def create_tracker(
        self,
        tracker_id,
        key,
        y=880,
        color="red",
    ):
        win = tk.Toplevel(self.root)

        win.overrideredirect(True)
        win.wm_attributes(
            "-topmost",
            True,
        )
        win.wm_attributes(
            "-transparentcolor",
            "white",
        )

        canvas = tk.Canvas(
            win,
            width=20,
            height=20,
            bg="white",
            highlightthickness=0,
        )

        canvas.pack()

        canvas.create_polygon(
            10,
            20,
            0,
            5,
            20,
            5,
            fill=color,
            outline="black",
        )

        self.trackers[tracker_id] = (win, key, y)

    def clear_trackers(self):
        for win, _, _ in self.trackers.values():
            win.destroy()

        self.trackers.clear()

    def toggle(self):
        if self.state.fishing.is_set():
            self.fishing.stop()
            self.clear_trackers()

            self.state.update(
                fish=0,
                bar=0,
                control=0,
                error=0,
                output=0,
                state="none",
            )

            return

        if not self.fishing.running():
            self.fishing.start()

            self.create_tracker(1, "fish", color="blue")
            self.create_tracker(2, "bar", color="red")

    def show_graph(self):
        times, fish, bar = self.state.get_graph_data()

        if not times:
            return

        plt.figure()

        plt.plot(times, fish, label="fish")
        plt.plot(times, bar, label="bar")

        control = self.state.get_data()["control"]

        left_edge = BORDERS[0] - REGION[0]
        right_edge = BORDERS[1] - REGION[0]

        left_border = left_edge + control
        right_border = right_edge - control

        plt.axhline(left_edge, linestyle="--", label="left edge")
        plt.axhline(right_edge, linestyle="--", label="right edge")

        plt.axhline(left_border, linestyle=":", label="left border")
        plt.axhline(right_border, linestyle=":", label="right border")

        plt.xlabel("time")
        plt.ylabel("position")

        plt.legend()
        plt.grid()
        plt.show()

    def exit(self):
        self.fishing.stop()
        self.clear_trackers()

        remove_hotkeys()

        self.root.after(0, self.root.destroy)
