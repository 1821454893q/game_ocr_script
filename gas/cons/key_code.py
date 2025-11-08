# src/keycodes.py
from enum import Enum
import win32con


class KeyCode(Enum):
    """统一的按键代码枚举 - 内部自动转换"""

    # 系统按键
    HOME = "home"
    BACK = "back"
    MENU = "menu"
    POWER = "power"

    # 导航键
    DPAD_UP = "dpad_up"
    DPAD_DOWN = "dpad_down"
    DPAD_LEFT = "dpad_left"
    DPAD_RIGHT = "dpad_right"
    DPAD_CENTER = "dpad_center"

    # 音量键
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    VOLUME_MUTE = "volume_mute"

    # 功能键
    ENTER = "enter"
    DELETE = "delete"
    SPACE = "space"
    TAB = "tab"
    ESCAPE = "escape"
    CAPS_LOCK = "caps_lock"

    # 数字键
    NUM_0 = "0"
    NUM_1 = "1"
    NUM_2 = "2"
    NUM_3 = "3"
    NUM_4 = "4"
    NUM_5 = "5"
    NUM_6 = "6"
    NUM_7 = "7"
    NUM_8 = "8"
    NUM_9 = "9"

    # 字母键
    A = "a"
    B = "b"
    C = "c"
    D = "d"
    E = "e"
    F = "f"
    G = "g"
    H = "h"
    I = "i"
    J = "j"
    K = "k"
    L = "l"
    M = "m"
    N = "n"
    O = "o"
    P = "p"
    Q = "q"
    R = "r"
    S = "s"
    T = "t"
    U = "u"
    V = "v"
    W = "w"
    X = "x"
    Y = "y"
    Z = "z"

    MouseDown = "mouse_left_down"
    MouseUp = "mouse_left_up"


# Android/ADB 按键映射
ANDROID_KEY_MAP = {
    KeyCode.HOME: 3,
    KeyCode.BACK: 4,
    KeyCode.MENU: 82,
    KeyCode.POWER: 26,
    KeyCode.DPAD_UP: 19,
    KeyCode.DPAD_DOWN: 20,
    KeyCode.DPAD_LEFT: 21,
    KeyCode.DPAD_RIGHT: 22,
    KeyCode.DPAD_CENTER: 23,
    KeyCode.VOLUME_UP: 24,
    KeyCode.VOLUME_DOWN: 25,
    KeyCode.ENTER: 66,
    KeyCode.DELETE: 67,
    KeyCode.SPACE: 62,
    KeyCode.TAB: 61,
    KeyCode.ESCAPE: 111,
    KeyCode.CAPS_LOCK: 115,
    # 数字键
    KeyCode.NUM_0: 7,
    KeyCode.NUM_1: 8,
    KeyCode.NUM_2: 9,
    KeyCode.NUM_3: 10,
    KeyCode.NUM_4: 11,
    KeyCode.NUM_5: 12,
    KeyCode.NUM_6: 13,
    KeyCode.NUM_7: 14,
    KeyCode.NUM_8: 15,
    KeyCode.NUM_9: 16,
    # 字母键
    KeyCode.A: 29,
    KeyCode.B: 30,
    KeyCode.C: 31,
    KeyCode.D: 32,
    KeyCode.E: 33,
    KeyCode.F: 34,
    KeyCode.G: 35,
    KeyCode.H: 36,
    KeyCode.I: 37,
    KeyCode.J: 38,
    KeyCode.K: 39,
    KeyCode.L: 40,
    KeyCode.M: 41,
    KeyCode.N: 42,
    KeyCode.O: 43,
    KeyCode.P: 44,
    KeyCode.Q: 45,
    KeyCode.R: 46,
    KeyCode.S: 47,
    KeyCode.T: 48,
    KeyCode.U: 49,
    KeyCode.V: 50,
    KeyCode.W: 51,
    KeyCode.X: 52,
    KeyCode.Y: 53,
    KeyCode.Z: 54,
}

