import time
from threading import Thread

from config import KP, KD, REGION, BORDERS, load_rod
from input import press, release, is_pressed, press_enter
from roblox import is_active
from vision import Vision


class FishingController:
    def __init__(self, camera, state, rod_name):
        self.camera = camera
        self.state = state
        self.vision = Vision(camera)
        self.rod = load_rod(rod_name)

        self.thread = None

    def start(self):
        if self.state.fishing.is_set():
            return

        if not is_active():
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
        return self.state.fishing.is_set() and is_active()

    def fish(self):
        try:
            self.cast()

            if not self.running():
                return

            self.shake()

            if not self.running():
                return

            self.reel()

        finally:
            self.state.fishing.clear()
            release()

    def cast(self):
        press()
        time.sleep(0.5)

        while self.running() and not is_pressed():
            press()
            time.sleep(0.05)

        release()

    def shake(self):
        fish_color, fish_y = self.rod["fish"]

        start_x, start_y, end_x, end_y = REGION
        mid_x = (end_x - start_x) // 2

        while self.running():
            frame = self.vision.get_frame()

            if frame is None:
                continue

            color = frame[fish_y - start_y, mid_x, :3]

            if self.vision.squared_dist(color, fish_color) == 0:
                return

            press_enter()
            time.sleep(0.25)

    def reel(self):
        start_x, start_y, end_x, end_y = REGION

        left_border, right_border = BORDERS

        fish_color, fish_screen_y = self.rod["fish"]
        arrow_color, arrow_screen_y = self.rod["arrows"]

        left_color, right_color, bar_screen_y = self.rod["bar"]

        off_color, on_color, click_screen_y = self.rod["click"]

        click_y = click_screen_y - start_y

        mid_x = (end_x - start_x) // 2
        half_width = (right_border - left_border) // 2

        last_fish = mid_x
        last_bar = mid_x
        last_error = 0
        last_vel = 0

        pulse = 0.05
        search_time = 2

        control = 0
        arrow_error = 0

        last_time = time.perf_counter()
        last_pulse = last_time
        last_found = last_time

        while self.running():
            frame = self.vision.get_frame()

            if frame is None:
                continue

            now = time.perf_counter()

            dt = max(
                now - last_time,
                0.001,
            )

            fish_coords = self.vision.search_row(frame, fish_screen_y, fish_color)

            if fish_coords.size:
                fish = int(fish_coords[0])
                last_found = now

            elif now - last_found < search_time:
                fish = last_fish

            else:
                fish = last_fish

            left_coords = self.vision.search_row(frame, bar_screen_y, left_color)
            right_coords = self.vision.search_row(frame, bar_screen_y, right_color)

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

                pixel = frame[click_y, mid_x, :3]

                on_dist = self.vision.squared_dist(pixel, on_color)
                off_dist = self.vision.squared_dist(pixel, off_color)

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

            left_edge = fish_screen - left_border
            right_edge = right_border - fish_screen

            edge_range = min(
                control * 1.25,
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
            last_vel = velocity
            last_time = now
