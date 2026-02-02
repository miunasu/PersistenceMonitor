"""报告生成模块"""

import os
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.constants import HIGH_RISK_EXTENSIONS


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        pass
    
    def print_differences(self, differences):
        """打印差异报告到控制台"""
        print("\n" + "=" * 80)
        print("持久化机制变化检测报告")
        print("=" * 80)
        
        has_changes = False
        
        # 新增项
        if differences['added']:
            has_changes = True
            print("\n[!] 检测到新增的持久化机制:")
            print("-" * 80)
            for category, items in differences['added'].items():
                print(f"\n  [{category.upper()}] - 新增 {len(items)} 项:")
                for key, value in list(items.items())[:10]:
                    print(f"    + {key}")
                    if isinstance(value, dict):
                        if 'process_name' in value:
                            print(f"        进程: {value['process_name']} (PID: {value.get('process_id', 'N/A')})")
                        for k, v in list(value.items())[:3]:
                            if k not in ['process_name', 'process_id', 'events']:
                                print(f"        {k}: {v}")
                if len(items) > 10:
                    print(f"    ... 还有 {len(items) - 10} 项")
        
        # 删除项
        if differences['removed']:
            has_changes = True
            print("\n[*] 检测到删除的项:")
            print("-" * 80)
            for category, items in differences['removed'].items():
                print(f"\n  [{category.upper()}] - 删除 {len(items)} 项:")
                for key in list(items.keys())[:10]:
                    print(f"    - {key}")
                if len(items) > 10:
                    print(f"    ... 还有 {len(items) - 10} 项")
        
        # 修改项
        if differences['modified']:
            has_changes = True
            print("\n[*] 检测到修改的项:")
            print("-" * 80)
            for category, items in differences['modified'].items():
                print(f"\n  [{category.upper()}] - 修改 {len(items)} 项:")
                for key in list(items.keys())[:5]:
                    print(f"    ~ {key}")
                if len(items) > 5:
                    print(f"    ... 还有 {len(items) - 5} 项")
        
        if not has_changes:
            print("\n[+] 未检测到持久化机制变化")
        
        print("\n" + "=" * 80)
    
    def save_report(self, differences, exe_name, output_dir=None):
        """保存报告到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exe_basename = Path(exe_name).stem
        
        if output_dir:
            report_dir = Path(output_dir)
        else:
            report_dir = Path(f"persistence_report_{exe_basename}_{timestamp}")
        
        report_dir.mkdir(exist_ok=True)
        
        print(f"\n[+] 正在生成报告到目录: {report_dir}/")
        
        # 保存总览
        self._save_summary(report_dir, exe_name, timestamp, differences)
        
        # 保存详细报告
        if differences['added']:
            self._save_added_items(report_dir, differences['added'])
        if differences['removed']:
            self._save_removed_items(report_dir, differences['removed'])
        if differences['modified']:
            self._save_modified_items(report_dir, differences['modified'])
        
        print(f"[+] 报告生成完成: {report_dir}/")
        return str(report_dir)
    
    def _save_summary(self, report_dir, exe_name, timestamp, differences):
        """保存总览报告"""
        summary_file = report_dir / "00_SUMMARY.txt"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("持久化监控报告 - 总览 (ETW 增强版)\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"分析目标: {exe_name}\n")
            f.write(f"分析时间: {timestamp}\n")
            f.write(f"报告生成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 统计
            f.write("-" * 80 + "\n")
            f.write("变化统计:\n")
            f.write("-" * 80 + "\n")
            
            total_added = sum(len(items) for items in differences['added'].values())
            total_removed = sum(len(items) for items in differences['removed'].values())
            total_modified = sum(len(items) for items in differences['modified'].values())
            
            f.write(f"新增项: {total_added}\n")
            f.write(f"删除项: {total_removed}\n")
            f.write(f"修改项: {total_modified}\n\n")
            
            if differences['added']:
                f.write("新增项详情:\n")
                for category, items in differences['added'].items():
                    f.write(f"  - {category}: {len(items)} 项\n")
                f.write("\n")
            
            # 风险评估
            f.write("-" * 80 + "\n")
            f.write("风险评估:\n")
            f.write("-" * 80 + "\n")
            
            high_risk = ['registry_autorun', 'services', 'scheduled_tasks', 'wmi_persistence', 'drivers']
            has_high_risk = any(cat in differences['added'] for cat in high_risk)
            
            if has_high_risk:
                f.write("[!] 检测到高风险持久化机制变化!\n\n")
                for cat in high_risk:
                    if cat in differences['added']:
                        f.write(f"  - {cat}: {len(differences['added'][cat])} 项\n")
            
            if 'filesystem' in differences['added']:
                f.write(f"\n[*] 文件系统变化 (ETW 捕获):\n")
                f.write(f"  - 新增文件: {len(differences['added']['filesystem'])} 个\n")
                
                # 统计高风险文件
                high_risk_files = []
                for path in differences['added']['filesystem'].keys():
                    ext = os.path.splitext(path)[1].lower()
                    if ext in HIGH_RISK_EXTENSIONS:
                        high_risk_files.append(path)
                
                if high_risk_files:
                    f.write(f"  - 高风险文件: {len(high_risk_files)} 个\n")
                    for path in high_risk_files[:5]:
                        f.write(f"      {path}\n")
            
            if not has_high_risk and 'filesystem' not in differences['added']:
                f.write("[+] 未检测到明显的高风险持久化机制\n")
            
            f.write("\n" + "=" * 80 + "\n")
    
    def _save_added_items(self, report_dir, added_items):
        """保存新增项报告"""
        for category, items in added_items.items():
            filename = report_dir / f"ADDED_{category}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"新增项 - {category}\n")
                f.write("=" * 80 + "\n")
                f.write(f"共 {len(items)} 项\n\n")
                
                if category == 'filesystem':
                    f.write("[*] 文件变化由 ETW 实时捕获\n\n")
                    
                    for i, (path, info) in enumerate(items.items(), 1):
                        f.write(f"[{i}] {path}\n")
                        f.write("-" * 80 + "\n")
                        if isinstance(info, dict):
                            if 'process_name' in info:
                                f.write(f"  创建进程: {info['process_name']}\n")
                            if 'process_id' in info:
                                f.write(f"  进程 PID: {info['process_id']}\n")
                            if 'was_temporary' in info:
                                f.write(f"  临时文件: {'是' if info['was_temporary'] else '否'}\n")
                        f.write("\n")
                else:
                    for i, (key, value) in enumerate(items.items(), 1):
                        f.write(f"[{i}] {key}\n")
                        f.write("-" * 80 + "\n")
                        if isinstance(value, dict):
                            for k, v in value.items():
                                if k != 'events':
                                    f.write(f"  {k}: {v}\n")
                        else:
                            f.write(f"  值: {value}\n")
                        f.write("\n")
    
    def _save_removed_items(self, report_dir, removed_items):
        """保存删除项报告"""
        for category, items in removed_items.items():
            filename = report_dir / f"REMOVED_{category}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"删除项 - {category}\n")
                f.write("=" * 80 + "\n")
                f.write(f"共 {len(items)} 项\n\n")
                
                for i, (key, value) in enumerate(items.items(), 1):
                    f.write(f"[{i}] {key}\n")
                    f.write("-" * 80 + "\n")
                    if isinstance(value, dict):
                        for k, v in value.items():
                            if k != 'events':
                                f.write(f"  {k}: {v}\n")
                    f.write("\n")
    
    def _save_modified_items(self, report_dir, modified_items):
        """保存修改项报告"""
        for category, items in modified_items.items():
            filename = report_dir / f"MODIFIED_{category}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"修改项 - {category}\n")
                f.write("=" * 80 + "\n")
                f.write(f"共 {len(items)} 项\n\n")
                
                for i, (key, changes) in enumerate(items.items(), 1):
                    f.write(f"[{i}] {key}\n")
                    f.write("-" * 80 + "\n")
                    if isinstance(changes, dict) and 'before' in changes:
                        f.write("  修改前:\n")
                        if isinstance(changes['before'], dict):
                            for k, v in changes['before'].items():
                                f.write(f"    {k}: {v}\n")
                        else:
                            f.write(f"    {changes['before']}\n")
                        f.write("  修改后:\n")
                        if isinstance(changes['after'], dict):
                            for k, v in changes['after'].items():
                                f.write(f"    {k}: {v}\n")
                        else:
                            f.write(f"    {changes['after']}\n")
                    f.write("\n")