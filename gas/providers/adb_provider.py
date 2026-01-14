# src/providers/adb_provider.py
from pathlib import Path
import platform
import subprocess
import shutil
import os
import time
from typing import Optional, Tuple, List, Dict, Any
import cv2
import numpy as np
import re

from gas.cons.key_code import KeyCode, get_android_keycode
from gas.interfaces.interfaces import IDeviceProvider
from gas.logger import get_logger
from gas.util.wrap_util import timeit

logger = get_logger()


class ADBDeviceInfo:
    def __init__(self, serial: str, status: str):
        self.serial = serial
        self.status = status

    def __str__(self):
        return f"{self.serial} ({self.status})"


def _scan_for_adb_in_directory(root: str, max_depth: int = 3) -> Optional[str]:
    root_path = Path(root)
    if not root_path.exists():
        return None

    adb_names = ["adb.exe", "nox_adb.exe", "hd-adb.exe", "adb_server.exe"]

    try:
        for depth in range(max_depth + 1):
            pattern = "*" + "/*" * depth
            for file_path in root_path.glob(pattern):
                if file_path.is_file() and file_path.name.lower() in [n.lower() for n in adb_names]:
                    full_path = str(file_path.resolve())
                    logger.info(f"扫盘发现 ADB: {full_path}")
                    return full_path
    except (PermissionError, OSError):
        pass
    except Exception as e:
        logger.debug(f"扫描目录 {root} 时异常: {e}")

    return None


def _find_adb_path() -> str:
    system = platform.system()

    adb_path = shutil.which("adb.exe" if system == "Windows" else "adb")
    if adb_path:
        logger.info(f"从系统 PATH 检测到 adb: {adb_path}")
        return adb_path

    if system != "Windows":
        logger.warning("非 Windows 系统暂不启用扫盘模式")
        return "adb"

    # 常见模拟器路径
    common_emulator_paths = [
        r"C:\Program Files\Nox\bin\nox_adb.exe",
        r"C:\Program Files\Nox\bin\adb.exe",
        r"C:\Program Files (x86)\Bignox\BigNox\bin\nox_adb.exe",
        r"C:\Program Files (x86)\Bignox\BigNox\bin\adb.exe",
        r"C:\Program Files\BlueStacks_nxt\hd-adb.exe",
        r"C:\Program Files\BlueStacks_nxt\adb.exe",
        r"C:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe",
        r"C:\Program Files\MuMu Emulator\shell\adb.exe",
        r"C:\LDPlayer\LDPlayer9\adb.exe",
        r"C:\LDPlayer\LDPlayer4.0\adb.exe",
        r"C:\Program Files\Microvirt\MEmu\adb.exe",
    ]

    for path in common_emulator_paths:
        if os.path.isfile(path):
            logger.info(f"命中常见模拟器路径: {path}")
            return path

    # 扫盘
    drive_letters = ["C:", "D:", "E:", "F:"]
    scan_roots = []
    for drive in drive_letters:
        drive_path = Path(drive) / "/"
        if drive_path.exists():
            scan_roots.extend(
                [
                    drive_path / "Program Files",
                    drive_path / "Program Files (x86)",
                    drive_path / "Nox",
                    drive_path / "Bignox",
                    drive_path / "BigNox",
                    drive_path / "BlueStacks_nxt",
                    drive_path / "MuMuPlayer-12.0",
                    drive_path / "MuMu Emulator",
                    drive_path / "LDPlayer",
                    drive_path / "Microvirt",
                    drive_path / "Netease",
                ]
            )

    logger.info("开始扫盘搜索 ADB（可能需要几秒）...")
    for root in scan_roots:
        if root.exists():
            found = _scan_for_adb_in_directory(str(root), max_depth=3)
            if found:
                return found

    # SDK 环境变量和默认路径
    sdk_root = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if sdk_root:
        candidate = Path(sdk_root) / "platform-tools" / "adb.exe"
        if candidate.exists():
            return str(candidate)

    home = os.path.expanduser("~")
    default_sdk = Path(home) / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "adb.exe"
    if default_sdk.exists():
        return str(default_sdk)

    logger.warning("未找到具体 adb，将使用 'adb'")
    return "adb"


