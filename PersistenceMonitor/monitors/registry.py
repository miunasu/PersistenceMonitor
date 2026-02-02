"""注册表监控模块"""

import winreg


class RegistryMonitor:
    """注册表自启动项监控"""
    
    # 自启动注册表键
    AUTORUN_KEYS = [
        # HKEY_CURRENT_USER
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon"),
        
        # HKEY_LOCAL_MACHINE
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunServices"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunServicesOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon"),
        
        # WOW6432Node
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce"),
        
        # 高级持久化位置
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows NT\CurrentVersion\Windows"),
        (winreg.HKEY_LOCAL_MACHINE, r"System\CurrentControlSet\Services"),
        (winreg.HKEY_LOCAL_MACHINE, r"System\CurrentControlSet\Control\Lsa"),
        (winreg.HKEY_LOCAL_MACHINE, r"System\CurrentControlSet\Control\Print\Monitors"),
        (winreg.HKEY_LOCAL_MACHINE, r"System\CurrentControlSet\Control\Session Manager\AppCertDlls"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\NetSh"),
    ]
    
    HIVE_NAMES = {
        winreg.HKEY_CURRENT_USER: "HKCU",
        winreg.HKEY_LOCAL_MACHINE: "HKLM",
        winreg.HKEY_CLASSES_ROOT: "HKCR",
        winreg.HKEY_USERS: "HKU",
    }
    
    def __init__(self):
        pass
    
    def _get_hive_name(self, hive):
        """获取注册表根键名称"""
        return self.HIVE_NAMES.get(hive, "UNKNOWN")
    
    def get_autorun_items(self):
        """获取所有自启动项"""
        results = {}
        
        for hive, key_path in self.AUTORUN_KEYS:
            try:
                key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, value, value_type = winreg.EnumValue(key, i)
                        full_path = f"{self._get_hive_name(hive)}\\{key_path}\\{name}"
                        results[full_path] = {
                            'value': str(value),
                            'type': value_type,
                            'hive': self._get_hive_name(hive),
                            'key': key_path,
                            'name': name
                        }
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except (FileNotFoundError, PermissionError, OSError):
                pass
        
        return results
    
    def get_snapshot(self):
        """获取快照"""
        return self.get_autorun_items()
    
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