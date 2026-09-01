from threading import Timer
from pynput import keyboard, mouse

mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()

mouse_down = False
keyboard_listener = None

debounce = False


def is_pressed():
    return mouse_down


def press():
    if not mouse_down:
        mouse_controller.press(mouse.Button.left)


def release():
    if mouse_down:
        mouse_controller.release(mouse.Button.left)


def press_enter():
    keyboard_controller.press(keyboard.Key.enter)
    keyboard_controller.release(keyboard.Key.enter)


def setup_hotkeys(toggle, show_graph, exit_program):
    global keyboard_listener

    keybinds = {
        keyboard.Key.f1: toggle,
        keyboard.Key.f2: show_graph,
        keyboard.Key.f3: exit_program,
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

    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.start()


def remove_hotkeys():
    global keyboard_listener

    if keyboard_listener is not None:
        keyboard_listener.stop()
        keyboard_listener = None


def _on_click(x, y, button, pressed):
    global mouse_down

    if button == mouse.Button.left:
        mouse_down = pressed


listener = mouse.Listener(on_click=_on_click)
listener.start()
