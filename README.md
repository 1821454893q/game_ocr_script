# OCR Automation Tool

基于 PaddleOCR 的 Windows 自动化工具，支持后台截图和操作。

## 安装

```bash
python -m build
pip install .

# 安装完毕之后 可以使用命令执行
ocr-tool --help

ocr-tool -w "MuMuNxDevice" -wc "Qt5156QWindowIcon" -t "云二重" -conf "0.5"