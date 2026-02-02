"""ETW 文件监控模块"""

import ctypes
from ctypes import POINTER, byref, sizeof, cast, c_void_p, c_ulonglong, c_ubyte
import threading
import time
from datetime import datetime
from collections import defaultdict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.constants import (
    EVENT_CONTROL_CODE_ENABLE_PROVIDER, EVENT_CONTROL_CODE_DISABLE_PROVIDER,
    TRACE_LEVEL_VERBOSE, INVALID_PROCESSTRACE_HANDLE,
    EVENT_ID_NAMECREATE, EVENT_ID_NAMEDELETE, EVENT_ID_CREATE,
    EVENT_ID_WRITE, EVENT_ID_DELETE, EVENT_ID_RENAME,
    EVENT_NAMES, INTERESTING_FILE_EVENTS, NOISE_PATH_PATTERNS,
    DEFAULT_SESSION_NAME
)
from core.structures import (
    GUID, EVENT_TRACE_PROPERTIES, EVENT_TRACE_LOGFILEW,
    PEVENT_RECORD_CALLBACK, KERNEL_FILE_PROVIDER_GUID, DEFAULT_SESSION_GUID
)
from core.api import (
    StartTraceW, ControlTraceW, EnableTraceEx2, OpenTraceW,
    ProcessTrace, CloseTrace, stop_trace_session,
    create_trace_properties, create_logfile_struct, get_process_name
)


class FileEvent:
    """文件事件"""
    def __init__(self, event_type, file_path, process_id, process_name, timestamp):
        self.event_type = event_type
        self.file_path = file_path
        self.process_id = process_id
        self.process_name = process_name
        self.timestamp = timestamp
    
    def to_dict(self):
        return {
            'event_type': self.event_type,
            'file_path': self.file_path,
            'process_id': self.process_id,
            'process_name': self.process_name,
            'timestamp': str(self.timestamp)
        }
    
    def __repr__(self):
        return f"FileEvent({self.event_type}, {self.file_path}, PID={self.process_id})"


