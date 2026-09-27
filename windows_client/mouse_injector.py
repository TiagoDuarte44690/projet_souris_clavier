import ctypes


# ============================================================
# WINDOWS API
# ============================================================

user32 = ctypes.windll.user32


INPUT_MOUSE = 0


MOUSEEVENTF_MOVE = 0x0001

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

MOUSEEVENTF_WHEEL = 0x0800


ULONG_PTR = ctypes.c_ulonglong


class MOUSEINPUT(
    ctypes.Structure
):

    _fields_ = [
        (
            "dx",
            ctypes.c_long
        ),
        (
            "dy",
            ctypes.c_long
        ),
        (
            "mouseData",
            ctypes.c_ulong
        ),
        (
            "dwFlags",
            ctypes.c_ulong
        ),
        (
            "time",
            ctypes.c_ulong
        ),
        (
            "dwExtraInfo",
            ULONG_PTR
        )
    ]


class INPUTUNION(
    ctypes.Union
):

    _fields_ = [
        (
            "mi",
            MOUSEINPUT
        )
    ]


class INPUT(
    ctypes.Structure
):

    _anonymous_ = (
        "u",
    )

    _fields_ = [
        (
            "type",
            ctypes.c_ulong
        ),
        (
            "u",
            INPUTUNION
        )
    ]


# ============================================================
# ENVOI WINDOWS
# ============================================================

def _send_mouse_input(
    dx=0,
    dy=0,
    flags=0,
    mouse_data=0
):

    input_event = INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(
            dx=dx,
            dy=dy,
            mouseData=mouse_data,
            dwFlags=flags,
            time=0,
            dwExtraInfo=0
        )
    )

    result = user32.SendInput(
        1,
        ctypes.byref(input_event),
        ctypes.sizeof(INPUT)
    )

    return result == 1


# ============================================================
# MOUVEMENT
# ============================================================

def handle_mouse_xy(
    dx,
    dy
):

    _send_mouse_input(
        dx=int(dx),
        dy=int(dy),
        flags=MOUSEEVENTF_MOVE
    )


def handle_mouse(
    axis,
    value
):

    value = int(value)

    if axis == "W":

        _send_mouse_input(
            mouse_data=value,
            flags=MOUSEEVENTF_WHEEL
        )


# ============================================================
# CLIC
# ============================================================

def handle_click(
    button,
    value
):

    value = int(value)

    if button == "L":

        if value == 1:

            _send_mouse_input(
                flags=MOUSEEVENTF_LEFTDOWN
            )

        elif value == 0:

            _send_mouse_input(
                flags=MOUSEEVENTF_LEFTUP
            )

    elif button == "R":

        if value == 1:

            _send_mouse_input(
                flags=MOUSEEVENTF_RIGHTDOWN
            )

        elif value == 0:

            _send_mouse_input(
                flags=MOUSEEVENTF_RIGHTUP
            )

    elif button == "C":

        if value == 1:

            _send_mouse_input(
                flags=MOUSEEVENTF_MIDDLEDOWN
            )

        elif value == 0:

            _send_mouse_input(
                flags=MOUSEEVENTF_MIDDLEUP
            )


# ============================================================
# POSITION CURSEUR
# ============================================================

def get_position():

    point = ctypes.wintypes.POINT()

    user32.GetCursorPos(
        ctypes.byref(point)
    )

    return (
        point.x,
        point.y
    )


def move_to(
    x,
    y
):

    user32.SetCursorPos(
        int(x),
        int(y)
    )