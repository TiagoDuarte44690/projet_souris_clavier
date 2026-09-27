import os
import sys
import threading


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
    start_server
)

from input_listener import (
    start_input_listener
)

from shared.clipboard import (
    start_clipboard_watcher,
    receive_clipboard
)


# ============================================================
# RÉCEPTION DES MESSAGES WINDOWS
# ============================================================

def receive_messages(
    connection
):

    buffer = ""

    print(
        "[RECEPTION] Surveillance des messages activée."
    )

    while True:

        try:

            data = connection.recv(
                65536
            )

            if not data:

                print(
                    "[RECEPTION] Connexion Windows fermée."
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

                line = line.rstrip(
                    "\r"
                )

                if not line:
                    continue

                # =================================================
                # PRESSE-PAPIER
                # =================================================

                if line.startswith(
                    "CLIP:"
                ):

                    clip_parts = line.split(
                        ":",
                        2
                    )

                    if len(clip_parts) != 3:

                        print(
                            "[CLIPBOARD] Message invalide."
                        )

                        continue

                    clipboard_type = (
                        clip_parts[1]
                    )

                    encoded_data = (
                        clip_parts[2]
                    )

                    print(
                        "[CLIPBOARD] {} reçu du Lenovo.".format(
                            clipboard_type
                        )
                    )

                    try:

                        receive_clipboard(
                            clipboard_type,
                            encoded_data
                        )

                        print(
                            "[CLIPBOARD] Presse-papier iMac mis à jour."
                        )

                    except Exception as error:

                        print(
                            "[CLIPBOARD] Erreur réception :",
                            error
                        )

                    continue

                # =================================================
                # AUTRES MESSAGES
                # =================================================

                print(
                    "[RECEPTION] Message reçu :",
                    line
                )

        except Exception as error:

            print(
                "[RECEPTION] Erreur :",
                error
            )

            break


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():

    print(
        "================================"
    )

    print(
        "     KEYBOARD SHARE SERVER"
    )

    print(
        "================================"
    )

    server, connection = start_server()

    try:

        # ========================================================
        # RÉCEPTION DES MESSAGES WINDOWS
        #
        # IMPORTANT :
        # Le thread tourne en parallèle du clavier/souris.
        # ========================================================

        receiver_thread = threading.Thread(
            target=receive_messages,
            args=(
                connection,
            ),
            daemon=True
        )

        receiver_thread.start()

        # ========================================================
        # PRESSE-PAPIER LOCAL
        #
        # iMac → Lenovo
        # ========================================================

        start_clipboard_watcher(
            connection,
            lambda conn, message: conn.sendall(
                (
                    message + "\n"
                ).encode(
                    "utf-8"
                )
            )
        )

        # ========================================================
        # CLAVIER + SOURIS
        #
        # iMac → Lenovo
        # ========================================================

        start_input_listener(
            connection
        )

    except KeyboardInterrupt:

        print(
            "\nArrêt du serveur."
        )

    finally:

        try:
            connection.close()
        except Exception:
            pass

        try:
            server.close()
        except Exception:
            pass


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":

    main()