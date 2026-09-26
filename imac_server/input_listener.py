from evdev import InputDevice, ecodes
import select
import subprocess

KEYBOARD_DEVICE = "/dev/input/event12"
MOUSE_DEVICE = "/dev/input/event3"

IMAC_WIDTH = 1920
EDGE_THRESHOLD = 5


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
    keyboard = InputDevice(KEYBOARD_DEVICE)
    mouse = InputDevice(MOUSE_DEVICE)

    print("Clavier : {}".format(keyboard.name))
    print("Souris : {}".format(mouse.name))
    print("Détection du bord droit activée...")
    print("iMac : 1920 x 1200")

    devices = [keyboard, mouse]

    while True:

        readable, _, _ = select.select(devices, [], [])

        mouse_x = 0
        mouse_y = 0
        mouse_wheel = 0

        for device in readable:

            events = device.read()

            for event in events:

                if device == keyboard:

                    if event.type != ecodes.EV_KEY:
                        continue

                    message = "K:{}:{}".format(
                        event.code,
                        event.value
                    )

                    send_message(connection, message)

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

        # Transmission des mouvements
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

        # Test du bord droit
        try:
            x, y = get_mouse_position()

            if x >= IMAC_WIDTH - EDGE_THRESHOLD:
                print(">>> BORD DROIT DÉTECTÉ : x={}, y={}".format(x, y))

        except Exception as error:
            print("Erreur position souris :", error)