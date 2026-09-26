from network import connect_to_server, send_message


def main():
    print("================================")
    print("     KEYBOARD SHARE CLIENT")
    print("================================")

    client = connect_to_server()

    print("Le Lenovo est connecté à l'iMac.")

    send_message(client, "TEST_LAN")

    client.close()


if __name__ == "__main__":
    main()