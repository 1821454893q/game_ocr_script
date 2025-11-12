# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gas",
    version="1.0.0",
    author="Jian",
    author_email="your.email@example.com",
    description="基于PaddleOCR的游戏自动化工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "opencv-python>=4.8.0",
        "pyautogui>=0.9.54",
        "pytesseract>=0.3.10",
        "pygetwindow>=0.0.9",
        "pywin32>=306",
        "paddleocr>=2.7.0",
        "pillow>=9.0.0",
        "psutil>=5.9.0",
        "pynput>=1.8.1",
        "mss>=10.1.0",
    ],
    entry_points={
        "console_scripts": [
            "gas=gas.cli:main",
        ],
    },
    include_package_data=True,
)
