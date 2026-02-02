"""进程监控模块"""

import subprocess


class ProcessMonitor:
    """进程监控"""
    
    def __init__(self):
        pass
    
    def get_running_processes(self):
        """获取运行中的进程列表"""
        try:
            result = subprocess.run(
                ["tasklist", "/v", "/fo", "csv"],
                capture_output=True, text=True, encoding='gbk', timeout=30
            )
            processes = {}
            lines = result.stdout.split('\n')
            
            for line in lines[1:]:
                if line.strip():
                    parts = [p.strip('"') for p in line.split('","')]
                    if len(parts) > 1:
                        name = parts[0].strip('"')
                        processes[f"{name}_{parts[1]}"] = {
                            'name': name,
                            'pid': parts[1] if len(parts) > 1 else '',
                            'session': parts[2] if len(parts) > 2 else '',
                            'session_num': parts[3] if len(parts) > 3 else '',
                            'mem': parts[4] if len(parts) > 4 else '',
                            'status': parts[5] if len(parts) > 5 else '',
                            'user': parts[6] if len(parts) > 6 else '',
                        }
            
            return processes
        except Exception as e:
            print(f"[!] 获取进程列表失败: {e}")
            return {}
    
    def get_snapshot(self):
        """获取快照"""
        return self.get_running_processes()
    
    @staticmethod
    def compare(before, after):
        """比较两个快照"""
        # 进程比较只看新增的
        added = {}
        for k, v in after.items():
            # 按进程名比较，忽略 PID
            name = v.get('name', '')
            found = False
            for bk, bv in before.items():
                if bv.get('name', '') == name:
                    found = True
                    break
            if not found:
                added[k] = v
        
        return {'added': added, 'removed': {}, 'modified': {}}