import time
import threading
import keyboard
import mouse
import dxcam
import ctypes
import numpy as np
import tkinter as tk

import matplotlib.pyplot as plt


def rgb_bgr(r, g, b):
    return np.array([b, g, r], dtype=np.int16)


RODS = {
    "default": {
        "fish": (rgb_bgr(67, 75, 91), 924),
        "arrows": (rgb_bgr(132, 133, 135), 924),
        "bar": (
            rgb_bgr(241, 241, 241),
            rgb_bgr(241, 241, 241),
            924,
        ),
        "click": (
            rgb_bgr(241, 241, 241),
            rgb_bgr(104, 123, 141),
            818,
        ),
    }
}

ROD = RODS["default"]

REGION = (567, 800, 1353, 945)
BORDERS = (572, 1348)

FPS = 75
GUI_REFRESH = 16

KP = 0.9
KD = 0.4

fishing = threading.Event()

trackers = {}
gui_data = {
    "fish": 0,
    "bar": 0,
    "control": 0,
    "error": 0,
    "output": 0.0,
    "state": "none",
}

gui_default = gui_data.copy()
gui_lock = threading.Lock()
gui_after = None

graph_time = []
graph_fish = []
graph_bar = []

root = tk.Tk()
camera = dxcam.create(output_color="BGRA", region=REGION)
camera.start(target_fps=FPS, video_mode=True)

get_frame = camera.get_latest_frame_view
is_fishing = fishing.is_set
is_pressed = mouse.is_pressed


def press():
    if not is_pressed():
        mouse.press()


def release():
    if is_pressed():
        mouse.release()


def search_row(frame, y, color, tolerance=5):
    row = frame[y, :, :3]
    diff = np.abs(row - color)

    return np.flatnonzero(np.all(diff <= tolerance, axis=1))


def squared_dist(a, b):
    d0 = int(a[0]) - int(b[0])
    d1 = int(a[1]) - int(b[1])
    d2 = int(a[2]) - int(b[2])

    return d0 * d0 + d1 * d1 + d2 * d2


def fish():
    cast()

    if not is_fishing():
        return

    shake()

    if not is_fishing():
        return

    reel()

    release()


def cast():
    press()
    time.sleep(0.5)

    if not is_pressed():
        cast()

    release()


def shake():
    fish_color, fish_y = ROD["fish"]

    start_x, start_y, end_x, end_y = REGION
    mid_x = (end_x - start_x) // 2

    while is_fishing():
        frame = get_frame()

        if frame is None:
            continue

        color = frame[fish_y - start_y, mid_x, :3]

        if np.array_equal(color, fish_color):
            return

        keyboard.press_and_release("enter")
        time.sleep(0.25)


def reel():
    start_x, start_y, end_y, end_x = REGION
    left_border, right_border = BORDERS

    fish_color, fish_screen_y = ROD["fish"]
    arrow_color, arrow_screen_y = ROD["arrows"]
    left_color, right_color, bar_screen_y = ROD["bar"]
    off_color, on_color, click_screen_y = ROD["click"]

    fish_y = fish_screen_y - start_y
    arrow_y = arrow_screen_y - start_y
    bar_y = bar_screen_y - start_y
    click_y = click_screen_y - start_y

    mid_x = (end_x - start_x) // 2
    half_width = (right_border - left_border) // 2

    last_fish = mid_x
    last_bar = mid_x

    pulse = 0.05

    last_error = 0
    last_vel = 0

    control = 0
    arrow_error = 0

    last_time = time.perf_counter()
    last_pulse = time.perf_counter()

    tracker(1, "fish", color="blue")
    tracker(2, "bar", color="red")

    while is_fishing():
        frame = get_frame()

        if frame is None:
            continue

        now = time.perf_counter()
        dt = max(now - last_time, 0.001)

        fish_coords = search_row(frame, fish_y, fish_color)

        if fish_coords.size:
            fish = int(fish_coords[0])
        else:
            fish = last_fish

        left_coords = search_row(frame, bar_y, left_color)
        right_coords = search_row(frame, bar_y, right_color)

        if left_coords.size and right_coords.size:
            left = int(left_coords[0])
            right = int(right_coords[-1])

            control = (right - left) // 2

            bar = left + control
            arrow_error = int(control * 0.17)

        else:
            arrow_coords = search_row(frame, arrow_y, arrow_color)
            pixel = frame[click_y, mid_x, :3]

            on_dist = squared_dist(pixel, on_color)
            off_dist = squared_dist(pixel, off_color)

            if arrow_coords.size:
                if on_dist < off_dist:
                    bar = int(arrow_coords[-1]) + arrow_error - control
                else:
                    bar = int(arrow_coords[0]) - arrow_error + control
            else:
                bar = last_bar + int(last_vel * dt)

        velocity = (bar - last_bar) / dt

        error = fish - bar
        derivative = (error - last_error) / dt

        output = KP * error + KD * derivative
        deadzone = control * 0.1

        fish_screen = start_x + fish
        bar_screen = start_x + bar

        left_edge = fish_screen - left_border
        right_edge = right_border - fish_screen
        edge_range = min(control * 1.25, half_width - 10)

        state = ""

        if left_edge < edge_range:
            release()

            last_pulse = now
            state = "left edge"

        elif right_edge < edge_range:
            press()

            last_pulse = now
            state = "right edge"

        elif output > deadzone:
            press()

            last_pulse = now
            state = "press"

        elif output < -deadzone:
            release()

            last_pulse = now
            state = "release"

        else:
            if now - last_pulse >= pulse:
                if is_pressed():
                    release()
                else:
                    press()

                last_pulse = now

            state = "deadzone"

        with gui_lock:
            gui_data["fish"] = fish_screen
            gui_data["bar"] = bar_screen

            gui_data["control"] = control

            gui_data["error"] = error
            gui_data["output"] = output

            gui_data["state"] = state

        graph_time.append(now)
        graph_fish.append(fish)
        graph_bar.append(bar)

        last_fish = fish
        last_bar = bar
        last_error = error
        last_vel = velocity
        last_time = now


