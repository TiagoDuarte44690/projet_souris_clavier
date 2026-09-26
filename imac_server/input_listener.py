from evdev import InputDevice, ecodes
import select
import subprocess


KEYBOARD_DEVICE = "/dev/input/event12"
MOUSE_DEVICE = "/dev/input/event3"

IMAC_WIDTH = 1920
IMAC_HEIGHT = 1200

EDGE_THRESHOLD = 5

ACTIVE_MACHINE = "IMAC"


# ============================================================
# RÉSEAU
# ============================================================

def send_message(connection, message):
    connection.sendall(
        (message + "\n").encode("utf-8")
    )


# ============================================================
# SOURIS iMAC
# ============================================================

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


# ============================================================
# CAPTURE DES PÉRIPHÉRIQUES
# ============================================================

def grab_devices(keyboard, mouse):

    try:

        keyboard.grab()

        print("Clavier iMac capturé.")

    except Exception as error:

        print(
            "Impossible de capturer le clavier :",
            error
        )

    try:

        mouse.grab()

        print("Souris iMac capturée.")

    except Exception as error:

        print(
            "Impossible de capturer la souris :",
            error
        )


def ungrab_devices(keyboard, mouse):

    try:

        keyboard.ungrab()

        print("Clavier iMac libéré.")

    except Exception as error:

        print(
            "Impossible de libérer le clavier :",
            error
        )

    try:

        mouse.ungrab()

        print("Souris iMac libérée.")

    except Exception as error:

        print(
            "Impossible de libérer la souris :",
            error
        )


# ============================================================
# iMAC → LENOVO
# ============================================================

def switch_to_lenovo(
    connection,
    keyboard,
    mouse,
    y
):

    global ACTIVE_MACHINE

    if ACTIVE_MACHINE == "LENOVO":
        return

    print("")
    print("================================")
    print(">>> PASSAGE VERS LENOVO")
    print("================================")

    # Capture du clavier et de la souris.
    grab_devices(
        keyboard,
        mouse
    )

    # Le curseur iMac reste au bord droit.
    move_local_mouse(
        IMAC_WIDTH - 1,
        y
    )

    ACTIVE_MACHINE = "LENOVO"

    # Envoi de la position Y au Lenovo.
    send_message(
        connection,
        "SWITCH:LENOVO:{}".format(y)
    )

    print("Machine active : LENOVO")


# ============================================================
# LENOVO → iMAC
# ============================================================

def switch_to_imac(
    keyboard,
    mouse,
    y
):

    global ACTIVE_MACHINE

    if ACTIVE_MACHINE == "IMAC":
        return

    print("")
    print("================================")
    print(">>> RETOUR VERS IMAC")
    print("================================")

    # Place le curseur iMac au bord droit
    # avant de rendre le contrôle à GNOME.
    move_local_mouse(
        IMAC_WIDTH - 2,
        y
    )

    # Très important :
    # GNOME récupère à nouveau les périphériques.
    ungrab_devices(
        keyboard,
        mouse
    )

    ACTIVE_MACHINE = "IMAC"

    print("Machine active : IMAC")


# ============================================================
# MESSAGE REÇU DU LENOVO
# ============================================================

def process_server_message(
    line,
    keyboard,
    mouse
):

    if not line:
        return

    parts = line.split(":")

    try:

        # ========================================================
        # SWITCH
        # ========================================================

        if parts[0] == "SWITCH":

            # ----------------------------------------------------
            # LENOVO → iMAC
            # ----------------------------------------------------

            if (
                len(parts) >= 2
                and parts[1] == "IMAC"
            ):

                if len(parts) >= 3:

                    y_lenovo = int(
                        parts[2]
                    )

                    # Conversion :
                    #
                    # Lenovo : 864 px
                    # iMac   : 1200 px

                    y_imac = int(
                        y_lenovo
                        * (IMAC_HEIGHT - 1)
                        / (864 - 1)
                    )

                else:

                    y_imac = IMAC_HEIGHT // 2

                switch_to_imac(
                    keyboard,
                    mouse,
                    y_imac
                )

            return

    except (
        ValueError,
        IndexError
    ) as error:

        print(
            "Message invalide :",
            repr(line),
            error
        )


