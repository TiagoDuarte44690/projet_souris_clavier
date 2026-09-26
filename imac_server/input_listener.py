from evdev import InputDevice, ecodes
import select
import subprocess

KEYBOARD_DEVICE = "/dev/input/event12"
MOUSE_DEVICE = "/dev/input/event3"

IMAC_WIDTH = 1920
IMAC_HEIGHT = 1200

EDGE_THRESHOLD = 5

ACTIVE_MACHINE = "IMAC"


def send_message(connection, message):
    connection.sendall((message + "\n").encode("utf-8"))


def get_mouse_position():
    result = subprocess.check_output(
        ["xdotool", "getmouselocation", "--shell"]
    ).decode("utf-8")

    position = {}

    for line in result.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            position[key] = int(value)

    return position["X"], position["Y"]


def move_local_mouse(x, y):
    subprocess.call([
        "xdotool",
        "mousemove",
        str(int(x)),
        str(int(y))
    ])


def grab_devices(keyboard, mouse):
    try:
        keyboard.grab()
    except Exception:
        pass

    try:
        mouse.grab()
    except Exception:
        pass


def ungrab_devices(keyboard, mouse):
    try:
        keyboard.ungrab()
    except Exception:
        pass

    try:
        mouse.ungrab()
    except Exception:
        pass


def switch_to_lenovo(connection, keyboard, mouse, y):
    global ACTIVE_MACHINE

    if ACTIVE_MACHINE == "LENOVO":
        return

    print("================================")
    print(">>> PASSAGE VERS LENOVO")
    print("================================")

    # On capture clavier + souris sur l'iMac.
    grab_devices(keyboard, mouse)

    # On bloque le curseur iMac sur le bord droit.
    move_local_mouse(IMAC_WIDTH - 1, y)

    ACTIVE_MACHINE = "LENOVO"

    send_message(
        connection,
        "SWITCH:LENOVO:{}".format(y)
    )


def switch_to_imac(connection, keyboard, mouse, y):
    global ACTIVE_MACHINE

    if ACTIVE_MACHINE == "IMAC":
        return

    print("================================")
    print(">>> RETOUR VERS IMAC")
    print("================================")

    # Positionner le curseur iMac au bord droit
    # avant de rendre la souris au système.
    move_local_mouse(IMAC_WIDTH - 2, y)

    # Rendre clavier + souris à GNOME.
    ungrab_devices(keyboard, mouse)

    ACTIVE_MACHINE = "IMAC"

    send_message(
        connection,
        "SWITCH:IMAC"
    )


def start_input_listener(connection):

    keyboard = InputDevice(KEYBOARD_DEVICE)
    mouse = InputDevice(MOUSE_DEVICE)

    print("Clavier : {}".format(keyboard.name))
    print("Souris : {}".format(mouse.name))
    print("================================")
    print("SHARE CLAVIER + SOURIS")
    print("================================")
    print("iMac : 1920 x 1200")
    print("Lenovo : 1536 x 864")
    print("Machine active : IMAC")

    devices = [keyboard, mouse]

    while True:

        readable, _, _ = select.select(devices, [], [])

        mouse_x = 0
        mouse_y = 0
        mouse_wheel = 0

        for device in readable:

            events = device.read()

            for event in events:

                # ======================================================
                # CLAVIER
                # ======================================================

                if device == keyboard:

                    if event.type != ecodes.EV_KEY:
                        continue

                    # Seulement quand Lenovo est actif.
                    if ACTIVE_MACHINE == "LENOVO":

                        send_message(
                            connection,
                            "K:{}:{}".format(
                                event.code,
                                event.value
                            )
                        )

                # ======================================================
                # SOURIS
                # ======================================================

                elif device == mouse:

                    if event.type == ecodes.EV_REL:

                        if event.code == ecodes.REL_X:
                            mouse_x += event.value

                        elif event.code == ecodes.REL_Y:
                            mouse_y += event.value

                        elif event.code == ecodes.REL_WHEEL:
                            mouse_wheel += event.value

                    elif event.type == ecodes.EV_KEY:

                        if ACTIVE_MACHINE != "LENOVO":
                            continue

                        if event.code == ecodes.BTN_LEFT:

                            send_message(
                                connection,
                                "M:L:{}".format(event.value)
                            )

                        elif event.code == ecodes.BTN_RIGHT:

                            send_message(
                                connection,
                                "M:R:{}".format(event.value)
                            )

                        elif event.code == ecodes.BTN_MIDDLE:

                            send_message(
                                connection,
                                "M:C:{}".format(event.value)
                            )

        # ==============================================================
        # MOUVEMENT SOURIS VERS LENOVO
        # ==============================================================

        if ACTIVE_MACHINE == "LENOVO":

            if mouse_x != 0:

                send_message(
                    connection,
                    "M:X:{}".format(mouse_x)
                )

            if mouse_y != 0:

                send_message(
                    connection,
                    "M:Y:{}".format(mouse_y)
                )

            if mouse_wheel != 0:

                send_message(
                    connection,
                    "M:W:{}".format(mouse_wheel)
                )

        # ==============================================================
        # BORD DROIT IMAC
        # ==============================================================

        if ACTIVE_MACHINE == "IMAC":

            try:

                x, y = get_mouse_position()

                if x >= IMAC_WIDTH - EDGE_THRESHOLD:

                    switch_to_lenovo(
                        connection,
                        keyboard,
                        mouse,
                        y
                    )

            except Exception as error:

                print(
                    "Erreur position souris : {}"
                    .format(error)
                )