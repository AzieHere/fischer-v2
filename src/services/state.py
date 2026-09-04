from threading import Event, Lock


class State:
    def __init__(self):
        self.fishing = Event()
        self.reeling = Event()
        self.lock = Lock()

        self.gui_data = {
            "fish": 0,
            "bar": 0,
            "control": 0,
            "caught": 0,
            "missed": 0,
            "status": "idle",
        }

        self.graph_time = []
        self.graph_fish = []
        self.graph_bar = []

    def update_gui(self, **values):
        with self.lock:
            self.gui_data.update(values)

    def get_data(self):
        with self.lock:
            return self.gui_data.copy()

    def clear_graph(self):
        with self.lock:
            self.graph_time.clear()
            self.graph_fish.clear()
            self.graph_bar.clear()

    def add_graph_point(self, time, fish, bar):
        with self.lock:
            self.graph_time.append(time)
            self.graph_fish.append(fish)
            self.graph_bar.append(bar)

    def get_graph_data(self):
        with self.lock:
            return (
                self.graph_time.copy(),
                self.graph_fish.copy(),
                self.graph_bar.copy(),
            )
