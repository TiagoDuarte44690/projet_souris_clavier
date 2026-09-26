from network import connect_to_server
from input_injector import handle_key
from mouse_injector import handle_mouse, handle_click, move_to


LENOVO_WIDTH = 1536
LENOVO_HEIGHT = 864

IMAC_WIDTH = 1920
IMAC_HEIGHT = 1200


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

                # ========================================================
                # BASCULEMENT DE MACHINE
                # ========================================================

                if parts[0] == "SWITCH":

                    if (
                        len(parts) >= 4
                        and parts[1] == "LENOVO"
                    ):

                        x_imac = int(parts[2])
                        y_imac = int(parts[3])

                        # Conversion de la position verticale
                        # iMac 1920x1200 -> Lenovo 1536x864
                        y_lenovo = int(
                            y_imac
                            * (LENOVO_HEIGHT - 1)
                            / (IMAC_HEIGHT - 1)
                        )

                        print(
                            ">>> BASCULEMENT VERS LENOVO : "
                            "iMac ({}, {}) -> "
                            "Lenovo ({}, {})".format(
                                x_imac,
                                y_imac,
                                5,
                                y_lenovo
                            )
                        )

                        # Positionner la souris près du bord gauche
                        move_to(
                            5,
                            y_lenovo
                        )

                    continue

                # ========================================================
                # CLAVIER
                # ========================================================

                if parts[0] == "K":

                    code = int(parts[1])
                    value = int(parts[2])

                    handle_key(
                        code,
                        value
                    )

                # ========================================================
                # SOURIS
                # ========================================================

                elif parts[0] == "M":

                    action = parts[1]
                    value = int(parts[2])

                    if action in (
                        "X",
                        "Y",
                        "W"
                    ):

                        handle_mouse(
                            action,
                            value
                        )

                    elif action in (
                        "L",
                        "R",
                        "C"
                    ):

                        handle_click(
                            action,
                            value
                        )

            except (ValueError, IndexError):

                print(
                    "Donnée invalide :",
                    repr(line)
                )


if __name__ == "__main__":
    main()