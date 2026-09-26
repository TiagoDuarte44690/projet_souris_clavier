from evdev import InputDevice, ecodes

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

    # Pour l'instant, on utilise un seul processus.
    # On surveille les deux périphériques avec select().
    import select

    devices = [keyboard, mouse]

    while True:
        readable, _, _ = select.select(devices, [], [])

        for device in readable:
            for event in device.read():
                # -------------------------
                # CLAVIER
                # -------------------------
                if device == keyboard:
                    if event.type != ecodes.EV_KEY:
                        continue

                    message = "K:{}:{}".format(
                        event.code,
                        event.value
                    )

                    send_message(connection, message)

                # -------------------------
                # SOURIS
                # -------------------------
                elif device == mouse:

                    # Mouvement X/Y
                    if event.type == ecodes.EV_REL:

                        if event.code == ecodes.REL_X:
                            message = "M:X:{}".format(event.value)
                            send_message(connection, message)

                        elif event.code == ecodes.REL_Y:
                            message = "M:Y:{}".format(event.value)
                            send_message(connection, message)

                        elif event.code == ecodes.REL_WHEEL:
                            message = "M:W:{}".format(event.value)
                            send_message(connection, message)

                    # Clics
                    elif event.type == ecodes.EV_KEY:

                        if event.code == ecodes.BTN_LEFT:
                            message = "M:L:{}".format(event.value)
                            send_message(connection, message)

                        elif event.code == ecodes.BTN_RIGHT:
                            message = "M:R:{}".format(event.value)
                            send_message(connection, message)

                        elif event.code == ecodes.BTN_MIDDLE:
                            message = "M:C:{}".format(event.value)
                            send_message(connection, message)