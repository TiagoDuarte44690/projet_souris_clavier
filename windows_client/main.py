from network import connect_to_server


def main():
    print("================================")
    print("     KEYBOARD SHARE CLIENT")
    print("================================")

    client = connect_to_server()

    print("Le Lenovo est connecté à l'iMac.")

    client.close()


if __name__ == "__main__":
    main()