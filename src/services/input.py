from threading import Timer

from pynput import keyboard, mouse

mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()

mouse_down = False
debounce = False


def is_pressed():
    return mouse_down


def press():
    global mouse_down

    if mouse_down:
        return

    mouse_controller.press(mouse.Button.left)
    mouse_down = True


def release():
    global mouse_down

    if not mouse_down:
        return

    mouse_controller.release(mouse.Button.left)
    mouse_down = False


def press_enter():
    keyboard_controller.press(keyboard.Key.enter)
    keyboard_controller.release(keyboard.Key.enter)


def setup_hotkeys(toggle, show_graph):
    keybinds = {
        keyboard.Key.f3: toggle,
        keyboard.Key.f2: show_graph,
    }

    def clear_debounce():
        global debounce
        debounce = False

    def on_press(key):
        global debounce

        callback = keybinds.get(key)

        if callback is None or debounce:
            return

        debounce = True
        Timer(1, clear_debounce).start()

        callback()

    keyboard.Listener(on_press=on_press).start()
