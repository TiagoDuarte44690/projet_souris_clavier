import socket
import threading


# ============================================================
# CONFIGURATION
# ============================================================

SERVER_HOST = "192.168.1.188"
SERVER_PORT = 24800


# ============================================================
# VERROU D'ENVOI
# ============================================================

SEND_LOCK = threading.Lock()


# ============================================================
# CONNEXION
# ============================================================

def connect_to_server():

    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    client.setsockopt(
        socket.IPPROTO_TCP,
        socket.TCP_NODELAY,
        1
    )

    print(
        "Connexion à l'iMac {}:{}...".format(
            SERVER_HOST,
            SERVER_PORT
        )
    )

    client.connect(
        (
            SERVER_HOST,
            SERVER_PORT
        )
    )

    print(
        "Connexion TCP établie."
    )

    print(
        "TCP_NODELAY activé."
    )

    return client


# ============================================================
# ENVOI D'UNE LIGNE
# ============================================================

def send_line(
    connection,
    message
):

    data = (
        message + "\n"
    ).encode(
        "utf-8"
    )

    with SEND_LOCK:

        connection.sendall(
            data
        )