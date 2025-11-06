# OCR Automation Tool

基于 PaddleOCR 的 Windows 自动化工具，支持后台截图和操作。

## 安装

```bash
pip install -r requirements.txt

python -m build

pip install .

# 安装完毕之后 可以使用命令执行
ocr-tool --help

ocr-tool -w "MuMuNxDevice" -wc "Qt5156QWindowIcon" -t "云二重" -conf "0.5"

安装¶
1. 安装PaddlePaddle¶
CPU端安装：


python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/


GPU端安装，由于GPU端需要根据具体CUDA版本来对应安装使用，以下仅以Linux平台，pip安装英伟达GPU， CUDA 11.8为例，其他平台，请参考飞桨官网安装文档中的说明进行操作。

0python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

请注意，PaddleOCR 3.x版本 依赖于 3.0 及以上版本的飞桨框架。

```