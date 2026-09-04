import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt

import config

from services.input import is_pressed, setup_hotkeys
from utils.helpers import is_roblox_active
from utils.rods import Rod, get_rods


class UI:
    def __init__(self, root, state, fishing):
        self.root = root
        self.state = state
        self.fishing = fishing

        self.trackers = {}

        self.setup_window()
        self.setup_controls()
        self.setup_table()

        setup_hotkeys(self.toggle, self.show_graph)

    def setup_window(self):
        self.root.title(f"azie's fischer v{config.VERSION}")
        self.root.geometry("200x220")

        self.root.resizable(False, False)

        self.root.attributes("-toolwindow", True)
        self.root.attributes("-topmost", True)

    def setup_controls(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame, text="rod", width=5).grid(row=0, column=0)

        rods = get_rods()
        current_rod = self.fishing.rod.name

        self.rod_dropdown = ttk.Combobox(
            frame,
            values=rods,
            width=16,
            state="readonly",
        )

        self.rod_dropdown.grid(row=0, column=1, pady=5, sticky="w")
        self.rod_dropdown.set(current_rod)

        self.rod_dropdown.bind(
            "<<ComboboxSelected>>",
            self.change_rod,
        )

        ttk.Label(frame, text="Kp", width=5).grid(row=1, column=0, pady=2)
        ttk.Label(frame, text="Kd", width=5).grid(row=2, column=0, pady=2)

        self.kp_entry = ttk.Entry(frame, width=16)
        self.kd_entry = ttk.Entry(frame, width=16)

        self.kp_entry.grid(row=1, column=1, sticky="w")
        self.kd_entry.grid(row=2, column=1, sticky="w")

        self.kp_entry.insert(0, self.fishing.kp)
        self.kd_entry.insert(0, self.fishing.kd)

        self.kp_entry.bind("<Return>", self.focus_root)
        self.kd_entry.bind("<Return>", self.focus_root)

        self.kp_entry.bind("<FocusOut>", self.update_controller)
        self.kd_entry.bind("<FocusOut>", self.update_controller)

    def focus_root(self, event=None):
        self.root.focus_set()

    def change_rod(self, event=None):
        rod_name = self.rod_dropdown.get()

        if not rod_name:
            return

        if self.state.fishing.is_set():
            self.fishing.stop()

        self.fishing.rod = Rod(rod_name)

    def update_controller(self, event=None):
        try:
            self.fishing.kp = float(self.kp_entry.get())
            self.fishing.kd = float(self.kd_entry.get())
        except ValueError:
            self.kp_entry.delete(0, tk.END)
            self.kd_entry.delete(0, tk.END)

            self.kp_entry.insert(0, self.fishing.kp)
            self.kd_entry.insert(0, self.fishing.kd)

    def setup_table(self):
        frame = tk.Frame(
            self.root,
            bg="white",
            bd=1,
            relief="solid",
        )
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.data_label = tk.Label(
            frame,
            bg="white",
            anchor="w",
            justify="left",
            padx=5,
        )
        self.data_label.pack(fill="both", expand=True)

    def update_table(self, data):
        caught = data["caught"]
        missed = data["missed"]
        status = data["status"]
        total = caught + missed

        if total > 0:
            success_rate = round(caught / total * 100, 1)
            success_rate = "%" + str(success_rate)
        else:
            success_rate = "N/A"

        lines = [
            f"status: {status}",
            "",
            f"caught: {caught}",
            f"missed: {missed}",
            "",
            f"success rate: {success_rate}",
        ]

        self.data_label.config(text="\n".join(lines))

    def create_tracker(self, tracker_id, key, y=880, color="red"):
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-transparentcolor", "white")

        canvas = tk.Canvas(win, width=20, height=20, bg="white", highlightthickness=0)
        canvas.pack()

        canvas.create_polygon(10, 20, 0, 5, 20, 5, fill=color, outline="black")

        self.trackers[tracker_id] = (win, key, y)

    def clear_trackers(self):
        for win, _, _ in list(self.trackers.values()):
            if win.winfo_exists():
                win.destroy()

        self.trackers.clear()

    def update_trackers(self, data):
        if self.state.reeling.is_set() and not self.trackers:
            self.create_tracker(1, "fish", color="blue")
            self.create_tracker(2, "bar", color="red")

        if not self.state.reeling.is_set() and self.trackers:
            self.clear_trackers()
            return

        for win, key, y in list(self.trackers.values()):
            if not win.winfo_exists():
                continue

            if key in data:
                x = int(data[key]) - 10
                win.geometry(f"+{x}+{y}")

    def start(self):
        self.update()

    def update(self):
        try:
            if not self.root.winfo_exists():
                return

            if not is_roblox_active():
                self.fishing.stop()
                self.cleanup()

            data = self.state.get_data()

            if self.data_label.winfo_exists():
                self.update_table(data)

            self.update_trackers(data)

            self.root.after(config.GUI_REFRESH, self.update)

        except tk.TclError:
            return

    def toggle(self):
        if self.state.fishing.is_set():
            self.fishing.stop()
            self.cleanup()
        elif is_roblox_active():
            self.fishing.start()

    def cleanup(self):
        self.clear_trackers()
        self.state.update_gui(
            fish=0,
            bar=0,
            control=0,
            status="idle",
        )

    def show_graph(self):
        times, fish, bar = self.state.get_graph_data()

        if not times:
            return

        control = self.state.get_data()["control"]
        left = config.BORDERS[0] - config.REGION[0]
        right = config.BORDERS[1] - config.REGION[0]

        plt.figure()

        plt.plot(times, fish, label="fish")
        plt.plot(times, bar, label="bar")

        plt.axhline(left, linestyle="--", label="left edge")
        plt.axhline(right, linestyle="--", label="right edge")
        plt.axhline(left + control, linestyle=":", label="left border")
        plt.axhline(right - control, linestyle=":", label="right border")

        plt.xlabel("time")
        plt.ylabel("position")
        plt.legend()
        plt.grid()
        plt.show()