# Windows 虚拟键映射
WINDOWS_KEY_MAP = {
    KeyCode.HOME: 0x24,  # VK_HOME
    KeyCode.BACK: 0x08,  # VK_BACK
    KeyCode.MENU: 0x12,  # VK_MENU (ALT)
    KeyCode.POWER: 0x5B,  # VK_LWIN
    KeyCode.DPAD_UP: 0x26,  # VK_UP
    KeyCode.DPAD_DOWN: 0x28,  # VK_DOWN
    KeyCode.DPAD_LEFT: 0x25,  # VK_LEFT
    KeyCode.DPAD_RIGHT: 0x27,  # VK_RIGHT
    KeyCode.DPAD_CENTER: 0x0D,  # VK_RETURN
    KeyCode.VOLUME_UP: 0xAF,  # VK_VOLUME_UP
    KeyCode.VOLUME_DOWN: 0xAE,  # VK_VOLUME_DOWN
    KeyCode.VOLUME_MUTE: 0xAD,  # VK_VOLUME_MUTE
    KeyCode.ENTER: 0x0D,  # VK_RETURN
    KeyCode.DELETE: 0x2E,  # VK_DELETE
    KeyCode.SPACE: 0x20,  # VK_SPACE
    KeyCode.TAB: 0x09,  # VK_TAB
    KeyCode.ESCAPE: 0x1B,  # VK_ESCAPE
    KeyCode.CAPS_LOCK: 0x14,  # VK_CAPITAL
    # 数字键
    KeyCode.NUM_0: win32con.VK_NUMPAD0,
    KeyCode.NUM_1: win32con.VK_NUMPAD1,
    KeyCode.NUM_2: win32con.VK_NUMPAD2,
    KeyCode.NUM_3: win32con.VK_NUMPAD3,
    KeyCode.NUM_4: win32con.VK_NUMPAD4,
    KeyCode.NUM_5: win32con.VK_NUMPAD5,
    KeyCode.NUM_6: win32con.VK_NUMPAD6,
    KeyCode.NUM_7: win32con.VK_NUMPAD7,
    KeyCode.NUM_8: win32con.VK_NUMPAD8,
    KeyCode.NUM_9: win32con.VK_NUMPAD9,
    # 字母键 - 使用字符的ASCII值（大写）
    KeyCode.A: 0x41,
    KeyCode.B: 0x42,
    KeyCode.C: 0x43,
    KeyCode.D: 0x44,
    KeyCode.E: 0x45,
    KeyCode.F: 0x46,
    KeyCode.G: 0x47,
    KeyCode.H: 0x48,
    KeyCode.I: 0x49,
    KeyCode.J: 0x4A,
    KeyCode.K: 0x4B,
    KeyCode.L: 0x4C,
    KeyCode.M: 0x4D,
    KeyCode.N: 0x4E,
    KeyCode.O: 0x4F,
    KeyCode.P: 0x50,
    KeyCode.Q: 0x51,
    KeyCode.R: 0x52,
    KeyCode.S: 0x53,
    KeyCode.T: 0x54,
    KeyCode.U: 0x55,
    KeyCode.V: 0x56,
    KeyCode.W: 0x57,
    KeyCode.X: 0x58,
    KeyCode.Y: 0x59,
    KeyCode.Z: 0x5A,
}


def get_android_keycode(key: KeyCode) -> int:
    """获取Android对应的按键代码"""
    return ANDROID_KEY_MAP.get(key, 0)


def get_windows_keycode(key: KeyCode) -> int:
    """获取Windows对应的虚拟键代码"""
    return WINDOWS_KEY_MAP.get(key, 0)


# pydirectinput 键名映射（直接使用字符串键名）
PYDIRECTINPUT_KEY_MAP = {
    KeyCode.HOME: "home",
    KeyCode.BACK: "backspace",  # pydirectinput中没有back，使用backspace
    KeyCode.MENU: "alt",
    KeyCode.POWER: "win",
    KeyCode.DPAD_UP: "up",
    KeyCode.DPAD_DOWN: "down",
    KeyCode.DPAD_LEFT: "left",
    KeyCode.DPAD_RIGHT: "right",
    KeyCode.DPAD_CENTER: "enter",
    KeyCode.VOLUME_UP: "volumeup",
    KeyCode.VOLUME_DOWN: "volumedown",
    KeyCode.VOLUME_MUTE: "volumemute",
    KeyCode.ENTER: "enter",
    KeyCode.DELETE: "delete",
    KeyCode.SPACE: "space",
    KeyCode.TAB: "tab",
    KeyCode.ESCAPE: "escape",
    KeyCode.CAPS_LOCK: "capslock",
    # 数字键
    KeyCode.NUM_0: "0",
    KeyCode.NUM_1: "1",
    KeyCode.NUM_2: "2",
    KeyCode.NUM_3: "3",
    KeyCode.NUM_4: "4",
    KeyCode.NUM_5: "5",
    KeyCode.NUM_6: "6",
    KeyCode.NUM_7: "7",
    KeyCode.NUM_8: "8",
    KeyCode.NUM_9: "9",
    # 字母键
    KeyCode.A: "a",
    KeyCode.B: "b",
    KeyCode.C: "c",
    KeyCode.D: "d",
    KeyCode.E: "e",
    KeyCode.F: "f",
    KeyCode.G: "g",
    KeyCode.H: "h",
    KeyCode.I: "i",
    KeyCode.J: "j",
    KeyCode.K: "k",
    KeyCode.L: "l",
    KeyCode.M: "m",
    KeyCode.N: "n",
    KeyCode.O: "o",
    KeyCode.P: "p",
    KeyCode.Q: "q",
    KeyCode.R: "r",
    KeyCode.S: "s",
    KeyCode.T: "t",
    KeyCode.U: "u",
    KeyCode.V: "v",
    KeyCode.W: "w",
    KeyCode.X: "x",
    KeyCode.Y: "y",
    KeyCode.Z: "z",
}


def get_pydirectinput_keyname(key: KeyCode) -> str:
    """获取pydirectinput对应的键名"""
    return PYDIRECTINPUT_KEY_MAP.get(key, "")
