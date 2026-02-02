#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持久化监控工具 - 模块化版本
ETW 增强的系统持久化机制监控
"""

import sys
import os
import subprocess
import time
import ctypes
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitors.etw_file import ETWFileMonitor
from utils.snapshot import SnapshotManager
from utils.report import ReportGenerator
from core.api import is_admin


def request_admin():
    """请求管理员权限"""
    if is_admin():
        return True
    
    print("[*] 正在请求管理员权限...")
    try:
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            f'"{script}" {params}', None, 1
        )
        
        if ret > 32:
            sys.exit(0)
        else:
            print("[!] 提权失败，将以降级模式运行")
            return False
    except Exception as e:
        print(f"[!] 提权请求失败: {e}")
        return False


class PersistenceMonitor:
    """持久化监控主类"""
    
    def __init__(self):
        self.etw_monitor = ETWFileMonitor()
        self.snapshot_manager = SnapshotManager()
        self.report_generator = ReportGenerator()
        self.snapshot_before = {}
        self.snapshot_after = {}
    
    def run_analysis(self, exe_path, wait_time=30):
        """运行完整分析流程"""
        print(f"\n{'=' * 80}")
        print(f"持久化监控工具 (模块化版本)")
        print(f"目标程序: {exe_path}")
        print(f"等待时间: {wait_time} 秒")
        print(f"{'=' * 80}\n")
        
        # 1. 获取运行前快照
        print("[1/5] 获取运行前快照...")
        self.snapshot_before = self.snapshot_manager.take_snapshot()
        
        # 2. 启动 ETW 文件监控
        print("\n[2/5] 启动 ETW 文件监控...")
        etw_enabled = self.etw_monitor.start()
        if not etw_enabled:
            print("[!] ETW 启动失败，请确保以管理员权限运行")
            print("[*] 将使用降级模式（无文件监控）继续...")
        
        # 3. 运行目标程序
        print(f"\n[3/5] 启动目标程序: {exe_path}")
        try:
            process = subprocess.Popen(
                [exe_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"[+] 进程已启动 (PID: {process.pid})")
        except Exception as e:
            print(f"[!] 启动程序失败: {e}")
            if etw_enabled:
                self.etw_monitor.stop()
            return None
        
        # 4. 等待
        print(f"\n[4/5] 等待 {wait_time} 秒...")
        try:
            time.sleep(wait_time)
        except KeyboardInterrupt:
            print("\n[*] 用户中断，提前结束等待")
        print("[+] 等待完成")
        
        # 5. 停止 ETW 并获取文件变化
        if etw_enabled:
            self.etw_monitor.stop()
            file_changes = self.etw_monitor.get_file_changes()
            print(f"[+] ETW 捕获文件事件:")
            print(f"    - 新建: {len(file_changes['created'])} 个")
            print(f"    - 删除: {len(file_changes['deleted'])} 个")
            print(f"    - 修改: {len(file_changes['modified'])} 个")
        else:
            file_changes = {'created': {}, 'deleted': {}, 'modified': {}, 'renamed': {}}
        
        # 6. 获取运行后快照
        print(f"\n[5/5] 获取运行后快照...")
        self.snapshot_after = self.snapshot_manager.take_snapshot()
        
        # 7. 比较差异
        print("\n[*] 分析差异...")
        differences = SnapshotManager.compare_snapshots(
            self.snapshot_before,
            self.snapshot_after,
            file_changes
        )
        
        # 8. 显示结果
        self.report_generator.print_differences(differences)
        
        # 9. 保存报告
        report_dir = self.report_generator.save_report(differences, exe_path)
        
        print(f"\n[*] 分析完成!")
        return differences


def main():
    """主入口函数"""
    if len(sys.argv) < 2:
        print("持久化监控工具 (模块化版本)")
        print("=" * 50)
        print("用法: python main.py <exe文件路径> [等待秒数]")
        print("示例: python main.py malware.exe 30")
        print("\n注意: 程序会自动请求管理员权限")
        input("\n按回车键退出...")
        sys.exit(1)
    
    exe_path = sys.argv[1]
    wait_time = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    if not Path(exe_path).exists():
        print(f"[!] 错误: 文件不存在: {exe_path}")
        input("\n按回车键退出...")
        sys.exit(1)
    
    # 请求管理员权限
    has_admin = request_admin()
    
    if not has_admin:
        print("[!] 警告: 未获得管理员权限")
        print("[!] ETW 文件监控将不可用，使用降级模式")
        print()
    
    try:
        monitor = PersistenceMonitor()
        monitor.run_analysis(exe_path, wait_time)
    except Exception as e:
        print(f"\n[!] 运行出错: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()