# ============================================================
# BOUCLE PRINCIPALE
# ============================================================

def start_input_listener(connection):

    global ACTIVE_MACHINE

    keyboard = InputDevice(
        KEYBOARD_DEVICE
    )

    mouse = InputDevice(
        MOUSE_DEVICE
    )

    print("")
    print("================================")
    print("     KEYBOARD + MOUSE SHARE")
    print("================================")
    print("")
    print("Clavier : {}".format(
        keyboard.name
    ))
    print("Souris  : {}".format(
        mouse.name
    ))
    print("")
    print("iMac   : 1920 x 1200")
    print("Lenovo : 1536 x 864")
    print("")
    print("Machine active : IMAC")
    print("================================")
    print("")

    devices = [
        keyboard,
        mouse
    ]

    # Buffer pour les messages Lenovo.
    server_buffer = ""

    while True:

        # On écoute simultanément :
        #
        # - clavier
        # - souris
        # - socket réseau
        #
        # C'est ce qui permet au Lenovo
        # de demander le retour vers l'iMac.

        readable, _, _ = select.select(
            devices + [connection],
            [],
            []
        )

        mouse_x = 0
        mouse_y = 0
        mouse_wheel = 0

        for device in readable:

            # ====================================================
            # MESSAGE RÉSEAU
            # ====================================================

            if device == connection:

                data = connection.recv(
                    4096
                )

                if not data:

                    print(
                        "Connexion Lenovo fermée."
                    )

                    return

                server_buffer += data.decode(
                    "utf-8"
                )

                while "\n" in server_buffer:

                    line, server_buffer = (
                        server_buffer.split(
                            "\n",
                            1
                        )
                    )

                    process_server_message(
                        line,
                        keyboard,
                        mouse
                    )

                continue

            # ====================================================
            # ÉVÉNEMENTS PÉRIPHÉRIQUE
            # ====================================================

            events = device.read()

            for event in events:

                # =================================================
                # CLAVIER
                # =================================================

                if device == keyboard:

                    if event.type != ecodes.EV_KEY:
                        continue

                    # Le clavier n'est envoyé au Lenovo
                    # que lorsque Lenovo est actif.

                    if ACTIVE_MACHINE == "LENOVO":

                        send_message(
                            connection,
                            "K:{}:{}".format(
                                event.code,
                                event.value
                            )
                        )

                # =================================================
                # SOURIS
                # =================================================

                elif device == mouse:

                    if event.type == ecodes.EV_REL:

                        if event.code == ecodes.REL_X:

                            mouse_x += event.value

                        elif event.code == ecodes.REL_Y:

                            mouse_y += event.value

                        elif event.code == ecodes.REL_WHEEL:

                            mouse_wheel += event.value

                    elif event.type == ecodes.EV_KEY:

                        # Les clics ne sont envoyés
                        # que lorsque Lenovo est actif.

                        if ACTIVE_MACHINE != "LENOVO":
                            continue

                        if event.code == ecodes.BTN_LEFT:

                            send_message(
                                connection,
                                "M:L:{}".format(
                                    event.value
                                )
                            )

                        elif event.code == ecodes.BTN_RIGHT:

                            send_message(
                                connection,
                                "M:R:{}".format(
                                    event.value
                                )
                            )

                        elif event.code == ecodes.BTN_MIDDLE:

                            send_message(
                                connection,
                                "M:C:{}".format(
                                    event.value
                                )
                            )

        # ========================================================
        # MOUVEMENTS → LENOVO
        # ========================================================

        if ACTIVE_MACHINE == "LENOVO":

            if mouse_x != 0:

                send_message(
                    connection,
                    "M:X:{}".format(
                        mouse_x
                    )
                )

            if mouse_y != 0:

                send_message(
                    connection,
                    "M:Y:{}".format(
                        mouse_y
                    )
                )

            if mouse_wheel != 0:

                send_message(
                    connection,
                    "M:W:{}".format(
                        mouse_wheel
                    )
                )

        # ========================================================
        # DÉTECTION BORD DROIT iMAC
        # ========================================================

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
                    "Erreur position souris :",
                    error
                )