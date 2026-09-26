from network import connect_to_server
from input_injector import handle_key
from mouse_injector import handle_mouse, handle_click


def main():
    print("================================")
    print("     KEYBOARD SHARE CLIENT")
    print("================================")

    client = connect_to_server()

    print("Le Lenovo est connecté à l'iMac.")
    print("Clavier + souris distants actifs.")

    buffer = ""

    while True:

        data = client.recv(4096)

        if not data:
            print("Connexion fermée par l'iMac.")
            break

        buffer += data.decode("utf-8")

        while "\n" in buffer:

            line, buffer = buffer.split("\n", 1)

            if not line:
                continue

            parts = line.split(":")

            try:

                # =========================
                # CLAVIER
                # K:code:value
                # =========================

                if parts[0] == "K":

                    code = int(parts[1])
                    value = int(parts[2])

                    handle_key(code, value)

                # =========================
                # SOURIS
                # M:X:value
                # M:Y:value
                # M:W:value
                # =========================

                elif parts[0] == "M":

                    action = parts[1]
                    value = int(parts[2])

                    if action in ("X", "Y", "W"):
                        handle_mouse(action, value)

                    elif action in ("L", "R", "C"):
                        handle_click(action, value)

            except (ValueError, IndexError):

                print(
                    "Donnée invalide :",
                    repr(line)
                )


if __name__ == "__main__":
    main()