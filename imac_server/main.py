from network import start_server
from input_listener import start_input_listener


def main():
    server, connection = start_server()

    try:
        start_input_listener(connection)
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
    finally:
        connection.close()
        server.close()


if __name__ == "__main__":
    main()