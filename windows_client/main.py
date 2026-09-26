from network import connect_to_server
from input_injector import handle_key
from mouse_injector import (
    handle_mouse,
    handle_click,
    move_to,
    get_position
)

import threading
import time


LENOVO_WIDTH = 1536
LENOVO_HEIGHT = 864

ACTIVE_MACHINE = False

mouse_position_lock = threading.Lock()


def send_switch_to_imac(client):
    global ACTIVE_MACHINE

    if not ACTIVE_MACHINE:
        return

    try:

        print("================================")
        print(">>> BORD GAUCHE LENOVO")
        print(">>> RETOUR VERS IMAC")
        print("================================")

        client.sendall(
            b"SWITCH:IMAC\n"
        )

        ACTIVE_MACHINE = False

    except Exception as error:

        print(
            "Erreur envoi SWITCH:IMAC :",
            error
        )


def monitor_mouse_edge(client):

    global ACTIVE_MACHINE

    while True:

        time.sleep(0.01)

        if not ACTIVE_MACHINE:
            continue

        try:

            x, y = get_position()

            if x <= 0:

                send_switch_to_imac(
                    client
                )

                # Évite le déclenchement permanent.
                move_to(
                    5,
                    y
                )

        except Exception as error:

            print(
                "Erreur surveillance souris :",
                error
            )


def main():

    global ACTIVE_MACHINE

    print("================================")
    print("     KEYBOARD SHARE CLIENT")
    print("================================")

    client = connect_to_server()

    print("Le Lenovo est connecté à l'iMac.")
    print("En attente du passage de la souris...")

    buffer = ""

    edge_thread = threading.Thread(
        target=monitor_mouse_edge,
        args=(client,),
        daemon=True
    )

    edge_thread.start()

    while True:

        data = client.recv(4096)

        if not data:

            print(
                "Connexion fermée par l'iMac."
            )

            break

        buffer += data.decode(
            "utf-8"
        )

        while "\n" in buffer:

            line, buffer = buffer.split(
                "\n",
                1
            )

            if not line:
                continue

            parts = line.split(":")

            try:

                # ======================================================
                # CHANGEMENT DE MACHINE
                # ======================================================

                if parts[0] == "SWITCH":

                    if (
                        len(parts) >= 2
                        and parts[1] == "LENOVO"
                    ):

                        y_imac = int(
                            parts[2]
                        )

                        # Conversion verticale :
                        #
                        # iMac 1200 px
                        # Lenovo 864 px

                        y_lenovo = int(
                            y_imac
                            * (LENOVO_HEIGHT - 1)
                            / 1199
                        )

                        print(
                            ">>> PASSAGE LENOVO"
                        )

                        move_to(
                            5,
                            y_lenovo
                        )

                        ACTIVE_MACHINE = True

                    elif (
                        len(parts) >= 2
                        and parts[1] == "IMAC"
                    ):

                        print(
                            ">>> PASSAGE IMAC"
                        )

                        ACTIVE_MACHINE = False

                    continue

                # ======================================================
                # CLAVIER
                # ======================================================

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

                # ======================================================
                # SOURIS
                # ======================================================

                elif parts[0] == "M":

                    if not ACTIVE_MACHINE:
                        continue

                    action = parts[1]

                    value = int(
                        parts[2]
                    )

                    if action in (
                        "X",
                        "Y",
                        "W"
                    ):

                        handle_mouse(
                            action,
                            value
                        )

                    elif action in (
                        "L",
                        "R",
                        "C"
                    ):

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