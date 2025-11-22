# src/erchong/cons/key_code.py
from enum import Enum
import win32con


class KeyCode(Enum):
    """统一的按键代码枚举 - 支持 Windows / Android / PyDirectInput 多平台映射"""

    # ==================== 系统按键 ====================
    HOME = "home"
    BACK = "back"           # Backspace
    MENU = "menu"           # Alt / Menu
    POWER = "power"
    WIN = "win"             # Windows 键

    # ==================== 导航键 ====================
    DPAD_UP = "dpad_up"
    DPAD_DOWN = "dpad_down"
    DPAD_LEFT = "dpad_left"
    DPAD_RIGHT = "dpad_right"
    DPAD_CENTER = "dpad_center"

    # ==================== 功能键 ====================
    ENTER = "enter"
    RETURN = "return"       # 同 ENTER
    DELETE = "delete"
    SPACE = "space"
    TAB = "tab"
    ESCAPE = "escape"
    CAPS_LOCK = "caps_lock"

    # ==================== 修饰键 ====================
    SHIFT = "shift"
    CONTROL = "ctrl"
    ALT = "alt"
    LSHIFT = "lshift"
    RSHIFT = "rshift"
    LCTRL = "lctrl"
    RCTRL = "rctrl"
    LALT = "lalt"
    RALT = "ralt"

    # ==================== 字母键 ====================
    A = "a"; B = "b"; C = "c"; D = "d"; E = "e"
    F = "f"; G = "g"; H = "h"; I = "i"; J = "j"
    K = "k"; L = "l"; M = "m"; N = "n"; O = "o"
    P = "p"; Q = "q"; R = "r"; S = "s"; T = "t"
    U = "u"; V = "v"; W = "w"; X = "x"; Y = "y"; Z = "z"

    # ==================== 主键盘区数字 ====================
    DIGIT_0 = "0"; DIGIT_1 = "1"; DIGIT_2 = "2"; DIGIT_3 = "3"
    DIGIT_4 = "4"; DIGIT_5 = "5"; DIGIT_6 = "6"; DIGIT_7 = "7"
    DIGIT_8 = "8"; DIGIT_9 = "9"

    # ==================== 小键盘数字 ====================
    NUM_0 = "num_0"; NUM_1 = "num_1"; NUM_2 = "num_2"; NUM_3 = "num_3"
    NUM_4 = "num_4"; NUM_5 = "num_5"; NUM_6 = "num_6"; NUM_7 = "num_7"
    NUM_8 = "num_8"; NUM_9 = "num_9"
    NUM_LOCK = "num_lock"
    NUM_ADD = "num_add"
    NUM_SUBTRACT = "num_subtract"
    NUM_MULTIPLY = "num_multiply"
    NUM_DIVIDE = "num_divide"
    NUM_DECIMAL = "num_decimal"
    NUM_ENTER = "num_enter"

    # ==================== F1 ~ F12 ====================
    F1 = "f1"; F2 = "f2"; F3 = "f3"; F4 = "f4"
    F5 = "f5"; F6 = "f6"; F7 = "f7"; F8 = "f8"
    F9 = "f9"; F10 = "f10"; F11 = "f11"; F12 = "f12"

    # ==================== 常用符号键 ====================
    TILDE = "tilde"         # ~
    EXCLAMATION = "!"       # !
    AT = "@"; HASH = "#"; DOLLAR = "$"
    PERCENT = "%"; CARET = "^"; AMPERSAND = "&"
    ASTERISK = "*"; LEFT_PAREN = "("; RIGHT_PAREN = ")"
    UNDERSCORE = "_"; PLUS = "+"; MINUS = "-"
    EQUALS = "="; BACKSLASH = "\\"; PIPE = "|"
    LEFT_BRACKET = "["; RIGHT_BRACKET = "]"
    LEFT_BRACE = "{"; RIGHT_BRACE = "}"
    SEMICOLON = ";"; COLON = ":"
    APOSTROPHE = "'"; QUOTE = "\""
    COMMA = ","; PERIOD = "."; SLASH = "/"; QUESTION = "?"

    # ==================== 鼠标键 ====================
    MOUSE_LEFT_DOWN = "mouse_left_down"
    MOUSE_LEFT_UP = "mouse_left_up"
    MOUSE_RIGHT_DOWN = "mouse_right_down"
    MOUSE_RIGHT_UP = "mouse_right_up"
    MOUSE_MIDDLE_DOWN = "mouse_middle_down"
    MOUSE_MIDDLE_UP = "mouse_middle_up"


