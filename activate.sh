#!/bin/bash

PROJECT_ROOT="$HOME/Documents/PROJET_SOURIS_CLAVIER"
IMAC_SERVER="$PROJECT_ROOT/imac_server/main.py"

LENOVO_IP="192.168.1.39"
COMMAND_PORT="24801"
SERVER_PORT="24800"

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

echo "[OK] Serveur lancé (PID $SERVER_PID)."
echo

echo "Attente du port 24800..."

for i in $(seq 1 30); do

    python3 -c "
import socket
s = socket.socket()
s.settimeout(0.2)
try:
    s.connect(('127.0.0.1', $SERVER_PORT))
    s.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null

    if [ $? -eq 0 ]; then
        break
    fi

    sleep 0.2
done

echo "[OK] Serveur iMac disponible."
echo

echo "[4/4] Lancement du client Lenovo..."

python3 -c "
import socket

s = socket.socket()
s.settimeout(5)
s.connect(('$LENOVO_IP', $COMMAND_PORT))
s.sendall(b'RUN\n')
print(s.recv(1024).decode().strip())
s.close()
"

echo
echo "================================"
echo "       🟢 CONNECTÉ"
echo "================================"
echo
echo "Clavier + souris actifs."
echo