from pynput.mouse import Controller, Button

mouse = Controller()


def handle_mouse(axis, value):
    value = int(value)

    if axis == "X":
        mouse.move(value, 0)

    elif axis == "Y":
        mouse.move(0, value)

    elif axis == "W":
        mouse.scroll(0, value)


def handle_click(button, value):

    if button == "L":
        btn = Button.left

    elif button == "R":
        btn = Button.right

    elif button == "C":
        btn = Button.middle

    else:
        return

    if value == 1:
        mouse.press(btn)

    elif value == 0:
        mouse.release(btn)