class ETWFileMonitor:
    """ETW 文件监控器"""
    
    def __init__(self, session_name=None):
        self.session_name = session_name or DEFAULT_SESSION_NAME
        self.session_handle = c_ulonglong(0)
        self.trace_handle = c_ulonglong(0)
        self.is_running = False
        self.events = []
        self.events_lock = threading.Lock()
        self.process_thread = None
        self.process_cache = {}
        self.event_count = 0
        
        # 必须保持引用防止垃圾回收
        self._callback_func = None
        self._logfile_struct = None
        self._props_buf = None
    
    def _should_filter(self, path):
        """检查是否应该过滤该路径"""
        if not path:
            return True
        upper = path.upper()
        for noise in NOISE_PATH_PATTERNS:
            if noise in upper:
                return True
        # 过滤只有驱动器根目录的路径
        if path.endswith('\\') and len(path) < 30:
            return True
        return False
    
    def _parse_file_path(self, user_data, length, event_id):
        """解析文件路径"""
        if not user_data or length < 8:
            return None
        
        try:
            raw = (c_ubyte * length).from_address(user_data)
            data = bytes(raw)
            
            # NameCreate/NameDelete (Id=10,11): FileObject(8) + FileName
            if event_id in (EVENT_ID_NAMECREATE, EVENT_ID_NAMEDELETE):
                if length > 8:
                    text = data[8:].decode('utf-16-le', errors='ignore').split('\x00')[0]
                    if text and len(text) > 1:
                        return text
            
            # Create (Id=12): 复杂结构，路径在偏移32
            elif event_id == EVENT_ID_CREATE:
                if length > 32:
                    text = data[32:].decode('utf-16-le', errors='ignore').split('\x00')[0]
                    if text and len(text) > 1 and ('\\' in text or ':' in text):
                        return text
                # 备选偏移
                for offset in [40, 24, 16, 8]:
                    if length > offset:
                        text = data[offset:].decode('utf-16-le', errors='ignore').split('\x00')[0]
                        if text and len(text) > 2 and ('\\' in text or ':' in text):
                            return text
            
            # 其他事件
            else:
                for offset in [8, 16, 24, 32, 0]:
                    if length > offset + 4:
                        text = data[offset:].decode('utf-16-le', errors='ignore').split('\x00')[0]
                        if text and len(text) > 2 and ('\\' in text or ':' in text):
                            return text
            
            return None
        except:
            return None
    
    def _event_callback(self, event_ptr):
        """ETW 事件回调"""
        if not self.is_running:
            return
        
        try:
            self.event_count += 1
            ev = event_ptr.contents
            event_id = ev.EventHeader.EventDescriptor.Id
            pid = ev.EventHeader.ProcessId
            
            # 只处理感兴趣的事件
            if event_id not in INTERESTING_FILE_EVENTS:
                return
            
            # 跳过系统进程
            if pid < 10:
                return
            
            path = self._parse_file_path(ev.UserData, ev.UserDataLength, event_id)
            
            if not path or self._should_filter(path):
                return
            
            etype = EVENT_NAMES.get(event_id, f'unknown_{event_id}')
            pname = get_process_name(pid, self.process_cache)
            
            fe = FileEvent(etype, path, pid, pname, datetime.now())
            
            with self.events_lock:
                self.events.append(fe)
                
        except:
            pass
    
    def _trace_thread(self):
        """处理跟踪的线程"""
        try:
            handle_value = self.trace_handle.value
            if handle_value == 0 or handle_value == INVALID_PROCESSTRACE_HANDLE:
                return
            
            handle_array = (c_ulonglong * 1)(handle_value)
            ProcessTrace(handle_array, 1, None, None)
        except:
            pass
    
    def start(self):
        """启动监控"""
        if self.is_running:
            return True
        
        print("[*] 启动 ETW 文件监控...")
        
        # 停止可能存在的旧会话
        stop_trace_session(self.session_name)
        time.sleep(0.3)
        
        # 创建属性
        self._props_buf, props = create_trace_properties(DEFAULT_SESSION_GUID)
        
        # 启动会话
        ret = StartTraceW(byref(self.session_handle), self.session_name, byref(props))
        if ret != 0:
            if ret == 183:  # ERROR_ALREADY_EXISTS
                stop_trace_session(self.session_name)
                time.sleep(0.5)
                ret = StartTraceW(byref(self.session_handle), self.session_name, byref(props))
            if ret != 0:
                print(f"[!] StartTrace 失败: {ret}")
                return False
        
        print(f"[+] 会话创建成功: {self.session_handle.value}")
        
        # 启用 Provider
        ret = EnableTraceEx2(
            self.session_handle.value,
            byref(KERNEL_FILE_PROVIDER_GUID),
            EVENT_CONTROL_CODE_ENABLE_PROVIDER,
            TRACE_LEVEL_VERBOSE,
            0xFFFFFFFFFFFFFFFF,  # 所有关键字
            0, 0, None
        )
        if ret != 0:
            print(f"[!] EnableTraceEx2 失败: {ret}")
            self.stop()
            return False
        
        print("[+] Provider 已启用")
        
        # 创建回调
        self._callback_func = PEVENT_RECORD_CALLBACK(self._event_callback)
        
        # 创建 LOGFILE 结构
        self._logfile_struct = create_logfile_struct(self.session_name, self._callback_func)
        
        # 打开跟踪
        trace_handle_value = OpenTraceW(byref(self._logfile_struct))
        if trace_handle_value == INVALID_PROCESSTRACE_HANDLE or trace_handle_value == 0:
            print(f"[!] OpenTrace 失败")
            self.stop()
            return False
        
        self.trace_handle.value = trace_handle_value
        print(f"[+] 跟踪已打开: 0x{self.trace_handle.value:X}")
        
        # 启动处理线程
        self.is_running = True
        self.process_thread = threading.Thread(target=self._trace_thread, daemon=True)
        self.process_thread.start()
        
        time.sleep(0.2)
        print("[+] ETW 文件监控已启动")
        return True
    
    def stop(self):
        """停止监控"""
        if not self.is_running and self.session_handle.value == 0:
            return
        
        print("[*] 停止 ETW 监控...")
        self.is_running = False
        
        # 关闭跟踪句柄
        if self.trace_handle.value != 0 and self.trace_handle.value != INVALID_PROCESSTRACE_HANDLE:
            CloseTrace(self.trace_handle.value)
            self.trace_handle.value = 0
        
        # 禁用 Provider
        if self.session_handle.value != 0:
            EnableTraceEx2(
                self.session_handle.value,
                byref(KERNEL_FILE_PROVIDER_GUID),
                EVENT_CONTROL_CODE_DISABLE_PROVIDER,
                0, 0, 0, 0, None
            )
        
        # 停止会话
        stop_trace_session(self.session_name)
        
        # 等待线程结束
        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=3)
        
        self.session_handle.value = 0
        print(f"[+] 已停止, 捕获 {len(self.events)} 个文件事件 (总事件: {self.event_count})")
    
    def get_events(self):
        """获取所有事件"""
        with self.events_lock:
            return list(self.events)
    
    def clear_events(self):
        """清空事件"""
        with self.events_lock:
            self.events.clear()
            self.event_count = 0
    
    def get_file_changes(self):
        """获取文件变化摘要"""
        with self.events_lock:
            changes = {'created': {}, 'deleted': {}, 'modified': {}, 'renamed': {}}
            
            by_path = defaultdict(list)
            for e in self.events:
                by_path[e.file_path].append(e)
            
            for path, evts in by_path.items():
                last = evts[-1]
                types = [e.event_type for e in evts]
                info = {
                    'process_id': last.process_id,
                    'process_name': last.process_name,
                    'events': [e.to_dict() for e in evts]
                }
                
                if 'delete' in types or 'name_delete' in types:
                    info['was_temporary'] = 'create' in types or 'name_create' in types
                    changes['deleted'][path] = info
                elif 'create' in types or 'name_create' in types:
                    changes['created'][path] = info
                elif 'write' in types:
                    info['write_count'] = types.count('write')
                    changes['modified'][path] = info
                elif 'rename' in types:
                    changes['renamed'][path] = info
            
            return changes


# 测试代码
if __name__ == "__main__":
    from core.api import is_admin
    
    if not is_admin():
        print("[!] 请以管理员权限运行")
        exit(1)
    
    print("=" * 50)
    print("ETW 文件监控模块测试")
    print("=" * 50)
    
    m = ETWFileMonitor()
    if m.start():
        print("\n监控中... 5秒后停止\n")
        time.sleep(5)
        m.stop()
        
        c = m.get_file_changes()
        print(f"\n结果: 创建={len(c['created'])}, 删除={len(c['deleted'])}, 修改={len(c['modified'])}")