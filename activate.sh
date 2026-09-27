#!/bin/bash

PROJECT_ROOT="$HOME/Documents/PROJET_SOURIS_CLAVIER"
IMAC_SERVER="$PROJECT_ROOT/imac_server/main.py"

LENOVO_IP="192.168.1.39"
COMMAND_PORT="24801"
SERVER_PORT="24800"

PID_FILE="$HOME/.projet_souris_clavier_server.pid"

echo "================================"
echo "   CLAVIER + SOURIS → LENOVO"
echo "================================"
echo

cd "$PROJECT_ROOT" || exit 1

echo "[1/4] Mise à jour GitHub..."

git pull --ff-only

if [ $? -ne 0 ]; then
    echo
    echo "ERREUR : impossible de mettre le projet à jour."
    read -p "Appuyez sur Entrée pour fermer..."
    exit 1
fi

echo "[OK] iMac à jour."
echo

echo "[2/4] Connexion au launcher Lenovo..."

READY=$(python3 -c "
import socket
import sys

try:
    s = socket.socket()
    s.settimeout(5)
    s.connect(('$LENOVO_IP', $COMMAND_PORT))
    s.sendall(b'START\n')
    response = s.recv(1024).decode().strip()
    s.close()
    print(response)
except Exception as e:
    print('ERROR:' + str(e))
    sys.exit(1)
")

if [[ "$READY" != "READY" ]]; then
    echo
    echo "ERREUR : le Lenovo n'est pas prêt."
    echo "Réponse : $READY"
    read -p "Appuyez sur Entrée pour fermer..."
    exit 1
fi

echo "[OK] Lenovo prêt."
echo

echo "[3/4] Démarrage du serveur iMac..."

sudo python3 "$IMAC_SERVER" &

SERVER_PID=$!

echo "$SERVER_PID" > "$PID_FILE"

echo "[OK] Serveur lancé (PID $SERVER_PID)."
echo

echo "Attente du port $SERVER_PORT..."

SERVER_READY=false

for i in $(seq 1 30); do

    if ss -ltn | grep -q ":$SERVER_PORT "; then
        SERVER_READY=true
        break
    fi

    sleep 0.2
done

if [ "$SERVER_READY" != true ]; then
    echo
    echo "ERREUR : le serveur iMac n'a pas ouvert le port $SERVER_PORT."

    if kill -0 "$SERVER_PID" 2>/dev/null; then
        sudo kill "$SERVER_PID" 2>/dev/null
    fi

    rm -f "$PID_FILE"

    read -p "Appuyez sur Entrée pour fermer..."
    exit 1
fi

echo "[OK] Serveur iMac disponible."
echo

echo "[4/4] Lancement du client Lenovo..."

RUNNING=$(python3 -c "
import socket
import sys

try:
    s = socket.socket()
    s.settimeout(5)
    s.connect(('$LENOVO_IP', $COMMAND_PORT))
    s.sendall(b'RUN\n')
    response = s.recv(1024).decode().strip()
    s.close()
    print(response)

    if response != 'RUNNING':
        sys.exit(1)

except Exception as e:
    print('ERROR:' + str(e))
    sys.exit(1)
")

if [[ "$RUNNING" != "RUNNING" ]]; then
    echo
    echo "ERREUR : impossible de lancer le client Lenovo."
    echo "Réponse : $RUNNING"

    if kill -0 "$SERVER_PID" 2>/dev/null; then
        sudo kill "$SERVER_PID" 2>/dev/null
    fi

    rm -f "$PID_FILE"

    read -p "Appuyez sur Entrée pour fermer..."
    exit 1
fi

echo
echo "================================"
echo "       🟢 CONNECTÉ"
echo "================================"
echo
echo "Clavier + souris actifs."
echo