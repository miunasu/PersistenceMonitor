"""快照管理模块"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from monitors.registry import RegistryMonitor
from monitors.service import ServiceMonitor
from monitors.task import TaskMonitor
from monitors.process import ProcessMonitor
from monitors.network import NetworkMonitor


class SnapshotManager:
    """快照管理器"""
    
    # 启动文件夹路径
    STARTUP_PATHS = [
        Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup",
        Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs/Startup"),
    ]
    
    def __init__(self):
        self.registry_monitor = RegistryMonitor()
        self.service_monitor = ServiceMonitor()
        self.task_monitor = TaskMonitor()
        self.process_monitor = ProcessMonitor()
        self.network_monitor = NetworkMonitor()
    
    def get_startup_folder_items(self):
        """获取启动文件夹中的项目"""
        items = {}
        for path in self.STARTUP_PATHS:
            if path.exists():
                for item in path.iterdir():
                    try:
                        items[str(item)] = {
                            'name': item.name,
                            'size': item.stat().st_size if item.is_file() else 0,
                            'modified': item.stat().st_mtime
                        }
                    except:
                        pass
        return items
    
    def get_wmi_persistence(self):
        """检查 WMI 事件订阅"""
        import subprocess
        
        def query_wmi(wmi_class):
            try:
                result = subprocess.run(
                    ["wmic", "path", wmi_class, "get", "/format:list"],
                    capture_output=True, text=True, encoding='gbk', timeout=10
                )
                return result.stdout
            except:
                return ""
        
        return {
            'event_consumers': query_wmi('__EventConsumer'),
            'event_filters': query_wmi('__EventFilter'),
            'filter_bindings': query_wmi('__FilterToConsumerBinding')
        }
    
    def get_bits_jobs(self):
        """获取 BITS 任务"""
        import subprocess
        try:
            result = subprocess.run(
                ["bitsadmin", "/list", "/allusers", "/verbose"],
                capture_output=True, text=True, encoding='gbk', timeout=10
            )
            return {'bits_jobs': result.stdout}
        except:
            return {'bits_jobs': ''}
    
    def get_powershell_profiles(self):
        """检查 PowerShell 配置文件"""
        profiles = {}
        profile_paths = [
            Path.home() / "Documents/WindowsPowerShell/profile.ps1",
            Path.home() / "Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1",
            Path.home() / "Documents/PowerShell/profile.ps1",
            Path("C:/Windows/System32/WindowsPowerShell/v1.0/profile.ps1"),
        ]
        
        for path in profile_paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    profiles[str(path)] = {
                        'size': path.stat().st_size,
                        'modified': path.stat().st_mtime,
                        'content_preview': content[:500]
                    }
                except:
                    pass
        
        return profiles
    
    def get_drivers(self):
        """获取已加载的驱动程序"""
        import subprocess
        try:
            result = subprocess.run(
                ["driverquery", "/v", "/fo", "csv"],
                capture_output=True, text=True, encoding='gbk', timeout=30
            )
            drivers = {}
            lines = result.stdout.split('\n')
            
            for line in lines[1:]:
                if line.strip():
                    parts = [p.strip('"') for p in line.split('","')]
                    if len(parts) > 1:
                        drivers[parts[0]] = {
                            'display_name': parts[1] if len(parts) > 1 else '',
                            'type': parts[2] if len(parts) > 2 else '',
                            'status': parts[4] if len(parts) > 4 else ''
                        }
            
            return drivers
        except Exception as e:
            print(f"[!] 获取驱动列表失败: {e}")
            return {}
    
    def take_snapshot(self):
        """获取完整系统快照"""
        print("[*] 正在获取系统快照...")
        
        snapshot = {
            'timestamp': datetime.now().isoformat(),
        }
        
        # 并发执行各个检测任务
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                'registry_autorun': executor.submit(self.registry_monitor.get_snapshot),
                'services': executor.submit(self.service_monitor.get_snapshot),
                'scheduled_tasks': executor.submit(self.task_monitor.get_snapshot),
                'startup_folders': executor.submit(self.get_startup_folder_items),
                'wmi_persistence': executor.submit(self.get_wmi_persistence),
                'running_processes': executor.submit(self.process_monitor.get_snapshot),
                'network_connections': executor.submit(self.network_monitor.get_snapshot),
                'bits_jobs': executor.submit(self.get_bits_jobs),
                'powershell_profiles': executor.submit(self.get_powershell_profiles),
                'drivers': executor.submit(self.get_drivers),
            }
            
            for key, future in futures.items():
                try:
                    snapshot[key] = future.result(timeout=30)
                except Exception as e:
                    print(f"[!] 获取 {key} 失败: {e}")
                    snapshot[key] = {}
        
        print(f"[+] 快照完成:")
        print(f"    - 注册表项: {len(snapshot.get('registry_autorun', {}))}")
        print(f"    - 服务: {len(snapshot.get('services', {}))}")
        print(f"    - 计划任务: {len(snapshot.get('scheduled_tasks', {}))}")
        print(f"    - 启动项: {len(snapshot.get('startup_folders', {}))}")
        print(f"    - 运行进程: {len(snapshot.get('running_processes', {}))}")
        print(f"    - 网络连接: {len(snapshot.get('network_connections', {}))}")
        print(f"    - 驱动程序: {len(snapshot.get('drivers', {}))}")
        
        return snapshot
    
    @staticmethod
    def compare_snapshots(before, after, file_changes=None):
        """比较两个快照"""
        print("[*] 分析差异...")
        
        differences = {
            'added': {},
            'removed': {},
            'modified': {}
        }
        
        # 比较各个模块
        categories = [
            ('registry_autorun', RegistryMonitor.compare),
            ('services', ServiceMonitor.compare),
            ('scheduled_tasks', TaskMonitor.compare),
            ('running_processes', ProcessMonitor.compare),
            ('network_connections', NetworkMonitor.compare),
        ]
        
        for category, compare_func in categories:
            before_items = before.get(category, {})
            after_items = after.get(category, {})
            
            result = compare_func(before_items, after_items)
            
            if result['added']:
                differences['added'][category] = result['added']
            if result['removed']:
                differences['removed'][category] = result['removed']
            if result.get('modified'):
                differences['modified'][category] = result['modified']
        
        # 简单比较的类别
        simple_categories = ['startup_folders', 'bits_jobs', 'powershell_profiles', 'drivers']
        for category in simple_categories:
            before_items = before.get(category, {})
            after_items = after.get(category, {})
            
            added = {k: v for k, v in after_items.items() if k not in before_items}
            removed = {k: v for k, v in before_items.items() if k not in after_items}
            
            if added:
                differences['added'][category] = added
            if removed:
                differences['removed'][category] = removed
        
        # 添加 ETW 文件变化
        if file_changes:
            if file_changes.get('created'):
                differences['added']['filesystem'] = file_changes['created']
            if file_changes.get('deleted'):
                differences['removed']['filesystem'] = file_changes['deleted']
            if file_changes.get('modified'):
                differences['modified']['filesystem'] = file_changes['modified']
        
        # WMI 特殊处理
        if before.get('wmi_persistence') != after.get('wmi_persistence'):
            differences['modified']['wmi_persistence'] = {
                'before': before.get('wmi_persistence', {}),
                'after': after.get('wmi_persistence', {})
            }
        
        return differences