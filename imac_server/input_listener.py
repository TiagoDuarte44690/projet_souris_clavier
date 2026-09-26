from evdev import InputDevice, ecodes


KEYBOARD_DEVICE = "/dev/input/event12"


def start_input_listener(connection):
    keyboard = InputDevice(KEYBOARD_DEVICE)

    print("Clavier détecté : {}".format(keyboard.name))
    print("Écoute des touches...")

    for event in keyboard.read_loop():

        if event.type != ecodes.EV_KEY:
            continue

        message = "{}:{}\n".format(
            event.code,
            event.value
        )

        connection.sendall(message.encode("utf-8"))

        print("Envoyé : {}".format(message.strip()))