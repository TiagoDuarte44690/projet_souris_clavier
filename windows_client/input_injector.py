from pynput.keyboard import Controller, Key


keyboard = Controller()


KEY_MAP = {
    1: Key.esc,
    14: Key.backspace,
    15: Key.tab,
    28: Key.enter,
    29: Key.ctrl,
    42: Key.shift,
    54: Key.shift_r,
    56: Key.alt,
    57: Key.space,
    58: Key.caps_lock,

    103: Key.up,
    108: Key.down,
    105: Key.left,
    106: Key.right,

    111: Key.delete,
    102: Key.home,
    107: Key.end,
    104: Key.page_up,
    109: Key.page_down,
}


def linux_code_to_key(code):
    if code in KEY_MAP:
        return KEY_MAP[code]

    # Linux KEY_A = 30, KEY_B = 48, etc.
    letter_codes = {
        2: "1",
        3: "2",
        4: "3",
        5: "4",
        6: "5",
        7: "6",
        8: "7",
        9: "8",
        10: "9",
        11: "0",

        30: "q",
        31: "s",
        32: "d",
        33: "f",
        34: "g",
        35: "h",
        36: "j",
        37: "k",
        38: "l",

        44: "w",
        45: "x",
        46: "c",
        47: "v",
        48: "b",
        49: "n",
        50: ",",

        16: "a",
        17: "z",
        18: "e",
        19: "r",
        20: "t",
        21: "y",
        22: "u",
        23: "i",
        24: "o",
        25: "p",
    }

    return letter_codes.get(code)


def handle_key(code, value):
    key = linux_code_to_key(code)

    if key is None:
        print("Code clavier non géré :", code)
        return

    if value == 1:
        keyboard.press(key)

    elif value == 0:
        keyboard.release(key)