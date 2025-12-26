# src/operation_player.py
import time
from typing import List, Optional
from dataclasses import dataclass

from .operation_recorder import OperationData, OperationRecorder
from gas.interfaces.interfaces import IDeviceProvider
from gas.logger import get_logger  # ← 统一使用你的日志系统

logger = get_logger()


@dataclass
class ReplayConfig:
    """回放配置"""

    speed: float = 1.0  # 播放速度倍率，>1 加速，<1 减速
    start_delay: float = 1.0  # 开始回放前的延迟（秒）
    loop: bool = False  # 是否循环播放（replay_loop 时有效）
    stop_on_error: bool = True  # 执行失败是否立即停止


class OperationPlayer:
    """
    操作回放器 - 与 OperationRecorder 对称设计
    所有输出统一使用 logger
    """

    def __init__(self, device_provider: IDeviceProvider):
        self.device = device_provider
        self.operations: List[OperationData] = []
        self.screen_width: int = 1920
        self.screen_height: int = 1080
        self.config = ReplayConfig()

    def load_from_recorder(self, recorder: OperationRecorder):
        """从录制器直接加载操作"""
        self.operations = recorder.get_operations()
        self.screen_width = recorder.screen_width
        self.screen_height = recorder.screen_height
        logger.info(f"从 Recorder 加载了 {len(self.operations)} 个操作")
        return self

    def load_from_file(self, filename: str):
        """从 JSON 文件加载操作（复用 Recorder 的加载逻辑）"""
        temp_recorder = OperationRecorder()
        if temp_recorder.load_from_file(filename):
            self.operations = temp_recorder.get_operations()
            self.screen_width = temp_recorder.screen_width
            self.screen_height = temp_recorder.screen_height
            logger.info(f"从文件 {filename} 加载了 {len(self.operations)} 个操作")
        else:
            logger.error(f"从文件 {filename} 加载操作失败")
        return self

    def _get_current_screen_size(self) -> tuple[int, int]:
        """获取当前设备屏幕尺寸，用于坐标反归一化"""
        size = self.device.get_size()
        if size and len(size) >= 2:
            return size[0], size[1]
        logger.warning("无法获取当前屏幕尺寸，使用默认 1920x1080")
        return 1920, 1080

    def _denormalize_x(self, norm_x: float) -> int:
        w, _ = self._get_current_screen_size()
        return int(norm_x * w)

    def _denormalize_y(self, norm_y: float) -> int:
        _, h = self._get_current_screen_size()
        return int(norm_y * h)

    def replay(self, config: Optional[ReplayConfig] = None) -> bool:
        """执行一次回放"""
        if not self.operations:
            logger.warning("没有可回放的操作序列")
            return False

        if not self.device.is_available():
            logger.error("设备不可用，无法回放")
            return False

        cfg = config or self.config

        logger.info(f"开始回放，共 {len(self.operations)} 个操作 | 速度: {cfg.speed}x | 起始延迟: {cfg.start_delay}s")
        time.sleep(cfg.start_delay)

        last_timestamp = 0.0

        try:
            for i, op in enumerate(self.operations):
                # 计算并等待相对时间间隔（支持变速）
                sleep_duration = (op.timestamp - last_timestamp) / cfg.speed
                if sleep_duration > 0:
                    time.sleep(sleep_duration)
                last_timestamp = op.timestamp

                success = self._execute_operation(op)
                if not success:
                    logger.error(f"第 {i+1}/{len(self.operations)} 个操作执行失败")
                    if cfg.stop_on_error:
                        logger.info("因 stop_on_error=True，已停止回放")
                        return False
                    else:
                        logger.warning("操作失败但继续执行后续操作")

            logger.info("全部操作回放完成")
            return True

        except KeyboardInterrupt:
            logger.warning("回放被用户手动中断（Ctrl+C）")
            return False
        except Exception as e:
            logger.exception(f"回放过程中发生未捕获异常: {e}")
            return False

    def _execute_operation(self, op: OperationData) -> bool:
        """执行单个录制操作，返回是否成功"""
        try:
            if op.type == "mouse":
                if op.mouse_action == "click":
                    x = self._denormalize_x(op.pos_x)
                    y = self._denormalize_y(op.pos_y)

                    if op.mouse_event == "down":
                        success = self.device.click(x, y, action="down")
                        logger.debug(f"鼠标按下: ({x}, {y}) button={op.mouse_button}")
                    elif op.mouse_event == "up":
                        success = self.device.click(x, y, action="up")
                        logger.debug(f"鼠标抬起: ({x}, {y}) button={op.mouse_button}")
                    else:  # tap
                        success = self.device.click(x, y)
                        logger.debug(f"鼠标点击: ({x}, {y}) button={op.mouse_button}")

                    return success

                elif op.mouse_action == "move":
                    x = self._denormalize_x(op.pos_x)
                    y = self._denormalize_y(op.pos_y)
                    logger.debug(f"鼠标移动: ({x}, {y})")
                    # 大多数 provider 不支持纯 move，可选择忽略或用微小 swipe 模拟
                    return True

                elif op.mouse_action == "scroll":
                    x = self._denormalize_x(op.pos_x)
                    y = self._denormalize_y(op.pos_y)
                    logger.debug(f"鼠标滚轮: delta={op.scroll} at ({x}, {y})")
                    # 暂不实现滚动（Windows/ADB 支持有限）
                    return True

            elif op.type == "keyboard":
                logger.debug(f"键盘事件: {op.key} {op.key_event}")
                # 简单实现：如果是一般字符，直接 input_text
                # 后续可扩展为 KeyCode 映射 + key_event
                if op.key_event in ("down", "tap") and len(op.key or "") == 1:
                    return self.device.input_text(op.key)
                return True

        except Exception as e:
            logger.error(f"执行操作时异常: {op} | 错误: {e}")
            return False

        return False

    def replay_loop(self, count: int = -1, delay_between: float = 2.0, config: Optional[ReplayConfig] = None):
        """循环回放"""
        i = 1
        while count < 0 or i <= count:
            logger.info(f"第 {i} 次循环回放开始")
            success = self.replay(config)
            if not success:
                logger.error(f"第 {i} 次回放失败，停止循环")
                break

            i += 1
            if (count < 0 or i <= count) and delay_between > 0:
                logger.info(f"循环间隔等待 {delay_between}s")
                time.sleep(delay_between)

        logger.info("循环回放结束")
