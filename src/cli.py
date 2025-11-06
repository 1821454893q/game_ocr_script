#!/usr/bin/env python3
"""OCR工具命令行接口"""

import argparse
import time
from .ocr_engine import OCREngine
from .logger import get_logger

logger = get_logger()


def main():
    parser = argparse.ArgumentParser(description="OCR自动化工具")
    parser.add_argument("--window", "-w", required=True, help="目标窗口标题")
    parser.add_argument("--text", "-t", required=True, help="要查找的文本")
    parser.add_argument("--click", "-c", action="store_true", help="找到后点击")
    parser.add_argument("--confidence", "-conf", type=float, default=0.8, help="置信度阈值")
    parser.add_argument("--interval", "-i", type=float, default=2.0, help="检查间隔(秒)")
    parser.add_argument("--continuous", "-cont", action="store_true", help="持续监控")

    args = parser.parse_args()

    # 创建OCR引擎
    engine = OCREngine(args.window)

    def search_once():
        result = engine.find_text(args.text, args.confidence)
        if result:
            x, y, text = result
            print(f"✅ 找到文本: '{text}' 坐标: ({x}, {y})")

            if args.click:
                engine.click_text(args.text, args.confidence)
            return True
        else:
            print(f"❌ 未找到文本: {args.text}")
            return False

    if args.continuous:
        print(f"🔄 持续监控中... 窗口: {args.window}, 文本: {args.text}")
        try:
            while True:
                search_once()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n👋 用户中断")
    else:
        search_once()


if __name__ == "__main__":
    main()
