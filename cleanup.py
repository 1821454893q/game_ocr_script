#!/usr/bin/env python3
"""
修复版跨平台项目清理脚本
用法: python cleanup.py
"""

import os
import shutil
import glob


def clean_project():
    """清理Python项目构建文件和缓存"""

    print("🧹 开始清理Python项目...")

    # 要删除的目录列表（具体路径）
    dirs_to_remove = [
        "build",
        "dist",
        ".pytest_cache",
        ".cache",
        "__pycache__",
    ]

    # 要删除的文件模式
    file_patterns = ["*.pyc", "*.pyo", ".coverage", "*.log"]

    # 删除固定目录
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"✅ 删除目录: {dir_path}")
            except Exception as e:
                print(f"⚠️  删除目录失败 {dir_path}: {e}")

    # 专门处理egg-info目录（需要递归查找）
    print("\n🔍 查找并清理egg-info目录...")
    egg_info_found = False

    # 方法1: 使用glob递归查找所有egg-info目录
    for egg_info_path in glob.glob("**/*.egg-info", recursive=True):
        if os.path.isdir(egg_info_path):
            try:
                shutil.rmtree(egg_info_path)
                print(f"✅ 删除egg-info: {egg_info_path}")
                egg_info_found = True
            except Exception as e:
                print(f"⚠️  删除egg-info失败 {egg_info_path}: {e}")

    # 方法2: 使用os.walk确保找到所有egg-info
    for root, dirs, files in os.walk("."):
        for dir_name in dirs:
            if dir_name.endswith(".egg-info"):
                egg_info_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(egg_info_path)
                    print(f"✅ 删除egg-info: {egg_info_path}")
                    egg_info_found = True
                except Exception as e:
                    print(f"⚠️  删除egg-info失败 {egg_info_path}: {e}")

    if not egg_info_found:
        print("ℹ️  未找到egg-info目录")

    # 删除文件
    print("\n🗑️  清理缓存文件...")
    for pattern in file_patterns:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    print(f"✅ 删除文件: {file_path}")
                except Exception as e:
                    print(f"⚠️  删除文件失败 {file_path}: {e}")

    # 专门递归删除所有__pycache__目录和.pyc文件
    print("\n🔍 深度清理Python缓存...")
    pycache_count = 0
    pyc_count = 0

    for root, dirs, files in os.walk("."):
        # 删除__pycache__目录
        if "__pycache__" in dirs:
            cache_dir = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ 删除缓存目录: {cache_dir}")
                pycache_count += 1
            except Exception as e:
                print(f"⚠️  删除缓存目录失败 {cache_dir}: {e}")

        # 删除.pyc和.pyo文件
        for file in files:
            if file.endswith((".pyc", ".pyo")):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"✅ 删除缓存文件: {file_path}")
                    pyc_count += 1
                except Exception as e:
                    print(f"⚠️  删除缓存文件失败 {file_path}: {e}")

    print(f"\n📊 清理统计:")
    print(f"   - 删除 {pycache_count} 个__pycache__目录")
    print(f"   - 删除 {pyc_count} 个.pyc/.pyo文件")
    print("🎉 清理完成!")


def find_egg_info_locations():
    """辅助函数：查找所有egg-info目录的位置"""
    print("\n🔍 扫描egg-info目录...")
    found = []

    for root, dirs, files in os.walk("."):
        for dir_name in dirs:
            if dir_name.endswith(".egg-info"):
                full_path = os.path.join(root, dir_name)
                found.append(full_path)
                print(f"📍 找到: {full_path}")

    if not found:
        print("ℹ️  未找到任何egg-info目录")

    return found


if __name__ == "__main__":
    # 先显示找到的egg-info目录
    egg_info_locations = find_egg_info_locations()

    if egg_info_locations:
        response = input(f"\n是否删除以上 {len(egg_info_locations)} 个egg-info目录? (y/N): ")
        if response.lower() in ["y", "yes"]:
            clean_project()
        else:
            print("❌ 用户取消操作")
    else:
        clean_project()
