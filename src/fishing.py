import time
import config

from threading import Thread, Timer
from vision import Vision

from utils import is_roblox_active, load_rod, bgrt
from input import press, release, is_pressed, press_enter


class FishingController:
    def __init__(self, camera, state, rod_name):
        self.camera = camera
        self.state = state
        self.vision = Vision(camera)

        self.rod_name = rod_name
        self.rod = load_rod(rod_name)

        self.kp = config.KP
        self.kd = config.KD

        self.thread = None

    def start(self):
        if self.state.fishing.is_set():
            return

        if not is_roblox_active():
            return

        self.state.fishing.set()
        self.state.clear_graph()

        self.thread = Thread(
            target=self.fish,
            daemon=True,
        )

        self.thread.start()

    def stop(self):
        self.state.fishing.clear()
        release()

    def running(self):
        return self.state.fishing.is_set() and is_roblox_active()

    def fish(self):
        try:
            self.cast()

            if not self.running():
                return

            self.shake()

            if not self.running():
                return

            self.reel()

            Timer(config.CAUGHT_SEARCH, self.fish)
        finally:
            self.state.fishing.clear()
            release()

    def cast(self):
        press()
        time.sleep(0.5)

        if self.running() and not is_pressed():
            self.cast()

        release()

    def shake(self):
        fish_color, fish_y = self.rod["fish"]

        start_x, start_y, end_x, end_y = config.REGION
        mid_x = (end_x - start_x) // 2

        while self.running():
            frame = self.vision.get_frame()

            if frame is None:
                continue

            color = frame[fish_y - start_y, mid_x]

            if self.vision.squared_dist(color, fish_color) == 0:
                return

            press_enter()
            time.sleep(0.3)

    def reel(self):
        caught_color = bgrt(*config.CAUGHT_COLOR)
        caught_y = config.CAUGHT_Y
        caught_search = config.CAUGHT_SEARCH

        start_x, start_y, end_x, end_y = config.REGION
        left_border, right_border = config.BORDERS

        fish_color, fish_screen_y = self.rod["fish"]
        arrow_color, arrow_screen_y = self.rod["arrows"]
        left_color, right_color, bar_screen_y = self.rod["bar"]
        off_color, on_color, click_screen_y = self.rod["click"]

        click_y = click_screen_y - start_y

        mid_x = (end_x - start_x) // 2
        half_width = (right_border - left_border) // 2

        last_fish = last_bar = mid_x
        last_error = control = arrow_error = 0

        last_time = last_pulse = last_found = time.perf_counter()

        pulse = 0.05

        self.state.reeling.set()

        while self.running():
            frame = self.vision.get_frame()

            if frame is None:
                continue

            fish_coords = self.vision.search_row(frame, fish_screen_y, fish_color)

            fish = last_fish

            if fish_coords.size:
                fish = int(fish_coords[0])
                last_found = now

            else:
                caught_coords = self.vision.search_row(frame, caught_y, caught_color)

                if caught_coords.size > 0:
                    self.state.reeling.clear()
                    self.state.data["caught"] += 1
                    return

                if now - last_found >= caught_search:
                    self.state.reeling.clear()
                    self.state.data["missed"] += 1
                    return

            left_coords = self.vision.search_row(frame, bar_screen_y, left_color)
            right_coords = self.vision.search_row(frame, bar_screen_y, right_color)

            bar = last_bar

            if left_coords.size and right_coords.size:
                left = int(left_coords[0])
                right = int(right_coords[-1])

                control = (right - left) // 2

                bar = left + control

                arrow_error = int(control * 0.17)

            else:
                arrow_coords = self.vision.search_row(
                    frame, arrow_screen_y, arrow_color
                )

                pixel = frame[click_y, mid_x]

                on_dist = self.vision.squared_dist(pixel, on_color)
                off_dist = self.vision.squared_dist(pixel, off_color)

                if arrow_coords.size:
                    if on_dist < off_dist:
                        bar = int(arrow_coords[-1]) + arrow_error - control
                    else:
                        bar = int(arrow_coords[0]) - arrow_error + control

            now = time.perf_counter()

            dt = max(
                now - last_time,
                0.001,
            )

            error = fish - bar
            derivative = (error - last_error) / dt

            output = self.kp * error + self.kd * derivative
            deadzone = control * 0.25

            fish_screen = start_x + fish

            left_edge = fish_screen - left_border
            right_edge = right_border - fish_screen

            edge_range = min(
                control * 1.5,
                half_width - 10,
            )

            state = "deadzone"

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

            elif now - last_pulse >= pulse:
                if is_pressed():
                    release()
                else:
                    press()

                last_pulse = now

            bar_screen = start_x + bar

            self.state.update(
                fish=fish_screen,
                bar=bar_screen,
                control=control,
                error=error,
                output=output,
                state=state,
            )

            self.state.add_graph_point(now, fish, bar)

            last_fish = fish
            last_bar = bar
            last_error = error
            last_time = now

        self.state.reeling.clear()
