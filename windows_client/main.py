from network import connect_to_server
from input_injector import key_down, key_up


def main():
    print("================================")
    print("     KEYBOARD SHARE CLIENT")
    print("================================")

    client = connect_to_server()

    print("Le Lenovo est connecté à l'iMac.")
    print("En attente des touches...")

    while True:
        data = client.recv(1024)

        if not data:
            print("Connexion fermée par l'iMac.")
            break

        print("Données reçues :", data)


if __name__ == "__main__":
    main()