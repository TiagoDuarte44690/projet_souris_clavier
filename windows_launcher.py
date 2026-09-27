import os
import socket
import subprocess
import sys
import threading


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

COMMAND_HOST = "0.0.0.0"
COMMAND_PORT = 24801

GITHUB_REMOTE = "origin"
GITHUB_BRANCH = "main"

MAIN_SCRIPT = os.path.join(
    PROJECT_ROOT,
    "windows_client",
    "main.py"
)


# ============================================================
# ÉTAT
# ============================================================

main_process = None
PROCESS_LOCK = threading.Lock()


# ============================================================
# GITHUB
# ============================================================

def update_project():

    print("")
    print("================================")
    print("       MISE À JOUR GITHUB")
    print("================================")

    try:

        result = subprocess.run(
            [
                "git",
                "pull",
                "--ff-only",
                GITHUB_REMOTE,
                GITHUB_BRANCH
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:

            print(
                "[GIT] Mise à jour impossible."
            )

            return False

        print(
            "[GIT] Projet à jour."
        )

        return True

    except Exception as error:

        print(
            "[GIT] Erreur :",
            error
        )

        return False


# ============================================================
# LANCEMENT DU CLIENT
# ============================================================

def start_main():

    global main_process

    with PROCESS_LOCK:

        if main_process is not None:

            if main_process.poll() is None:

                print(
                    "[LAUNCHER] Le client est déjà lancé."
                )

                return

        print("")
        print("================================")
        print("       LANCEMENT CLIENT")
        print("================================")

        try:

            main_process = subprocess.Popen(
                [
                    sys.executable,
                    MAIN_SCRIPT
                ],
                cwd=PROJECT_ROOT
            )

            print(
                "[LAUNCHER] main.py lancé. PID : {}".format(
                    main_process.pid
                )
            )

        except Exception as error:

            print(
                "[LAUNCHER] Impossible de lancer main.py :",
                error
            )


# ============================================================
# TRAITEMENT DES COMMANDES
# ============================================================

def handle_command(connection):

    try:

        data = connection.recv(1024)

        if not data:
            return

        command = data.decode(
            "utf-8",
            errors="replace"
        ).strip()

        print(
            "[LAUNCHER] Commande reçue : {}".format(
                command
            )
        )

        # ----------------------------------------------------
        # START
        # ----------------------------------------------------
        #
        # START = seulement mise à jour + préparation.
        # On NE lance PAS encore main.py.
        #
        if command == "START":

            print(
                "[LAUNCHER] START demandé."
            )

            if not update_project():

                connection.sendall(
                    b"UPDATE_ERROR\n"
                )

                return

            connection.sendall(
                b"READY\n"
            )

            return

        # ----------------------------------------------------
        # RUN
        # ----------------------------------------------------
        #
        # RUN = lancer le client Windows.
        #
        if command == "RUN":

            print(
                "[LAUNCHER] RUN demandé."
            )

            start_main()

            connection.sendall(
                b"RUNNING\n"
            )

            return

        # ----------------------------------------------------
        # STOP
        # ----------------------------------------------------

        if command == "STOP":

            print(
                "[LAUNCHER] STOP demandé."
            )

            with PROCESS_LOCK:

                if main_process is not None:

                    if main_process.poll() is None:

                        main_process.terminate()

                        print(
                            "[LAUNCHER] main.py arrêté."
                        )

                    else:

                        print(
                            "[LAUNCHER] main.py n'est pas lancé."
                        )

                else:

                    print(
                        "[LAUNCHER] Aucun client actif."
                    )

            connection.sendall(
                b"STOPPED\n"
            )

            return

        # ----------------------------------------------------
        # COMMANDE INCONNUE
        # ----------------------------------------------------

        print(
            "[LAUNCHER] Commande inconnue."
        )

        connection.sendall(
            b"UNKNOWN_COMMAND\n"
        )

    except Exception as error:

        print(
            "[LAUNCHER] Erreur commande :",
            error
        )

    finally:

        try:
            connection.close()
        except Exception:
            pass


# ============================================================
# SERVEUR
# ============================================================

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
        (
            COMMAND_HOST,
            COMMAND_PORT
        )
    )

    server.listen(5)

    print("")
    print("================================")
    print("     LENOVO LAUNCHER")
    print("================================")
    print(
        "En attente sur le port {}".format(
            COMMAND_PORT
        )
    )

    while True:

        connection, address = server.accept()

        print(
            "[LAUNCHER] Connexion depuis : {}".format(
                address
            )
        )

        thread = threading.Thread(
            target=handle_command,
            args=(connection,)
        )

        thread.daemon = True
        thread.start()


# ============================================================
# PROGRAMME
# ============================================================

if __name__ == "__main__":

    start_server()