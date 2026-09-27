import os
import sys
import threading
import time


# ============================================================
# RACINE DU PROJET
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT
    )


# ============================================================
# IMPORTS
# ============================================================

from network import (
    connect_to_server,
    send_line
)

from input_injector import (
    handle_key
)

from mouse_injector import (
    handle_mouse,
    handle_mouse_xy,
    handle_click,
    move_to,
    get_position
)

from shared.clipboard import (
    start_clipboard_watcher,
    receive_clipboard
)


# ============================================================
# CONFIGURATION
# ============================================================

LENOVO_WIDTH = 1536
LENOVO_HEIGHT = 864

IMAC_HEIGHT = 1200


ACTIVE_MACHINE = False


# ============================================================
# LENOVO → iMAC
# ============================================================

def send_switch_to_imac(
    client
):

    global ACTIVE_MACHINE

    if not ACTIVE_MACHINE:
        return

    try:

        x, y = get_position()

        print("")
        print("================================")
        print(">>> BORD GAUCHE LENOVO")
        print(">>> RETOUR VERS IMAC")
        print("================================")

        send_line(
            client,
            "SWITCH:IMAC:{}".format(
                y
            )
        )

        ACTIVE_MACHINE = False

        # ----------------------------------------------------
        # On éloigne le curseur du bord.
        # ----------------------------------------------------

        move_to(
            5,
            y
        )

    except Exception as error:

        print(
            "Erreur envoi SWITCH:IMAC :",
            error
        )


# ============================================================
# SURVEILLANCE BORD GAUCHE
# ============================================================

def monitor_mouse_edge(
    client
):

    global ACTIVE_MACHINE

    while True:

        time.sleep(
            0.005
        )

        if not ACTIVE_MACHINE:
            continue

        try:

            x, y = get_position()

            if x <= 0:

                send_switch_to_imac(
                    client
                )

        except Exception as error:

            print(
                "Erreur surveillance souris :",
                error
            )


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():

    global ACTIVE_MACHINE

    print("================================")
    print("     KEYBOARD SHARE CLIENT")
    print("================================")

    client = connect_to_server()

    print("")
    print(
        "Le Lenovo est connecté à l'iMac."
    )
    print(
        "Mode souris haute performance."
    )
    print("")

    # ========================================================
    # PRESSE-PAPIER
    # ========================================================

    start_clipboard_watcher(
        client,
        send_line
    )

    # ========================================================
    # THREAD BORD GAUCHE
    # ========================================================

    edge_thread = threading.Thread(
        target=monitor_mouse_edge,
        args=(client,),
        daemon=True
    )

    edge_thread.start()

    # ========================================================
    # RÉCEPTION
    # ========================================================

    buffer = ""

    while True:

        data = client.recv(
            4096
        )

        if not data:

            print(
                "Connexion fermée par l'iMac."
            )

            break

        buffer += data.decode(
            "utf-8"
        )

        while "\n" in buffer:

            line, buffer = (
                buffer.split(
                    "\n",
                    1
                )
            )

            if not line:
                continue

            try:

                # =================================================
                # PRESSE-PAPIER
                #
                # IMPORTANT :
                # Le presse-papier fonctionne indépendamment
                # de ACTIVE_MACHINE.
                # =================================================

                if line.startswith("CLIP:"):

                    clip_parts = line.split(
                        ":",
                        2
                    )

                    if len(clip_parts) == 3:

                        clipboard_type = (
                            clip_parts[1]
                        )

                        encoded_data = (
                            clip_parts[2]
                        )

                        print(
                            "[CLIPBOARD] {} reçu.".format(
                                clipboard_type
                            )
                        )

                        receive_clipboard(
                            clipboard_type,
                            encoded_data
                        )

                    continue

                # =================================================
                # AUTRES MESSAGES
                # =================================================

                parts = line.split(":")

                # =================================================
                # SWITCH
                # =================================================

                if parts[0] == "SWITCH":

                    if (
                        len(parts) >= 2
                        and parts[1] == "LENOVO"
                    ):

                        if len(parts) >= 3:

                            y_imac = int(
                                parts[2]
                            )

                            y_lenovo = int(
                                y_imac
                                * (LENOVO_HEIGHT - 1)
                                / (IMAC_HEIGHT - 1)
                            )

                        else:

                            y_lenovo = (
                                LENOVO_HEIGHT // 2
                            )

                        print(
                            ">>> PASSAGE LENOVO"
                        )

                        move_to(
                            5,
                            y_lenovo
                        )

                        ACTIVE_MACHINE = True

                    continue

                # =================================================
                # CLAVIER
                # =================================================

                if parts[0] == "K":

                    if not ACTIVE_MACHINE:
                        continue

                    code = int(
                        parts[1]
                    )

                    value = int(
                        parts[2]
                    )

                    handle_key(
                        code,
                        value
                    )

                # =================================================
                # SOURIS
                # =================================================

                elif parts[0] == "M":

                    if not ACTIVE_MACHINE:
                        continue

                    action = parts[1]

                    # ---------------------------------------------
                    # XY GROUPÉ
                    # ---------------------------------------------

                    if action == "XY":

                        dx = int(
                            parts[2]
                        )

                        dy = int(
                            parts[3]
                        )

                        handle_mouse_xy(
                            dx,
                            dy
                        )

                    # ---------------------------------------------
                    # MOLETTE
                    # ---------------------------------------------

                    elif action == "W":

                        value = int(
                            parts[2]
                        )

                        handle_mouse(
                            "W",
                            value
                        )

                    # ---------------------------------------------
                    # CLICS
                    # ---------------------------------------------

                    elif action in (
                        "L",
                        "R",
                        "C"
                    ):

                        value = int(
                            parts[2]
                        )

                        handle_click(
                            action,
                            value
                        )

            except (
                ValueError,
                IndexError
            ):

                print(
                    "Donnée invalide :",
                    repr(line)
                )


if __name__ == "__main__":

    main()