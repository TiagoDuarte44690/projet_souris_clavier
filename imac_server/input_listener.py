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


def start_input_listener(connection):
    global ACTIVE_MACHINE

    keyboard = InputDevice(KEYBOARD_DEVICE)
    mouse = InputDevice(MOUSE_DEVICE)

    print("Clavier : {}".format(keyboard.name))
    print("Souris : {}".format(mouse.name))
    print("Transmission clavier + souris...")
    print("Détection du bord droit activée...")
    print("iMac : {} x {}".format(IMAC_WIDTH, IMAC_HEIGHT))

    devices = [keyboard, mouse]

    while True:

        readable, _, _ = select.select(devices, [], [])

        mouse_x = 0
        mouse_y = 0
        mouse_wheel = 0

        for device in readable:

            events = device.read()

            for event in events:

                # ========================================================
                # CLAVIER
                # ========================================================

                if device == keyboard:

                    if event.type != ecodes.EV_KEY:
                        continue

                    # Pour l'instant, le clavier est toujours transmis.
                    # La gestion du clavier actif viendra ensuite.

                    message = "K:{}:{}".format(
                        event.code,
                        event.value
                    )

                    send_message(connection, message)

                # ========================================================
                # SOURIS
                # ========================================================

                elif device == mouse:

                    if event.type == ecodes.EV_REL:

                        if event.code == ecodes.REL_X:
                            mouse_x += event.value

                        elif event.code == ecodes.REL_Y:
                            mouse_y += event.value

                        elif event.code == ecodes.REL_WHEEL:
                            mouse_wheel += event.value

                    elif event.type == ecodes.EV_KEY:

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

        # ================================================================
        # TRANSMISSION DES MOUVEMENTS
        # ================================================================

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

        # ================================================================
        # DÉTECTION DU BORD DROIT DE L'iMAC
        # ================================================================

        if ACTIVE_MACHINE == "IMAC":

            try:
                x, y = get_mouse_position()

                if x >= IMAC_WIDTH - EDGE_THRESHOLD:

                    print(
                        ">>> BASCULEMENT VERS LENOVO : "
                        "x={}, y={}".format(x, y)
                    )

                    send_message(
                        connection,
                        "SWITCH:LENOVO:{}:{}".format(x, y)
                    )

                    ACTIVE_MACHINE = "LENOVO"

                    # On éloigne légèrement le curseur du bord
                    # pour éviter de déclencher le switch en boucle.
                    subprocess.call([
                        "xdotool",
                        "mousemove",
                        str(IMAC_WIDTH - 20),
                        str(y)
                    ])

            except Exception as error:

                print(
                    "Erreur position souris : {}"
                    .format(error)
                )