def tracker(tracker_id, key, y=880, color="red"):
    win = tk.Toplevel(root)

    win.overrideredirect(True)
    win.wm_attributes("-topmost", True)
    win.wm_attributes("-transparentcolor", "white")

    canvas = tk.Canvas(win, width=20, height=20, bg="white", highlightthickness=0)
    canvas.pack()

    canvas.create_polygon(10, 20, 0, 5, 20, 5, fill=color, outline="black")

    trackers[tracker_id] = (win, key, y)


def clear_trackers():
    for tracker in trackers.values():
        tracker[0].destroy()

    trackers.clear()


def setup_hotkeys():
    keyboard.add_hotkey("f1", toggle)
    keyboard.add_hotkey("f2", graph_data)
    keyboard.add_hotkey("f3", exit_program)


def setup_gui():
    app_id = "azie.fischer.v4"

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

    root.title("azie's fischer")
    root.geometry("320x240")
    root.iconbitmap(r"images/azwald.ico")

    root.attributes("-topmost", True)


def update_gui():
    global gui_data, gui_after

    if not root.winfo_exists():
        return

    with gui_lock:
        data = gui_data.copy()

    for win, key, y in trackers:
        win.geometry(f"+{int(data[key] - 10)}+{y}")

    gui_after = root.after(GUI_REFRESH, update_gui)


def graph_data():
    plt.plot(graph_time, graph_fish, label="fish")
    plt.plot(graph_time, graph_bar, label="bar")

    control = gui_data["control"]

    left_edge = BORDERS[0] - REGION[0]
    right_edge = BORDERS[1] - REGION[0]

    left_border = left_edge + control
    right_border = right_edge - control

    plt.axhline(left_edge, color="green", linestyle="--", label="left edge")
    plt.axhline(right_edge, color="red", linestyle="--", label="right edge")

    plt.axhline(left_border, color="green", linestyle=":", label="left border")
    plt.axhline(right_border, color="red", linestyle=":", label="right border")

    plt.xlabel("time")
    plt.ylabel("position")

    plt.legend()
    plt.grid()
    plt.show()


def toggle():
    global gui_data

    if is_fishing():
        fishing.clear()
        clear_trackers()
        release()

        gui_data = gui_default.copy()

        return

    fishing.set()

    graph_time.clear()
    graph_bar.clear()
    graph_fish.clear()

    threading.Thread(target=fish, daemon=True).start()


def stop():
    global gui_after

    fishing.clear()

    if gui_after is not None:
        root.after_cancel(gui_after)
        gui_after = None

    release()
    keyboard.unhook_all()

    camera.stop()
    camera.release()

    clear_trackers()

    root.destroy()


def exit_program():
    root.after(0, stop)


setup_gui()
update_gui()

setup_hotkeys()

root.mainloop()
