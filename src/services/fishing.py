import time
from threading import Thread, Timer

import config

from services.input import is_pressed, press, press_enter, release
from services.vision import Vision
from utils.helpers import clamp, is_roblox_active
from utils.rods import Rod

CAST_DELAY = 0.5
SHAKE_DELAY = 0.3

MIN_CONTROLLER_DT = 0.01
MIN_EDGE_RANGE = 50

MAX_DERIVATIVE = 100


class FishingController:
    def __init__(self, camera, state, rod_name):
        self.camera = camera
        self.state = state
        self.vision = Vision(camera)

        self.rod = Rod(rod_name)

        self.kp = config.KP
        self.kd = config.KD

        self.thread = None

    def start(self):
        if self.state.fishing.is_set():
            return

        if not is_roblox_active():
            return

        self.state.fishing.set()

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
            self.state.clear_graph()

            if not self.running():
                return

            self.cast()

            if not self.running():
                return

            self.shake()

            if not self.running():
                return

            self.reel()

            Timer(config.FISH_TIMEOUT, self.fish).start()

        finally:
            self.state.reeling.clear()
            release()

    def cast(self):
        self.state.update_gui(status="casting")

        while self.running():
            press()
            time.sleep(CAST_DELAY)

            if is_pressed():
                break

        release()

    def shake(self):
        fish = self.rod.fish

        start_x, start_y, end_x = config.REGION[:3]
        mid_x = (end_x - start_x) // 2

        get_frame = self.vision.get_frame
        squared_dist = self.vision.squared_dist

        self.state.update_gui(status="shaking")

        while self.running():
            frame = get_frame()

            if frame is None:
                continue

            color = frame[fish.y - start_y, mid_x]

            if squared_dist(color, fish.color) == 0:
                return

            press_enter()
            time.sleep(SHAKE_DELAY)

    def reel(self):
        start_x, start_y, end_x = config.REGION[:3]
        left_border, right_border = config.BORDERS

        fish = self.rod.fish
        arrow = self.rod.arrow
        bar = self.rod.bar
        click = self.rod.click

        click_y = click.y - start_y

        mid_x = (end_x - start_x) // 2
        half_width = (right_border - left_border) // 2

        get_frame = self.vision.get_frame
        search_row = self.vision.search_row
        squared_dist = self.vision.squared_dist

        state = self.state

        last_fish = mid_x
        last_bar = mid_x

        control = 0
        arrow_offset = 0

        last_error = 0

        now = time.perf_counter()
        last_time = now
        last_found = now
        last_gui = now

        self.state.update_gui(status="reeling")

        state.reeling.set()
        release()

        while self.running():
            frame = get_frame()

            if frame is None:
                continue

            now = time.perf_counter()
            dt = max(now - last_time, 0.001)

            fish_cords = search_row(frame, fish.y, fish.color)
            left_cords = search_row(frame, bar.y, bar.left_color)
            right_cords = search_row(frame, bar.y, bar.right_color)

            fish_x = last_fish
            bar_x = last_bar

            if fish_cords.size:
                fish_x = int(fish_cords[0])
                last_found = now

            else:
                caught = self.caught_status(frame, now, last_found)

                if caught > -1:
                    return

            if left_cords.size and right_cords.size:
                left = int(left_cords[0])
                right = int(right_cords[-1])

                control = (right - left) // 2
                bar_x = left + control

                arrow_offset = int(control * 0.17)

                last_found = now

            else:
                arrow_cords = search_row(frame, arrow.y, arrow.color)

                if arrow_cords.size:
                    pixel = frame[click_y, mid_x]

                    on_dist = squared_dist(pixel, click.on_color)
                    off_dist = squared_dist(pixel, click.off_color)

                    if on_dist < off_dist:
                        bar_x = int(arrow_cords[-1]) + arrow_offset - control
                    else:
                        bar_x = int(arrow_cords[0]) - arrow_offset + control

                    last_found = now

                else:
                    caught = self.caught_status(frame, now, last_found)

                    if caught > -1:
                        return

            output, error = self.controller(bar_x, fish_x, last_error, dt)

            last_error = error
            last_time = now

            last_bar = bar_x
            last_fish = fish_x

            fish_screen = start_x + fish_x
            bar_screen = start_x + bar_x

            left_edge = fish_screen - left_border
            right_edge = right_border - fish_screen

            edge_range = clamp(
                control * 1.75,
                MIN_EDGE_RANGE,
                half_width - 10,
            )

            if left_edge < edge_range:
                release()

            elif right_edge < edge_range:
                press()

            elif output > config.THRESHOLD:
                press()

            elif output < -config.THRESHOLD:
                release()

            if now - last_gui >= config.GUI_REFRESH / 1000:
                state.update_gui(
                    fish=fish_screen,
                    bar=bar_screen,
                    control=control,
                )
                state.add_graph_point(now, fish_x, bar_x)

                last_gui = now

    def controller(self, bar, fish, last_error, dt):
        error = fish - bar
        derivative = (error - last_error) / max(dt, MIN_CONTROLLER_DT)
        derivative = clamp(derivative, -MAX_DERIVATIVE, MAX_DERIVATIVE)

        output = self.kp * error + self.kd * derivative

        return output, error

    def caught_status(self, frame, now, last_found):
        caught_cords = self.vision.search(
            frame,
            *config.CAUGHT_RANGE,
            config.CAUGHT_COLOR,
        )

        if caught_cords.size:
            self.state.gui_data["caught"] += 1
            return 0

        if now - last_found >= config.CAUGHT_SEARCH:
            self.state.gui_data["missed"] += 1
            return 0

        return -1
