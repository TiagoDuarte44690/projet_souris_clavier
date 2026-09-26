from pynput.keyboard import Controller


keyboard = Controller()


def key_down(key):
    keyboard.press(key)


def key_up(key):
    keyboard.release(key)