# ==================== Windows 虚拟键映射 ====================
WINDOWS_KEY_MAP = {
    KeyCode.HOME: 0x24,
    KeyCode.BACK: 0x08,
    KeyCode.MENU: 0x12,
    KeyCode.POWER: 0x5B,
    KeyCode.WIN: 0x5B,

    KeyCode.DPAD_UP: 0x26,
    KeyCode.DPAD_DOWN: 0x28,
    KeyCode.DPAD_LEFT: 0x25,
    KeyCode.DPAD_RIGHT: 0x27,
    KeyCode.DPAD_CENTER: 0x0D,

    KeyCode.ENTER: 0x0D,
    KeyCode.RETURN: 0x0D,
    KeyCode.DELETE: 0x2E,
    KeyCode.SPACE: 0x20,
    KeyCode.TAB: 0x09,
    KeyCode.ESCAPE: 0x1B,
    KeyCode.CAPS_LOCK: 0x14,

    KeyCode.SHIFT: 0x10,
    KeyCode.CONTROL: 0x11,
    KeyCode.ALT: 0x12,
    KeyCode.LSHIFT: 0xA0,
    KeyCode.RSHIFT: 0xA1,
    KeyCode.LCTRL: 0xA2,
    KeyCode.RCTRL: 0xA3,
    KeyCode.LALT: 0xA4,
    KeyCode.RALT: 0xA5,

    # 字母键（大写 ASCII = VK 码）
    KeyCode.A: 0x41, KeyCode.B: 0x42, KeyCode.C: 0x43, KeyCode.D: 0x44,
    KeyCode.E: 0x45, KeyCode.F: 0x46, KeyCode.G: 0x47, KeyCode.H: 0x48,
    KeyCode.I: 0x49, KeyCode.J: 0x4A, KeyCode.K: 0x4B, KeyCode.L: 0x4C,
    KeyCode.M: 0x4D, KeyCode.N: 0x4E, KeyCode.O: 0x4F, KeyCode.P: 0x50,
    KeyCode.Q: 0x51, KeyCode.R: 0x52, KeyCode.S: 0x53, KeyCode.T: 0x54,
    KeyCode.U: 0x55, KeyCode.V: 0x56, KeyCode.W: 0x57, KeyCode.X: 0x58,
    KeyCode.Y: 0x59, KeyCode.Z: 0x5A,

    # 主键盘区数字
    KeyCode.DIGIT_0: 0x30, KeyCode.DIGIT_1: 0x31, KeyCode.DIGIT_2: 0x32,
    KeyCode.DIGIT_3: 0x33, KeyCode.DIGIT_4: 0x34, KeyCode.DIGIT_5: 0x35,
    KeyCode.DIGIT_6: 0x36, KeyCode.DIGIT_7: 0x37, KeyCode.DIGIT_8: 0x38,
    KeyCode.DIGIT_9: 0x39,

    # 小键盘
    KeyCode.NUM_0: win32con.VK_NUMPAD0, KeyCode.NUM_1: win32con.VK_NUMPAD1,
    KeyCode.NUM_2: win32con.VK_NUMPAD2, KeyCode.NUM_3: win32con.VK_NUMPAD3,
    KeyCode.NUM_4: win32con.VK_NUMPAD4, KeyCode.NUM_5: win32con.VK_NUMPAD5,
    KeyCode.NUM_6: win32con.VK_NUMPAD6, KeyCode.NUM_7: win32con.VK_NUMPAD7,
    KeyCode.NUM_8: win32con.VK_NUMPAD8, KeyCode.NUM_9: win32con.VK_NUMPAD9,
    KeyCode.NUM_LOCK: win32con.VK_NUMLOCK,
    KeyCode.NUM_ADD: win32con.VK_ADD,
    KeyCode.NUM_SUBTRACT: win32con.VK_SUBTRACT,
    KeyCode.NUM_MULTIPLY: win32con.VK_MULTIPLY,
    KeyCode.NUM_DIVIDE: win32con.VK_DIVIDE,
    KeyCode.NUM_DECIMAL: win32con.VK_DECIMAL,
    KeyCode.NUM_ENTER: win32con.VK_RETURN,

    # F1~F12
    KeyCode.F1: 0x70, KeyCode.F2: 0x71, KeyCode.F3: 0x72, KeyCode.F4: 0x73,
    KeyCode.F5: 0x74, KeyCode.F6: 0x75, KeyCode.F7: 0x76, KeyCode.F8: 0x77,
    KeyCode.F9: 0x78, KeyCode.F10: 0x79, KeyCode.F11: 0x7A, KeyCode.F12: 0x7B,

    # 常用符号（主键盘区）
    KeyCode.TILDE: 0xC0, KeyCode.EXCLAMATION: 0x31,
    KeyCode.AT: 0x32, KeyCode.HASH: 0x33, KeyCode.DOLLAR: 0x34,
    KeyCode.PERCENT: 0x35, KeyCode.CARET: 0x36, KeyCode.AMPERSAND: 0x37,
    KeyCode.ASTERISK: 0x38, KeyCode.LEFT_PAREN: 0x39, KeyCode.RIGHT_PAREN: 0x30,
    KeyCode.UNDERSCORE: 0xBD, KeyCode.PLUS: 0xBB, KeyCode.MINUS: 0xBD,
    KeyCode.EQUALS: 0xBB, KeyCode.BACKSLASH: 0xBC, KeyCode.PIPE: 0xDC,
    KeyCode.LEFT_BRACKET: 0xDB, KeyCode.RIGHT_BRACKET: 0xDD,
    KeyCode.LEFT_BRACE: 0xDB, KeyCode.RIGHT_BRACE: 0xDD,
    KeyCode.SEMICOLON: 0xBA, KeyCode.COLON: 0xBA,
    KeyCode.APOSTROPHE: 0xDE, KeyCode.QUOTE: 0xDE,
    KeyCode.COMMA: 0xBC, KeyCode.PERIOD: 0xBE, KeyCode.SLASH: 0xBF, KeyCode.QUESTION: 0xBF,
}


