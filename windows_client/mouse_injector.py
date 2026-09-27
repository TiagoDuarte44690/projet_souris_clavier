import ctypes
import ctypes.wintypes


# ============================================================
# WINDOWS API
# ============================================================

user32 = ctypes.windll.user32


# ============================================================
# CONSTANTES INPUT
# ============================================================

INPUT_MOUSE = 0


# ============================================================
# FLAGS SOURIS
# ============================================================

MOUSEEVENTF_MOVE = 0x0001

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

MOUSEEVENTF_WHEEL = 0x0800


# ============================================================
# CONFIGURATION MOLETTE
# ============================================================

# Windows utilise 120 unités pour un cran de molette.
WHEEL_DELTA = 120

# Multiplicateur supplémentaire.
#
# 1 = vitesse Windows normale
# 2 = deux fois plus rapide
# 3 = trois fois plus rapide
#
# On commence à 1.
SCROLL_MULTIPLIER = 1


# ============================================================
# TYPES WINDOWS
# ============================================================

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
            dx=int(dx),
            dy=int(dy),
            mouseData=int(mouse_data),
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
# MOUVEMENT SOURIS
# ============================================================

def handle_mouse_xy(
    dx,
    dy
):

    dx = int(dx)
    dy = int(dy)

    if dx == 0 and dy == 0:
        return

    _send_mouse_input(
        dx=dx,
        dy=dy,
        flags=MOUSEEVENTF_MOVE
    )


# ============================================================
# MOLETTE
# ============================================================

def handle_mouse(
    axis,
    value
):

    value = int(value)

    if axis != "W":
        return

    if value == 0:
        return

    # --------------------------------------------------------
    # Linux → Windows
    #
    # Linux nous donne généralement :
    #
    #     +1 / -1
    #
    # Windows attend :
    #
    #     +120 / -120
    #
    # --------------------------------------------------------

    scroll_amount = (
        value
        * WHEEL_DELTA
        * SCROLL_MULTIPLIER
    )

    _send_mouse_input(
        mouse_data=scroll_amount,
        flags=MOUSEEVENTF_WHEEL
    )


# ============================================================
# CLICS SOURIS
# ============================================================

def handle_click(
    button,
    value
):

    value = int(value)

    # ========================================================
    # CLIC GAUCHE
    # ========================================================

    if button == "L":

        if value == 1:

            _send_mouse_input(
                flags=MOUSEEVENTF_LEFTDOWN
            )

        elif value == 0:

            _send_mouse_input(
                flags=MOUSEEVENTF_LEFTUP
            )

    # ========================================================
    # CLIC DROIT
    # ========================================================

    elif button == "R":

        if value == 1:

            _send_mouse_input(
                flags=MOUSEEVENTF_RIGHTDOWN
            )

        elif value == 0:

            _send_mouse_input(
                flags=MOUSEEVENTF_RIGHTUP
            )

    # ========================================================
    # CLIC MOLETTE
    # ========================================================

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
# POSITION DU CURSEUR
# ============================================================

def get_position():

    point = ctypes.wintypes.POINT()

    success = user32.GetCursorPos(
        ctypes.byref(point)
    )

    if not success:

        return (
            0,
            0
        )

    return (
        point.x,
        point.y
    )


# ============================================================
# POSITIONNEMENT DU CURSEUR
# ============================================================

def move_to(
    x,
    y
):

    user32.SetCursorPos(
        int(x),
        int(y)
    )