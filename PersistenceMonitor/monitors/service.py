"""服务监控模块"""

import subprocess


class ServiceMonitor:
    """Windows 服务监控"""
    
    def __init__(self):
        pass
    
    def get_services(self):
        """获取系统服务列表"""
        try:
            result = subprocess.run(
                ["sc", "query", "type=", "service", "state=", "all"],
                capture_output=True, text=True, encoding='gbk', timeout=30
            )
            services = {}
            lines = result.stdout.split('\n')
            current_service = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('SERVICE_NAME:'):
                    current_service = line.split(':', 1)[1].strip()
                    services[current_service] = {}
                elif current_service and ':' in line:
                    key, value = line.split(':', 1)
                    services[current_service][key.strip()] = value.strip()
            
            # 获取服务详细配置
            for service_name in list(services.keys()):
                try:
                    config_result = subprocess.run(
                        ["sc", "qc", service_name],
                        capture_output=True, text=True, encoding='gbk', timeout=2
                    )
                    for line in config_result.stdout.split('\n'):
                        line = line.strip()
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            if key in ['BINARY_PATH_NAME', 'DISPLAY_NAME', 'START_TYPE', 'SERVICE_START_NAME']:
                                services[service_name][key] = value.strip()
                except:
                    pass
            
            return services
        except Exception as e:
            print(f"[!] 获取服务列表失败: {e}")
            return {}
    
    def get_snapshot(self):
        """获取快照"""
        return self.get_services()
    
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