import base64
import hashlib
import os
import platform
import subprocess
import tempfile
import threading
import time


# ============================================================
# CONFIGURATION
# ============================================================

POLL_INTERVAL = 0.50

MAX_CLIPBOARD_SIZE = 50 * 1024 * 1024

SYSTEM = platform.system()


# ============================================================
# ÉTAT
# ============================================================

_last_local_hash = None

# Hash du dernier contenu reçu depuis l'autre machine.
#
# Il sert uniquement à empêcher un effet miroir :
#
# iMac → Lenovo → iMac → Lenovo → ...
#
_ignore_next_hash = None

# Windows possède un compteur natif du presse-papier.
# Cela permet d'éviter de lancer PowerShell toutes les
# 0,5 seconde lorsque rien n'a changé.
_last_windows_sequence = None


# ============================================================
# OUTIL : HASH
# ============================================================

def _hash_data(data):

    return hashlib.sha256(
        data
    ).hexdigest()


# ============================================================
# LINUX
# ============================================================

def _linux_get_text():

    try:

        result = subprocess.check_output(
            [
                "xclip",
                "-selection",
                "clipboard",
                "-o",
                "-t",
                "UTF8_STRING"
            ],
            stderr=subprocess.DEVNULL
        )

        if not result:

            return None

        return result

    except Exception:

        return None


def _linux_get_image():

    try:

        result = subprocess.check_output(
            [
                "xclip",
                "-selection",
                "clipboard",
                "-o",
                "-t",
                "image/png"
            ],
            stderr=subprocess.DEVNULL
        )

        if not result:

            return None

        if len(result) > MAX_CLIPBOARD_SIZE:

            print(
                "[CLIPBOARD] Image trop volumineuse : {} Mo".format(
                    round(
                        len(result) / 1024 / 1024,
                        1
                    )
                )
            )

            return None

        return result

    except Exception:

        return None


