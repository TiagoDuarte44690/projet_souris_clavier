import socket


SERVER_HOST = "192.168.1.188"
SERVER_PORT = 24800


def connect_to_server():

    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    # ========================================================
    # TCP LOW LATENCY
    # ========================================================

    client.setsockopt(
        socket.IPPROTO_TCP,
        socket.TCP_NODELAY,
        1
    )

    print(
        "Connexion à {}:{}...".format(
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
        "Connexion établie."
    )

    print(
        "TCP_NODELAY activé."
    )

    return client