import dxcam
import cv2
import numpy as np
import time
import threading
from datetime import datetime

class DXCAMDemo:
    def __init__(self):
        self.camera = None
        self.is_recording = False
        self.fps = 0
        self.frame_count = 0
        self.start_time = 0
        
    def init_camera(self):
        """初始化DXCAM相机"""
        try:
            print("🚀 初始化 DXCAM...")
            
            # 创建相机实例
            self.camera = dxcam.create()
            
            if self.camera is None:
                print("❌ 无法创建DXCAM实例")
                return False
            
            print("✅ DXCAM初始化成功")
            print(f"📱 设备: {self.camera.device}")
            print(f"📺 输出信息: {self.camera.output_info}")
            print(f"🎯 分辨率: {self.camera.resolution}")
            print(f"📊 色彩格式: {self.camera.color_format}")
            
            return True
            
        except Exception as e:
            print(f"❌ DXCAM初始化失败: {e}")
            return False
    
    def list_monitors(self):
        """列出所有显示器"""
        try:
            cameras = dxcam.create(output_idx=None, output_color="BGR")
            if cameras:
                print("\n📋 可用显示器:")
                for i, cam in enumerate(cameras):
                    print(f"  [{i}] {cam.output_name} - {cam.resolution}")
                return cameras
            return None
        except Exception as e:
            print(f"❌ 获取显示器列表失败: {e}")
            return None
    
    def select_monitor(self):
        """选择要截图的显示器"""
        monitors = self.list_monitors()
        if not monitors:
            print("❌ 未找到显示器")
            return None
        
        try:
            choice = input(f"选择显示器 (0-{len(monitors)-1}，直接回车选择主显示器): ").strip()
            if choice and choice.isdigit() and 0 <= int(choice) < len(monitors):
                selected = monitors[int(choice)]
                print(f"✅ 选择显示器: {selected.output_name}")
                return dxcam.create(output_idx=int(choice), output_color="BGR")
            else:
                print("✅ 使用主显示器")
                return dxcam.create(output_idx=0, output_color="BGR")
        except:
            print("✅ 使用默认主显示器")
            return dxcam.create(output_idx=0, output_color="BGR")
    
    def select_region(self):
        """选择截图区域"""
        print("\n🎯 区域选择:")
        print("  1. 全屏截图")
        print("  2. 选择区域")
        
        choice = input("请选择 (1-2): ").strip()
        
        if choice == "2":
            try:
                print("📏 请输入区域坐标 (格式: left,top,width,height)")
                print("  例如: 100,100,800,600")
                region_input = input("区域: ").strip()
                
                if region_input:
                    left, top, width, height = map(int, region_input.split(','))
                    region = (left, top, left + width, top + height)
                    print(f"✅ 设置区域: {region}")
                    return region
            except:
                print("❌ 区域格式错误，使用全屏")
        
        print("✅ 使用全屏截图")
        return None
    
    def start_capture(self, target_fps=60, region=None):
        """开始截图"""
        if not self.camera:
            if not self.init_camera():
                return False
        
        try:
            print(f"\n🎮 开始截图 - 目标FPS: {target_fps}")
            if region:
                print(f"📐 截图区域: {region}")
            
            # 开始截图
            self.camera.start(target_fps=target_fps, region=region, video_mode=True)
            
            self.is_recording = True
            self.frame_count = 0
            self.start_time = time.time()
            
            # 启动FPS计算线程
            fps_thread = threading.Thread(target=self._calculate_fps, daemon=True)
            fps_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ 启动截图失败: {e}")
            return False
    
    def _calculate_fps(self):
        """计算实时FPS"""
        last_count = 0
        while self.is_recording:
            time.sleep(1)
            current_count = self.frame_count
            self.fps = current_count - last_count
            last_count = current_count
    
    def realtime_preview(self):
        """实时预览"""
        print("\n👀 实时预览模式")
        print("  按 's' 保存当前帧")
        print("  按 'q' 退出预览")
        print("  按 'r' 开始/停止录制视频")
        
        recording_video = False
        video_writer = None
        
        try:
            while self.is_recording:
                # 获取最新帧
                frame = self.camera.get_latest_frame()
                
                if frame is not None:
                    self.frame_count += 1
                    
                    # 添加信息叠加
                    info_frame = self._add_frame_info(frame)
                    
                    # 显示帧
                    cv2.imshow('DXCAM - 后台截图预览', info_frame)
                    
                    # 录制视频
                    if recording_video and video_writer is not None:
                        video_writer.write(frame)
                    
                    # 键盘控制
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('s'):
                        self._save_frame(frame)
                    elif key == ord('r'):
                        recording_video = not recording_video
                        if recording_video:
                            video_writer = self._start_recording(frame)
                        else:
                            self._stop_recording(video_writer)
                            video_writer = None
                
                time.sleep(0.001)  # 短暂休眠避免过高CPU占用
                
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断")
        finally:
            if recording_video and video_writer is not None:
                self._stop_recording(video_writer)
            self.stop_capture()
            cv2.destroyAllWindows()
    
    def _add_frame_info(self, frame):
        """在帧上添加信息"""
        info_frame = frame.copy()
        
        # 添加FPS信息
        fps_text = f"FPS: {self.fps}"
        cv2.putText(info_frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 添加帧计数
        count_text = f"Frames: {self.frame_count}"
        cv2.putText(info_frame, count_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 添加时间戳
        time_text = datetime.now().strftime("%H:%M:%S")
        cv2.putText(info_frame, time_text, (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 添加分辨率信息
        res_text = f"Size: {frame.shape[1]}x{frame.shape[0]}"
        cv2.putText(info_frame, res_text, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return info_frame
    
    def _save_frame(self, frame):
        """保存当前帧"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"screenshot_{timestamp}.png"
        cv2.imwrite(filename, frame)
        print(f"💾 截图已保存: {filename}")
    
    def _start_recording(self, frame):
        """开始录制视频"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.avi"
        
        height, width = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video_writer = cv2.VideoWriter(filename, fourcc, 30.0, (width, height))
        
        print(f"🎥 开始录制: {filename}")
        return video_writer
    
    def _stop_recording(self, video_writer):
        """停止录制视频"""
        if video_writer:
            video_writer.release()
            print("⏹️ 录制已停止")
    
    def stop_capture(self):
        """停止截图"""
        if self.camera and self.is_recording:
            self.camera.stop()
            self.is_recording = False
            
            # 计算统计信息
            end_time = time.time()
            duration = end_time - self.start_time
            avg_fps = self.frame_count / duration if duration > 0 else 0
            
            print(f"\n📊 截图统计:")
            print(f"  总帧数: {self.frame_count}")
            print(f"  持续时间: {duration:.2f}秒")
            print(f"  平均FPS: {avg_fps:.2f}")
    
    def benchmark(self, duration=10):
        """性能测试"""
        print(f"\n🧪 开始性能测试 ({duration}秒)...")
        
        if self.start_capture(target_fps=144):  # 高FPS测试
            time.sleep(duration)
            self.stop_capture()
    
    def interactive_demo(self):
        """交互式演示"""
        print("=" * 50)
        print("🎮 DXCAM 后台截图演示")
        print("=" * 50)
        
        # 选择显示器
        self.camera = self.select_monitor()
        if not self.camera:
            return
        
        # 选择区域
        region = self.select_region()
        
        # 选择FPS
        try:
            fps = int(input("🎯 输入目标FPS (默认60): ") or "60")
        except:
            fps = 60
        
        # 开始截图
        if self.start_capture(target_fps=fps, region=region):
            # 实时预览
            self.realtime_preview()
        
        print("👋 演示结束")

# 快速测试函数
def quick_test():
    """快速测试DXCAM"""
    print("🚀 DXCAM快速测试...")
    
    try:
        # 创建相机
        camera = dxcam.Camera()
        if camera is None:
            print("❌ 无法创建DXCAM相机")
            return
        
        # 开始截图
        camera.start(target_fps=60)
        print("✅ DXCAM启动成功")
        print("📸 截图5帧测试...")
        
        # 测试截图几帧
        for i in range(5):
            frame = camera.get_latest_frame()
            if frame is not None:
                print(f"✅ 第{i+1}帧: {frame.shape}")
                
                # 显示第一帧
                if i == 0:
                    cv2.imshow('DXCAM Test Frame', frame)
                    cv2.waitKey(1000)  # 显示1秒
                    cv2.destroyAllWindows()
            
            time.sleep(0.5)
        
        camera.stop()
        print("🎉 DXCAM测试成功!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    # 选择运行模式
    print("选择运行模式:")
    print("1. 快速测试")
    print("2. 完整演示")
    
    choice = input("请选择 (1-2): ").strip()
    
    if choice == "1":
        quick_test()
    else:
        demo = DXCAMDemo()
        demo.interactive_demo()