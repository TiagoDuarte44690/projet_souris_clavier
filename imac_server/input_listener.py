from evdev import InputDevice, ecodes
import select

KEYBOARD_DEVICE = "/dev/input/event12"
MOUSE_DEVICE = "/dev/input/event3"


def send_message(connection, message):
    connection.sendall((message + "\n").encode("utf-8"))


def start_input_listener(connection):
    keyboard = InputDevice(KEYBOARD_DEVICE)
    mouse = InputDevice(MOUSE_DEVICE)

    print("Clavier : {}".format(keyboard.name))
    print("Souris : {}".format(mouse.name))
    print("Transmission clavier + souris...")

    devices = [keyboard, mouse]

    while True:

        readable, _, _ = select.select(devices, [], [])

        mouse_x = 0
        mouse_y = 0
        mouse_wheel = 0

        for device in readable:

            events = device.read()

            for event in events:

                # ==================================================
                # CLAVIER
                # ==================================================

                if device == keyboard:

                    if event.type != ecodes.EV_KEY:
                        continue

                    message = "K:{}:{}".format(
                        event.code,
                        event.value
                    )

                    send_message(connection, message)

                # ==================================================
                # SOURIS
                # ==================================================

                elif device == mouse:

                    # --------------------------
                    # MOUVEMENT
                    # --------------------------

                    if event.type == ecodes.EV_REL:

                        if event.code == ecodes.REL_X:
                            mouse_x += event.value

                        elif event.code == ecodes.REL_Y:
                            mouse_y += event.value

                        elif event.code == ecodes.REL_WHEEL:
                            mouse_wheel += event.value

                    # --------------------------
                    # CLICS
                    # --------------------------

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

        # ==========================================================
        # ON ENVOIE LE MOUVEMENT EN UNE FOIS
        # ==========================================================

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