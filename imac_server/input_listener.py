from evdev import InputDevice, ecodes

import select
import subprocess
import time


# ============================================================
# CONFIGURATION
# ============================================================

KEYBOARD_DEVICE = "/dev/input/event12"
MOUSE_DEVICE = "/dev/input/event3"

IMAC_WIDTH = 1920
IMAC_HEIGHT = 1200

LENOVO_WIDTH = 1536
LENOVO_HEIGHT = 864

EDGE_THRESHOLD = 5

# Intervalle maximum avant d'envoyer les mouvements accumulés.
# 0.002 = 2 ms.
MOUSE_FLUSH_INTERVAL = 0.002

# Vérification de la position du curseur iMac.
# On ne lance PAS xdotool à chaque événement.
EDGE_CHECK_INTERVAL = 0.015


ACTIVE_MACHINE = "IMAC"


# ============================================================
# ÉTAT PERFORMANCE
# ============================================================

last_edge_check = 0.0
last_mouse_flush = 0.0

pending_x = 0
pending_y = 0
pending_wheel = 0


# ============================================================
# RÉSEAU
# ============================================================

def send_message(connection, message):

    connection.sendall(
        (message + "\n").encode("utf-8")
    )


def send_mouse_move(
    connection,
    dx,
    dy
):

    if dx == 0 and dy == 0:
        return

    connection.sendall(
        "M:XY:{}:{}\n".format(
            dx,
            dy
        ).encode("utf-8")
    )


def send_mouse_wheel(
    connection,
    value
):

    if value == 0:
        return

    connection.sendall(
        "M:W:{}\n".format(
            value
        ).encode("utf-8")
    )


# ============================================================
# SOURIS iMAC
# ============================================================

def get_mouse_position():

    result = subprocess.check_output(
        [
            "xdotool",
            "getmouselocation",
            "--shell"
        ]
    ).decode("utf-8")

    position = {}

    for line in result.splitlines():

        if "=" not in line:
            continue

        key, value = line.split(
            "=",
            1
        )

        position[key] = int(value)

    return (
        position["X"],
        position["Y"]
    )


def move_local_mouse(x, y):

    subprocess.call(
        [
            "xdotool",
            "mousemove",
            str(int(x)),
            str(int(y))
        ]
    )


# ============================================================
# CAPTURE DES PÉRIPHÉRIQUES
# ============================================================

def grab_devices(
    keyboard,
    mouse
):

    try:

        keyboard.grab()

        print(
            "Clavier iMac capturé."
        )

    except Exception as error:

        print(
            "Impossible de capturer le clavier :",
            error
        )

    try:

        mouse.grab()

        print(
            "Souris iMac capturée."
        )

    except Exception as error:

        print(
            "Impossible de capturer la souris :",
            error
        )


def ungrab_devices(
    keyboard,
    mouse
):

    try:

        keyboard.ungrab()

        print(
            "Clavier iMac libéré."
        )

    except Exception as error:

        print(
            "Impossible de libérer le clavier :",
            error
        )

    try:

        mouse.ungrab()

        print(
            "Souris iMac libérée."
        )

    except Exception as error:

        print(
            "Impossible de libérer la souris :",
            error
        )


# ============================================================
# RESET MOUVEMENTS
# ============================================================

def reset_pending_mouse():

    global pending_x
    global pending_y
    global pending_wheel

    pending_x = 0
    pending_y = 0
    pending_wheel = 0


# ============================================================
# ENVOI MOUVEMENTS ACCUMULÉS
# ============================================================

