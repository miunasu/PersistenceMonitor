"""计划任务监控模块"""

import subprocess


class TaskMonitor:
    """计划任务监控"""
    
    def __init__(self):
        pass
    
    def get_scheduled_tasks(self):
        """获取计划任务列表"""
        try:
            result = subprocess.run(
                ["schtasks", "/query", "/fo", "CSV", "/v"],
                capture_output=True, text=True, encoding='gbk', timeout=30
            )
            tasks = {}
            lines = result.stdout.split('\n')
            
            # 解析 CSV 格式
            headers = []
            first_data_line = True
            for line in lines:
                if not line.strip():
                    continue
                parts = [p.strip('"') for p in line.split('","')]
                if first_data_line:
                    headers = parts
                    first_data_line = False
                else:
                    if len(parts) > 1:
                        # 任务名在第2列（索引1），第1列是主机名
                        task_name = parts[1] if len(parts) > 1 else parts[0]
                        task_info = {}
                        for j, header in enumerate(headers):
                            if j < len(parts):
                                task_info[header] = parts[j]
                        tasks[task_name] = task_info
            
            return tasks
        except Exception as e:
            print(f"[!] 获取计划任务失败: {e}")
            return {}
    
    def get_snapshot(self):
        """获取快照"""
        return self.get_scheduled_tasks()
    
    @staticmethod
    def compare(before, after):
        """比较两个快照"""
        added = {k: v for k, v in after.items() if k not in before}
        removed = {k: v for k, v in before.items() if k not in after}
        modified = {}
        
        for k in before:
            if k in after and before[k] != after[k]:
                modified[k] = {'before': before[k], 'after': after[k]}
        
        return {'added': added, 'removed': removed, 'modified': modified}