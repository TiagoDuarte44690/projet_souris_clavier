import socket


SERVER_IP = "192.168.1.188"
PORT = 24800


def connect_to_server():
    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    print("Connexion à {}:{}...".format(SERVER_IP, PORT))

    client.connect((SERVER_IP, PORT))

    print("Connexion réussie !")

    return client


def send_message(client, message):
    data = message.encode("utf-8")
    client.sendall(data)

    print("Message envoyé : {}".format(message))