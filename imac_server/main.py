from network import start_server


def main():
    server, connection = start_server()

    connection.close()
    server.close()


if __name__ == "__main__":
    main()