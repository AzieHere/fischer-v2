import keyboard
import mouse


def is_pressed():
    return mouse.is_pressed()


def press():
    if not is_pressed():
        mouse.press()


def release():
    if is_pressed():
        mouse.release()


def press_enter():
    keyboard.press_and_release("enter")


def setup_hotkeys(toggle, show_graph, exit_program):
    keyboard.add_hotkey("f1", toggle)
    keyboard.add_hotkey("f2", show_graph)
    keyboard.add_hotkey("f3", exit_program)


def remove_hotkeys():
    keyboard.unhook_all()
