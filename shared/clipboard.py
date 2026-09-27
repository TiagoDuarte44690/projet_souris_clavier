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

POLL_INTERVAL = 0.25

MAX_CLIPBOARD_SIZE = 50 * 1024 * 1024

SYSTEM = platform.system()


# ============================================================
# ÉTAT
# ============================================================

_last_local_hash = None

_last_remote_hash = None

_lock = threading.Lock()


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
            "{0}",
            [System.Drawing.Imaging.ImageFormat]::Png
        )

        $image.Dispose()
    }
}
""".format(
        temp_path.replace(
            "\\",
            "\\\\"
        )
    )

    try:

        if os.path.exists(temp_path):

            os.remove(temp_path)

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
            return None

        return data

    except Exception:

        return None


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

            file.write(data)

        script = r"""
Add-Type -AssemblyName System.Windows.Forms

$text = [System.IO.File]::ReadAllText(
    "{0}",
    [System.Text.Encoding]::UTF8
)

[System.Windows.Forms.Clipboard]::SetText(
    $text
)
""".format(
            temp_path.replace(
                "\\",
                "\\\\"
            )
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

        try:

            os.remove(
                temp_path
            )

        except Exception:
            pass

        return True

    except Exception as error:

        print(
            "[CLIPBOARD] Erreur texte Windows :",
            error
        )

        return False


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

            file.write(data)

        script = r"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$image = [System.Drawing.Image]::FromFile(
    "{0}"
)

[System.Windows.Forms.Clipboard]::SetImage(
    $image
)

$image.Dispose()
""".format(
            temp_path.replace(
                "\\",
                "\\\\"
            )
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

        try:

            os.remove(
                temp_path
            )

        except Exception:
            pass

        return True

    except Exception as error:

        print(
            "[CLIPBOARD] Erreur image Windows :",
            error
        )

        return False


# ============================================================
# LECTURE PRESSE-PAPIER LOCAL
# ============================================================

def get_local_clipboard():

    # ========================================================
    # LINUX
    # ========================================================

    if SYSTEM == "Linux":

        # On teste d'abord l'image.
        image = _linux_get_image()

        if image:

            return (
                "IMAGE",
                image
            )

        # Puis le texte.
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

        image = _windows_get_image()

        if image:

            return (
                "IMAGE",
                image
            )

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
    global _last_remote_hash

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
                # Nouveau contenu local
                # ------------------------------------------------

                if current_hash != _last_local_hash:

                    # Si ce contenu vient d'être reçu
                    # de l'autre machine, on ne le renvoie
                    # surtout pas.
                    if current_hash == _last_remote_hash:

                        _last_local_hash = current_hash

                    else:

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

    global _last_remote_hash
    global _last_local_hash

    try:

        data = base64.b64decode(
            encoded_data
        )

        if len(data) > MAX_CLIPBOARD_SIZE:

            print(
                "[CLIPBOARD] Donnée reçue trop volumineuse."
            )

            return

        current_hash = _hash_data(
            data
        )

        _last_remote_hash = current_hash

        if set_local_clipboard(
            clipboard_type,
            data
        ):

            _last_local_hash = (
                current_hash
            )

            print(
                "[CLIPBOARD] {} reçu."
                .format(
                    clipboard_type
                )
            )

        else:

            print(
                "[CLIPBOARD] Impossible de définir le presse-papier."
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