def _linux_set_text(data):

    try:

        process = subprocess.Popen(
            [
                "xclip",
                "-selection",
                "clipboard",
                "-t",
                "UTF8_STRING",
                "-i"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        process.communicate(
            data
        )

        return True

    except Exception as error:

        print(
            "[CLIPBOARD] Erreur texte Linux :",
            error
        )

        return False


def _linux_set_image(data):

    try:

        process = subprocess.Popen(
            [
                "xclip",
                "-selection",
                "clipboard",
                "-t",
                "image/png",
                "-i"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        process.communicate(
            data
        )

        return True

    except Exception as error:

        print(
            "[CLIPBOARD] Erreur image Linux :",
            error
        )

        return False


# ============================================================
# WINDOWS
# ============================================================

def _windows_clipboard_changed():

    global _last_windows_sequence

    try:

        import ctypes

        user32 = ctypes.windll.user32

        sequence = user32.GetClipboardSequenceNumber()

        if sequence == 0:

            return True

        if sequence == _last_windows_sequence:

            return False

        _last_windows_sequence = sequence

        return True

    except Exception:

        # Si l'API Windows n'est pas disponible,
        # on laisse la surveillance fonctionner normalement.
        return True


# ============================================================
# WINDOWS : LECTURE TEXTE
# ============================================================

def _windows_get_text():

    script = r"""
Add-Type -AssemblyName System.Windows.Forms

if ([System.Windows.Forms.Clipboard]::ContainsText()) {

    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

    [System.Windows.Forms.Clipboard]::GetText()
}
"""

    try:

        result = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script
            ],
            stderr=subprocess.DEVNULL
        )

        if not result:

            return None

        return result

    except Exception:

        return None


# ============================================================
# WINDOWS : LECTURE IMAGE
# ============================================================

def _windows_get_image():

    temp_path = os.path.join(
        tempfile.gettempdir(),
        "keyboard_share_clipboard.png"
    )

    script = r"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

if ([System.Windows.Forms.Clipboard]::ContainsImage()) {

    $image = [System.Windows.Forms.Clipboard]::GetImage()

    if ($null -ne $image) {

        $image.Save(
            "__CLIPBOARD_TEMP_PATH__",
            [System.Drawing.Imaging.ImageFormat]::Png
        )

        $image.Dispose()
    }
}
"""

    # --------------------------------------------------------
    # IMPORTANT
    #
    # On ne fait PAS .format(...) ici.
    #
    # Le script PowerShell contient lui-même des accolades.
    # On remplace uniquement notre marqueur.
    # --------------------------------------------------------

    script = script.replace(
        "__CLIPBOARD_TEMP_PATH__",
        temp_path
    )

    try:

        if os.path.exists(temp_path):

            os.remove(
                temp_path
            )

        subprocess.call(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if not os.path.exists(temp_path):

            return None

        with open(
            temp_path,
            "rb"
        ) as file:

            data = file.read()

        try:

            os.remove(
                temp_path
            )

        except Exception:

            pass

        if not data:

            return None

        if len(data) > MAX_CLIPBOARD_SIZE:

            print(
                "[CLIPBOARD] Image Windows trop volumineuse."
            )

            return None

        return data

    except Exception as error:

        print(
            "[CLIPBOARD] Erreur lecture image Windows :",
            error
        )

        try:

            if os.path.exists(temp_path):

                os.remove(
                    temp_path
                )

        except Exception:

            pass

        return None


# ============================================================
# WINDOWS : ÉCRITURE TEXTE
# ============================================================

def _windows_set_text(data):

    temp_path = os.path.join(
        tempfile.gettempdir(),
        "keyboard_share_clipboard.txt"
    )

    try:

        with open(
            temp_path,
            "wb"
        ) as file:

            file.write(
                data
            )

        script = r"""
Add-Type -AssemblyName System.Windows.Forms

$text = [System.IO.File]::ReadAllText(
    "__CLIPBOARD_TEMP_PATH__",
    [System.Text.Encoding]::UTF8
)

[System.Windows.Forms.Clipboard]::SetText(
    $text
)
"""

        # ----------------------------------------------------
        # Même principe :
        # surtout pas de .format(...)
        # ----------------------------------------------------

        script = script.replace(
            "__CLIPBOARD_TEMP_PATH__",
            temp_path
        )

        result = subprocess.call(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        try:

            os.remove(
                temp_path
            )

        except Exception:

            pass

        return result == 0

    except Exception as error:

        print(
            "[CLIPBOARD] Erreur texte Windows :",
            error
        )

        try:

            if os.path.exists(temp_path):

                os.remove(
                    temp_path
                )

        except Exception:

            pass

        return False


# ============================================================
# WINDOWS : ÉCRITURE IMAGE
# ============================================================

def _windows_set_image(data):

    temp_path = os.path.join(
        tempfile.gettempdir(),
        "keyboard_share_clipboard.png"
    )

    try:

        with open(
            temp_path,
            "wb"
        ) as file:

            file.write(
                data
            )

        script = r"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$image = [System.Drawing.Image]::FromFile(
    "__CLIPBOARD_TEMP_PATH__"
)

[System.Windows.Forms.Clipboard]::SetImage(
    $image
)

$image.Dispose()
"""

        # ----------------------------------------------------
        # IMPORTANT :
        # pas de .format(...)
        # ----------------------------------------------------

        script = script.replace(
            "__CLIPBOARD_TEMP_PATH__",
            temp_path
        )

        result = subprocess.call(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        try:

            os.remove(
                temp_path
            )

        except Exception:

            pass

        return result == 0

    except Exception as error:

        print(
            "[CLIPBOARD] Erreur image Windows :",
            error
        )

        try:

            if os.path.exists(temp_path):

                os.remove(
                    temp_path
                )

        except Exception:

            pass

        return False


# ============================================================
# LECTURE PRESSE-PAPIER LOCAL
# ============================================================

def get_local_clipboard():

    # ========================================================
    # LINUX
    # ========================================================

    if SYSTEM == "Linux":

        # ----------------------------------------------------
        # On teste d'abord l'image.
        # ----------------------------------------------------

        image = _linux_get_image()

        if image:

            return (
                "IMAGE",
                image
            )

        # ----------------------------------------------------
        # Puis le texte.
        # ----------------------------------------------------

        text = _linux_get_text()

        if text:

            return (
                "TEXT",
                text
            )

        return (
            None,
            None
        )

    # ========================================================
    # WINDOWS
    # ========================================================

    if SYSTEM == "Windows":

        # ----------------------------------------------------
        # Si le presse-papier n'a pas changé, inutile de
        # lancer PowerShell.
        # ----------------------------------------------------

        if not _windows_clipboard_changed():

            return (
                None,
                None
            )

        # ----------------------------------------------------
        # On teste d'abord l'image.
        # ----------------------------------------------------

        image = _windows_get_image()

        if image:

            return (
                "IMAGE",
                image
            )

        # ----------------------------------------------------
        # Puis le texte.
        # ----------------------------------------------------

        text = _windows_get_text()

        if text:

            return (
                "TEXT",
                text
            )

        return (
            None,
            None
        )

    return (
        None,
        None
    )


# ============================================================
# ÉCRITURE PRESSE-PAPIER LOCAL
# ============================================================

def set_local_clipboard(
    clipboard_type,
    data
):

    if clipboard_type == "TEXT":

        if SYSTEM == "Linux":

            return _linux_set_text(
                data
            )

        if SYSTEM == "Windows":

            return _windows_set_text(
                data
            )

    elif clipboard_type == "IMAGE":

        if SYSTEM == "Linux":

            return _linux_set_image(
                data
            )

        if SYSTEM == "Windows":

            return _windows_set_image(
                data
            )

    return False


# ============================================================
# ENVOI PRESSE-PAPIER
# ============================================================

def send_clipboard(
    connection,
    clipboard_type,
    data,
    send_function
):

    # --------------------------------------------------------
    # Protection taille
    # --------------------------------------------------------

    if len(data) > MAX_CLIPBOARD_SIZE:

        print(
            "[CLIPBOARD] Donnée trop volumineuse."
        )

        return

    # --------------------------------------------------------
    # Conversion en Base64
    # --------------------------------------------------------

    encoded = base64.b64encode(
        data
    ).decode(
        "ascii"
    )

    message = (
        "CLIP:{}:{}"
        .format(
            clipboard_type,
            encoded
        )
    )

    # --------------------------------------------------------
    # Le verrou d'envoi est géré par send_function
    # (send_line côté réseau).
    # --------------------------------------------------------

    send_function(
        connection,
        message
    )


# ============================================================
# SURVEILLANCE PRESSE-PAPIER
# ============================================================

def clipboard_watcher(
    connection,
    send_function
):

    global _last_local_hash
    global _ignore_next_hash

    print(
        "[CLIPBOARD] Surveillance activée."
    )

    while True:

        try:

            clipboard_type, data = (
                get_local_clipboard()
            )

            if (
                clipboard_type is not None
                and data is not None
            ):

                current_hash = _hash_data(
                    data
                )

                # ------------------------------------------------
                # CONTENU QUI VIENT D'ÊTRE REÇU
                #
                # On le laisse dans le presse-papier local,
                # mais on ne le renvoie pas immédiatement.
                # ------------------------------------------------

                if (
                    _ignore_next_hash is not None
                    and current_hash == _ignore_next_hash
                ):

                    _last_local_hash = current_hash

                    _ignore_next_hash = None

                # ------------------------------------------------
                # NOUVEAU CONTENU LOCAL
                # ------------------------------------------------

                elif current_hash != _last_local_hash:

                    print(
                        "[CLIPBOARD] Nouveau {} local."
                        .format(
                            clipboard_type
                        )
                    )

                    send_clipboard(
                        connection,
                        clipboard_type,
                        data,
                        send_function
                    )

                    _last_local_hash = (
                        current_hash
                    )

        except Exception as error:

            print(
                "[CLIPBOARD] Erreur surveillance :",
                error
            )

        time.sleep(
            POLL_INTERVAL
        )


# ============================================================
# RÉCEPTION PRESSE-PAPIER
# ============================================================

def receive_clipboard(
    clipboard_type,
    encoded_data
):

    global _ignore_next_hash
    global _last_local_hash

    try:

        # ----------------------------------------------------
        # Vérification du type
        # ----------------------------------------------------

        if clipboard_type not in (
            "TEXT",
            "IMAGE"
        ):

            print(
                "[CLIPBOARD] Type inconnu :",
                clipboard_type
            )

            return

        # ----------------------------------------------------
        # Décodage Base64
        # ----------------------------------------------------

        data = base64.b64decode(
            encoded_data
        )

        if not data:

            print(
                "[CLIPBOARD] Donnée vide reçue."
            )

            return

        # ----------------------------------------------------
        # Protection taille
        # ----------------------------------------------------

        if len(data) > MAX_CLIPBOARD_SIZE:

            print(
                "[CLIPBOARD] Donnée reçue trop volumineuse."
            )

            return

        # ----------------------------------------------------
        # Hash
        # ----------------------------------------------------

        current_hash = _hash_data(
            data
        )

        # ----------------------------------------------------
        # Écriture dans le presse-papier local
        # ----------------------------------------------------

        success = set_local_clipboard(
            clipboard_type,
            data
        )

        if success:

            # ------------------------------------------------
            # On indique au watcher que ce contenu vient du
            # réseau et ne doit donc pas repartir.
            # ------------------------------------------------

            _ignore_next_hash = current_hash

            _last_local_hash = current_hash

            print(
                "[CLIPBOARD] {} reçu."
                .format(
                    clipboard_type
                )
            )

        else:

            print(
                "[CLIPBOARD] Impossible de définir "
                "le presse-papier."
            )

    except Exception as error:

        print(
            "[CLIPBOARD] Erreur réception :",
            error
        )


# ============================================================
# THREAD
# ============================================================

def start_clipboard_watcher(
    connection,
    send_function
):

    thread = threading.Thread(
        target=clipboard_watcher,
        args=(
            connection,
            send_function
        ),
        daemon=True
    )

    thread.start()

    return thread