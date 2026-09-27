import socket


HOST = "0.0.0.0"
PORT = 24800


def start_server():

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server.bind(
        (HOST, PORT)
    )

    server.listen(1)

    print("================================")
    print("     KEYBOARD SHARE SERVER")
    print("================================")
    print("Serveur en écoute sur le port {}".format(PORT))
    print("En attente du PC Windows...")

    connection, address = server.accept()

    # ========================================================
    # TCP LOW LATENCY
    # ========================================================

    connection.setsockopt(
        socket.IPPROTO_TCP,
        socket.TCP_NODELAY,
        1
    )

    print("Connexion reçue depuis : {}".format(address))
    print("TCP_NODELAY activé.")

    return server, connection