def flush_mouse(
    connection,
    force=False
):

    global pending_x
    global pending_y
    global pending_wheel
    global last_mouse_flush

    now = time.monotonic()

    if not force:

        if (
            now - last_mouse_flush
            < MOUSE_FLUSH_INTERVAL
        ):

            return

    # --------------------------------------------------------
    # XY
    # --------------------------------------------------------

    if (
        pending_x != 0
        or pending_y != 0
    ):

        send_mouse_move(
            connection,
            pending_x,
            pending_y
        )

        pending_x = 0
        pending_y = 0

    # --------------------------------------------------------
    # MOLETTE
    # --------------------------------------------------------

    if pending_wheel != 0:

        send_mouse_wheel(
            connection,
            pending_wheel
        )

        pending_wheel = 0

    last_mouse_flush = now


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

    # Évite qu'un ancien mouvement
    # soit envoyé après le changement.
    reset_pending_mouse()

    grab_devices(
        keyboard,
        mouse
    )

    # Positionne le curseur iMac
    # au bord droit.
    move_local_mouse(
        IMAC_WIDTH - 1,
        y
    )

    ACTIVE_MACHINE = "LENOVO"

    send_message(
        connection,
        "SWITCH:LENOVO:{}".format(y)
    )

    print(
        "Machine active : LENOVO"
    )


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

    reset_pending_mouse()

    move_local_mouse(
        IMAC_WIDTH - 2,
        y
    )

    ungrab_devices(
        keyboard,
        mouse
    )

    ACTIVE_MACHINE = "IMAC"

    print(
        "Machine active : IMAC"
    )


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

        # ====================================================
        # SWITCH
        # ====================================================

        if parts[0] != "SWITCH":
            return

        if (
            len(parts) >= 2
            and parts[1] == "IMAC"
        ):

            if len(parts) >= 3:

                y_lenovo = int(
                    parts[2]
                )

                y_imac = int(
                    y_lenovo
                    * (IMAC_HEIGHT - 1)
                    / (LENOVO_HEIGHT - 1)
                )

            else:

                y_imac = (
                    IMAC_HEIGHT // 2
                )

            switch_to_imac(
                keyboard,
                mouse,
                y_imac
            )

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
    global last_edge_check
    global last_mouse_flush

    global pending_x
    global pending_y
    global pending_wheel

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
    print(
        "Clavier : {}".format(
            keyboard.name
        )
    )
    print(
        "Souris  : {}".format(
            mouse.name
        )
    )
    print("")
    print(
        "iMac   : {} x {}".format(
            IMAC_WIDTH,
            IMAC_HEIGHT
        )
    )
    print(
        "Lenovo : {} x {}".format(
            LENOVO_WIDTH,
            LENOVO_HEIGHT
        )
    )
    print("")
    print(
        "Machine active : IMAC"
    )
    print("")
    print(
        "Optimisations souris :"
    )
    print(
        "  - TCP_NODELAY"
    )
    print(
        "  - mouvements XY groupés"
    )
    print(
        "  - buffer 2 ms"
    )
    print(
        "  - xdotool limité"
    )
    print("================================")
    print("")

    devices = [
        keyboard,
        mouse
    ]

    server_buffer = ""

    last_edge_check = time.monotonic()
    last_mouse_flush = time.monotonic()

    while True:

        # ====================================================
        # SELECT
        # ====================================================

        readable, _, _ = select.select(
            devices + [connection],
            [],
            [],
            MOUSE_FLUSH_INTERVAL
        )

        # ====================================================
        # TRAITEMENT DES ÉVÉNEMENTS
        # ====================================================

        for device in readable:

            # =================================================
            # RÉSEAU
            # =================================================

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

            # =================================================
            # PÉRIPHÉRIQUE
            # =================================================

            events = device.read()

            for event in events:

                # =============================================
                # CLAVIER
                # =============================================

                if device == keyboard:

                    if event.type != ecodes.EV_KEY:
                        continue

                    if ACTIVE_MACHINE == "LENOVO":

                        send_message(
                            connection,
                            "K:{}:{}".format(
                                event.code,
                                event.value
                            )
                        )

                # =============================================
                # SOURIS
                # =============================================

                elif device == mouse:

                    # -----------------------------------------
                    # MOUVEMENT
                    # -----------------------------------------

                    if event.type == ecodes.EV_REL:

                        if ACTIVE_MACHINE != "LENOVO":
                            continue

                        if event.code == ecodes.REL_X:

                            pending_x += event.value

                        elif event.code == ecodes.REL_Y:

                            pending_y += event.value

                        elif event.code == ecodes.REL_WHEEL:

                            pending_wheel += event.value

                    # -----------------------------------------
                    # CLIC
                    # -----------------------------------------

                    elif event.type == ecodes.EV_KEY:

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

        # ====================================================
        # ENVOI DES MOUVEMENTS
        # ====================================================

        if ACTIVE_MACHINE == "LENOVO":

            flush_mouse(
                connection
            )

        else:

            reset_pending_mouse()

        # ====================================================
        # DÉTECTION BORD DROIT
        # ====================================================

        if ACTIVE_MACHINE == "IMAC":

            now = time.monotonic()

            if (
                now - last_edge_check
                >= EDGE_CHECK_INTERVAL
            ):

                last_edge_check = now

                try:

                    x, y = get_mouse_position()

                    if (
                        x
                        >= IMAC_WIDTH
                        - EDGE_THRESHOLD
                    ):

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