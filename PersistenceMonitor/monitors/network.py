"""网络连接监控模块"""

import subprocess
import os


class NetworkMonitor:
    """网络连接监控"""
    
    def __init__(self):
        self._process_cache = {}
    
    def _get_process_name_by_pid(self, pid):
        """通过 PID 获取进程名"""
        if not pid or pid == '0':
            return 'System'
        
        pid_str = str(pid)
        if pid_str in self._process_cache:
            return self._process_cache[pid_str]
        
        try:
            # 使用 tasklist 查询进程名
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, encoding='gbk', timeout=5
            )
            output = result.stdout.strip()
            if output and ',' in output:
                # 格式: "进程名","PID","会话名","会话#","内存使用"
                parts = output.split(',')
                if parts:
                    name = parts[0].strip('"')
                    self._process_cache[pid_str] = name
                    return name
        except:
            pass
        
        self._process_cache[pid_str] = f'PID:{pid}'
        return f'PID:{pid}'
    
    def get_network_connections(self):
        """获取网络连接（包含进程名）"""
        try:
            # 先尝试使用 netstat -anob（需要管理员权限，直接显示进程名）
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True, encoding='gbk', timeout=30
            )
            
            connections = {}
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and ('TCP' in line or 'UDP' in line):
                    parts = line.split()
                    if len(parts) >= 4:
                        protocol = parts[0]
                        local_addr = parts[1]
                        
                        if protocol == 'TCP' and len(parts) >= 5:
                            remote_addr = parts[2]
                            state = parts[3]
                            pid = parts[4]
                        else:
                            remote_addr = parts[2] if len(parts) > 2 else '*:*'
                            state = 'N/A'
                            pid = parts[3] if len(parts) > 3 else '0'
                        
                        # 获取进程名
                        process_name = self._get_process_name_by_pid(pid)
                        
                        conn_key = f"{protocol}_{local_addr}_{remote_addr}_{pid}"
                        connections[conn_key] = {
                            'protocol': protocol,
                            'local': local_addr,
                            'remote': remote_addr,
                            'state': state,
                            'pid': pid,
                            'process_name': process_name
                        }
            
            return connections
        except Exception as e:
            print(f"[!] 获取网络连接失败: {e}")
            return {}
    
    def get_connections_with_process(self):
        """获取网络连接（使用 PowerShell 获取更详细信息）"""
        try:
            # 使用 PowerShell 获取更详细的网络连接信息
            ps_cmd = '''
            Get-NetTCPConnection | Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State,OwningProcess,@{Name='ProcessName';Expression={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}} | ConvertTo-Csv -NoTypeInformation
            '''
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=30
            )
            
            connections = {}
            lines = result.stdout.strip().split('\n')
            
            if len(lines) > 1:
                # 跳过标题行
                for line in lines[1:]:
                    if line.strip():
                        parts = [p.strip('"') for p in line.split('","')]
                        if len(parts) >= 7:
                            local_addr = f"{parts[0]}:{parts[1]}"
                            remote_addr = f"{parts[2]}:{parts[3]}"
                            state = parts[4]
                            pid = parts[5]
                            process_name = parts[6] if parts[6] else f'PID:{pid}'
                            
                            conn_key = f"TCP_{local_addr}_{remote_addr}_{pid}"
                            connections[conn_key] = {
                                'protocol': 'TCP',
                                'local': local_addr,
                                'remote': remote_addr,
                                'state': state,
                                'pid': pid,
                                'process_name': process_name
                            }
            
            # 也获取 UDP 连接
            ps_cmd_udp = '''
            Get-NetUDPEndpoint | Select-Object LocalAddress,LocalPort,OwningProcess,@{Name='ProcessName';Expression={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}} | ConvertTo-Csv -NoTypeInformation
            '''
            result_udp = subprocess.run(
                ["powershell", "-Command", ps_cmd_udp],
                capture_output=True, text=True, timeout=30
            )
            
            lines_udp = result_udp.stdout.strip().split('\n')
            if len(lines_udp) > 1:
                for line in lines_udp[1:]:
                    if line.strip():
                        parts = [p.strip('"') for p in line.split('","')]
                        if len(parts) >= 4:
                            local_addr = f"{parts[0]}:{parts[1]}"
                            pid = parts[2]
                            process_name = parts[3] if parts[3] else f'PID:{pid}'
                            
                            conn_key = f"UDP_{local_addr}_*:*_{pid}"
                            connections[conn_key] = {
                                'protocol': 'UDP',
                                'local': local_addr,
                                'remote': '*:*',
                                'state': 'N/A',
                                'pid': pid,
                                'process_name': process_name
                            }
            
            return connections
        except Exception as e:
            print(f"[!] PowerShell 获取网络连接失败: {e}")
            # 回退到普通方法
            return self.get_network_connections()
    
    def get_snapshot(self):
        """获取快照"""
        return self.get_network_connections()
    
    @staticmethod
    def filter_noise(connections):
        """过滤网络连接噪音"""
        filtered = {}
        # 常见系统进程（可以选择过滤或保留）
        system_processes = {'svchost.exe', 'System', 'lsass.exe', 'services.exe'}
        
        for key, info in connections.items():
            remote = info.get('remote', '')
            process_name = info.get('process_name', '')
            
            # 过滤本地连接
            if remote.startswith('127.0.0.1:') or remote.startswith('[::1]:'):
                continue
            if remote in ['0.0.0.0:0', '*:*', '0.0.0.0:*', '::']:
                continue
            # 过滤 IPv6 本地
            if remote.startswith('[::'):
                continue
            
            # 可选：过滤系统进程的监听端口
            # if process_name in system_processes and info.get('state') == 'LISTENING':
            #     continue
            
            filtered[key] = info
        return filtered
    
    @staticmethod
    def compare(before, after):
        """比较两个快照"""
        # 过滤噪音后比较
        before_filtered = NetworkMonitor.filter_noise(before)
        after_filtered = NetworkMonitor.filter_noise(after)
        
        added = {k: v for k, v in after_filtered.items() if k not in before_filtered}
        removed = {k: v for k, v in before_filtered.items() if k not in after_filtered}
        
        return {'added': added, 'removed': removed, 'modified': {}}
    
    @staticmethod
    def format_connection(info):
        """格式化连接信息用于显示"""
        return (f"{info['protocol']} {info['local']} -> {info['remote']} "
                f"[{info['state']}] {info['process_name']} (PID:{info['pid']})")


# 测试代码
if __name__ == "__main__":
    print("网络连接监控测试")
    print("=" * 60)
    
    monitor = NetworkMonitor()
    connections = monitor.get_network_connections()
    
    print(f"\n共 {len(connections)} 个连接")
    
    # 过滤后显示
    filtered = NetworkMonitor.filter_noise(connections)
    print(f"过滤后 {len(filtered)} 个连接\n")
    
    print("外部连接:")
    for key, info in list(filtered.items())[:20]:
        print(f"  {NetworkMonitor.format_connection(info)}")