from network import start_server
from input_listener import start_input_listener

from shared.clipboard import (
    start_clipboard_watcher,
    send_clipboard
)


def send_clipboard_message(
    connection,
    message
):

    send_clipboard(
        connection,
        message,
        "",
        lambda conn, msg: conn.sendall(
            (msg + "\n").encode("utf-8")
        )
    )


def main():

    server, connection = start_server()

    try:

        # ====================================================
        # PRESSE-PAPIER PARTAGÉ
        # ====================================================

        start_clipboard_watcher(
            connection,
            lambda conn, message: conn.sendall(
                (message + "\n").encode("utf-8")
            )
        )

        # ====================================================
        # CLAVIER + SOURIS
        # ====================================================

        start_input_listener(
            connection
        )

    except KeyboardInterrupt:

        print(
            "\nArrêt du serveur."
        )

    finally:

        connection.close()
        server.close()


if __name__ == "__main__":

    main()