class ADBProvider(IDeviceProvider):
    def __init__(
        self,
        adb_path: Optional[str] = None,
        device_id: Optional[str | int] = None,
    ):
        if adb_path is None:
            adb_path = _find_adb_path()
        self.adb_path = adb_path

        if not self._test_adb_version():
            raise RuntimeError(f"ADB 不可用: {self.adb_path}")

        self.device_id: Optional[str] = None
        self._screen_size: Optional[Tuple[int, int]] = None

        # 用于模拟拖拽的内部状态（链式短 swipe）
        self.is_pressed: bool = False
        self.down_x: Optional[int] = None
        self.down_y: Optional[int] = None
        self.last_x: Optional[int] = None
        self.last_y: Optional[int] = None

        devices = self._list_devices()
        if not devices:
            raise RuntimeError("未检测到任何在线设备")

        if device_id is not None:
            if isinstance(device_id, str):
                if any(d.serial == device_id for d in devices):
                    self.device_id = device_id
                else:
                    raise ValueError(f"设备未找到: {device_id}")
            elif isinstance(device_id, int):
                if 0 <= device_id < len(devices):
                    self.device_id = devices[device_id].serial
                else:
                    raise IndexError(f"索引超出范围: {device_id}")
        elif len(devices) == 1:
            self.device_id = devices[0].serial
            logger.info(f"自动选择唯一设备: {self.device_id}")
        else:
            device_list = "\n".join(f"  [{i}] {d}" for i, d in enumerate(devices))
            raise RuntimeError(f"检测到多个设备，请指定:\n{device_list}")

        logger.info(f"ADBProvider 初始化成功，设备: {self.device_id}")

    def _test_adb_version(self) -> bool:
        try:
            result = subprocess.run([self.adb_path, "version"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0 and "Android Debug Bridge" in result.stdout
        except Exception:
            return False

    def _run_adb(self, command: List[str], text: bool = True, timeout: int = 10) -> subprocess.CompletedProcess:
        full_cmd = [self.adb_path]
        if self.device_id:
            full_cmd += ["-s", self.device_id]
        full_cmd += command
        return subprocess.run(full_cmd, capture_output=True, text=text, timeout=timeout)

    def _list_devices(self) -> List[ADBDeviceInfo]:
        try:
            result = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return []
            devices = []
            for line in result.stdout.splitlines()[1:]:
                if "\tdevice" in line:
                    serial = line.split("\t")[0].strip()
                    devices.append(ADBDeviceInfo(serial, "device"))
            return devices
        except Exception as e:
            logger.error(f"列出设备失败: {e}")
            return []

    def is_available(self) -> bool:
        try:
            result = self._run_adb(["get-state"], timeout=5)
            return result.returncode == 0 and "device" in result.stdout.strip()
        except Exception:
            return False

    @timeit
    def capture(self) -> Optional[np.ndarray]:
        try:
            result = self._run_adb(["exec-out", "screencap", "-p"], text=False, timeout=15)
            if result.returncode != 0 or not result.stdout:
                return None
            img = cv2.imdecode(np.frombuffer(result.stdout, np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                self._screen_size = (img.shape[1], img.shape[0])
                return img
        except Exception as e:
            logger.error(f"截图失败: {e}")
        return None

    def get_size(self) -> Optional[Tuple[int, int, int, int]]:
        if self._screen_size:
            return (*self._screen_size, 0, 0)
        try:
            result = self._run_adb(["shell", "wm", "size"])
            if result.returncode == 0:
                match = re.search(r"(\d+)x(\d+)", result.stdout)
                if match:
                    w, h = int(match.group(1)), int(match.group(2))
                    self._screen_size = (w, h)
                    return (w, h, 0, 0)
        except Exception:
            pass
        return None

    def click(self, x: int, y: int) -> bool:
        try:
            result = self._run_adb(["shell", "input", "tap", str(x), str(y)])
            return result.returncode == 0
        except Exception:
            return False

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.2) -> bool:
        try:
            ms = max(10, int(duration * 1000))
            result = self._run_adb(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(ms)])
            return result.returncode == 0
        except Exception:
            return False

    def mouse_action(self, x: int, y: int, action: str = "move", delay: float = 0.01) -> bool:
        """
        ADB 低级鼠标操作实现
        """
        time.sleep(delay)

        try:
            success = True

            if action == "down":
                # 对于ADB，按下时需要立即执行一个极短的swipe来模拟按下
                self.is_pressed = True
                self.down_x = x
                self.down_y = y
                self.last_x = x
                self.last_y = y

                # 执行一个极短的swipe来模拟按下（从x,y到x+1,y+1，持续0.01秒）
                # 这样后续的移动才会被识别为拖拽
                success = self.swipe(x, y, x + 1, y + 1, duration=0.01)

            elif action == "up":
                if self.is_pressed:
                    if self.down_x is not None and self.down_y is not None:
                        # 如果是点击（按下和抬起在同一位置）
                        if abs(x - self.down_x) < 5 and abs(y - self.down_y) < 5:
                            # 纯点击：执行tap
                            success = self.click(x, y)
                        else:
                            # 拖拽结束：最后一段短swipe
                            if self.last_x is not None and self.last_y is not None:
                                success = self.swipe(self.last_x, self.last_y, x, y, duration=0.03)
                # 重置状态
                self.is_pressed = False
                self.down_x = None
                self.down_y = None
                self.last_x = x
                self.last_y = y

            elif action in ("move", "drag"):
                # 如果处于按下状态，执行拖拽
                if self.is_pressed and self.last_x is not None and self.last_y is not None:
                    # 计算移动距离，动态调整持续时间
                    distance = ((x - self.last_x) ** 2 + (y - self.last_y) ** 2) ** 0.5
                    duration = max(0.01, min(0.05, distance * 0.001))  # 根据距离调整
                    success = self.swipe(self.last_x, self.last_y, x, y, duration=duration)

                self.last_x = x
                self.last_y = y

            return success

        except Exception as e:
            logger.error(f"ADB mouse_action 失败 {action} ({x},{y}): {e}")
            # 异常时强制重置，防止状态卡住
            self.is_pressed = False
            self.down_x = None
            self.down_y = None
            return False

    def input_text(self, text: str) -> bool:
        try:
            escaped = text.replace(" ", "%s")
            result = self._run_adb(["shell", "input", "text", escaped])
            return result.returncode == 0
        except Exception:
            return False

    def key_event(self, keycode: KeyCode, action: str = "tap") -> bool:
        android_code = get_android_keycode(keycode)
        if android_code == 0:
            return False
        try:
            if action == "tap":
                cmd = ["shell", "input", "keyevent", str(android_code)]
            elif action == "down" or action == "longpress":
                cmd = ["shell", "input", "keyevent", "--longpress", str(android_code)]
            else:
                return False
            result = self._run_adb(cmd)
            return result.returncode == 0
        except Exception:
            return False

    def get_info(self) -> Dict[str, Any]:
        try:
            model_result = self._run_adb(["shell", "getprop", "ro.product.model"], text=True)
            model = model_result.stdout.strip() if model_result.returncode == 0 else "Unknown"
            size = self.get_size()
            return {
                "type": "adb",
                "device_id": self.device_id,
                "model": model,
                "size": size,
                "adb_path": self.adb_path,
            }
        except Exception:
            return {}