def get_windows_keycode(key: KeyCode) -> int:
    """获取 Windows 虚拟键码"""
    return WINDOWS_KEY_MAP.get(key, 0)


def get_android_keycode(key: KeyCode) -> int:
    """获取 Android 按键码（保留你原来的）"""
    # 你原来的映射可以继续扩展
    return {
        KeyCode.HOME: 3, KeyCode.BACK: 4, KeyCode.MENU: 82, KeyCode.POWER: 26,
        KeyCode.ENTER: 66, KeyCode.SPACE: 62, KeyCode.TAB: 61, KeyCode.ESCAPE: 111,
        KeyCode.A: 29, KeyCode.B: 30, KeyCode.C: 31, KeyCode.D: 32, KeyCode.E: 33,
        KeyCode.F: 34, KeyCode.G: 35, KeyCode.H: 36, KeyCode.I: 37, KeyCode.J: 38,
        KeyCode.K: 39, KeyCode.L: 40, KeyCode.M: 41, KeyCode.N: 42, KeyCode.O: 43,
        KeyCode.P: 44, KeyCode.Q: 45, KeyCode.R: 46, KeyCode.S: 47, KeyCode.T: 48,
        KeyCode.U: 49, KeyCode.V: 50, KeyCode.W: 51, KeyCode.X: 52, KeyCode.Y: 53, KeyCode.Z: 54,
    }.get(key, 0)


# 可选：PyDirectInput 映射（如果你以后要用）
def get_pydirectinput_keyname(key: KeyCode) -> str:
    return {
        KeyCode.SHIFT: "shift", KeyCode.CONTROL: "ctrl", KeyCode.ALT: "alt",
        KeyCode.WIN: "win", KeyCode.F1: "f1", KeyCode.F12: "f12",
        KeyCode.DIGIT_1: "1", KeyCode.SPACE: "space",
    }.get(key, "")