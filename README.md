# gas - 基于OCR的自动化工具库

基于PaddleOCR的跨平台自动化工具库，支持Windows窗口和Android设备（通过ADB）的OCR文字识别和自动化操作。

## 功能特性

- **多平台支持**: 支持Windows窗口操作和Android设备（通过ADB）
- **OCR文字识别**: 基于PaddleOCR PP-OCRv5模型进行文字识别
- **后台操作**: 支持窗口后台截图和操作，无需前置窗口
- **灵活的文本匹配**: 支持精确匹配、正则表达式匹配
- **批量处理**: 支持同时处理多个文本动作
- **命令行工具**: 提供便捷的命令行接口

## 安装

```bash
# 克隆或下载项目后
pip install -e .

# 或者直接安装
pip install gas
```

### 依赖安装

如果需要手动安装依赖：

```bash
pip install -r requirements.txt
```

### PaddlePaddle安装

根据您的环境选择安装方式：

**CPU版本：**
```bash
python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

**GPU版本（CUDA 11.8）：**
```bash
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
```

## 快速开始

### 命令行使用

```bash
# 基本用法
gas --window "窗口标题" --text "要查找的文本" --confidence 0.8

# 查找文本并点击
gas -w "MuMuPlayer" -t "登录" -c

# 持续监控模式
gas -w "MuMuPlayer" -t "开始游戏" --continuous

# 完整参数示例
gas -w "MuMuNxDevice" -wc "Qt5156QWindowIcon" -t "云二重" -conf 0.5
```

### Python代码使用

#### 1. Windows窗口操作

```python
from gas import OCREngine

# 创建OCR引擎实例
engine = OCREngine.create_with_window("MuMuPlayer")

# 查找文本
result = engine.find_text("登录", confidence=0.8)
if result:
    x, y, text = result
    print(f"找到文本: {text} 位置: ({x}, {y})")

# 点击文本
engine.click_text("开始游戏", confidence=0.8)

# 等待文本出现
result = engine.wait_for_text("加载完成", timeout=60)
```

#### 2. Android设备操作（ADB）

```python
from gas import OCREngine

# 创建ADB引擎实例
engine = OCREngine.create_with_adb()

# 或指定设备
engine = OCREngine.create_with_adb(device_id="emulator-5554")

# 执行操作
engine.click_text("确定", confidence=0.8)
engine.swipe(100, 500, 100, 200)  # 滑动操作
```

#### 3. 批量处理文本动作

```python
from gas import OCREngine, TextAction

engine = OCREngine.create_with_window("游戏窗口")

# 定义多个文本动作
actions = [
    TextAction(
        pattern=r"等级:\d+",  # 正则匹配
        action=lambda x, y, text, engine: print(f"找到等级: {text}"),
        description="等级文本"
    ),
    TextAction(
        pattern="战斗胜利",
        action=lambda x, y, text, engine: engine.click(x, y+50),  # 点击下方按钮
        once=True,  # 只执行一次
        priority=10  # 优先级
    )
]

# 批量处理
results = engine.process_texts(actions, confidence=0.8)
```

## API参考

### OCREngine类

#### 创建引擎实例

- `OCREngine.create_with_window(window_title, class_name=None, capture_mode=1, activate_windows=False)`
  - 创建Windows窗口引擎
  - `capture_mode`: 1使用bitblt截图，2使用PrintWindow截图
  - `activate_windows`: 是否激活窗口后操作

- `OCREngine.create_with_adb(adb_path=None, device_id=None)`
  - 创建ADB引擎
  - 自动搜索ADB路径和设备

#### 主要方法

- `find_text(target_text, confidence=0.5, use_regex=False)` - 查找文本
- `find_text_in_region(target_text, region, confidence=0.5, use_regex=False)` - 在指定区域查找文本
- `click_text(target_text, confidence=0.5, use_regex=False)` - 点击文本
- `exist_text(target_text, confidence=0.5, use_regex=False)` - 检查文本是否存在
- `wait_for_text(target_text, timeout=30, confidence=0.5, interval=1.0)` - 等待文本出现
- `process_texts(actions, confidence=0.5, stop_after_first=False, region=None)` - 批量处理文本动作
- `click(x, y)` - 点击坐标
- `swipe(x1, y1, x2, y2, is_drag=True, duration=0.5)` - 滑动操作
- `input_text(text)` - 输入文本
- `key_click(key)` - 按键操作

### TextAction类

用于批量处理文本动作，支持：

- `pattern`: 匹配模式（字符串或正则表达式）
- `action`: 匹配后的回调函数 `(x, y, text, engine) -> result`
- `priority`: 优先级（数字越大优先级越高）
- `once`: 是否只执行一次
- `description`: 描述信息

## 支持的设备

### Windows窗口
- 模拟器（如MuMu、BlueStacks、NoxPlayer等）
- 普通Windows应用程序窗口
- 支持后台操作无需窗口前置

### Android设备
- 真实Android设备（需开启USB调试）
- Android模拟器（通过ADB连接）
- 自动检测和搜索ADB路径

## 高级功能

### 区域截图识别
```python
# 在指定区域查找文本 [left, top, right, bottom]
region = (100, 100, 500, 500)
result = engine.find_text_in_region("按钮", region, confidence=0.8)
```

### 正则表达式匹配
```python
# 使用正则表达式匹配动态文本
result = engine.find_text(r"剩余次数:\d+", confidence=0.8, use_regex=True)
```

### 持续监控
```python
import time

while True:
    result = engine.find_text("目标文本", confidence=0.8)
    if result:
        x, y, text = result
        engine.click(x, y)
        break
    time.sleep(1)
```

## 注意事项

1. **权限要求**: 使用ADB功能需要Android设备开启USB调试
2. **窗口权限**: Windows后台操作可能需要管理员权限
3. **性能考虑**: OCR识别会消耗一定计算资源，建议合理设置confidence值
4. **兼容性**: 不同模拟器可能需要特定的ADB路径

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/
```

## 许可证

MIT