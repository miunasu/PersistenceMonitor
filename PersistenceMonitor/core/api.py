"""Windows ETW API 封装"""

import ctypes
from ctypes import POINTER, byref, sizeof, cast, c_void_p
from ctypes import c_ulonglong, c_ulong, c_ubyte

from .structures import (
    GUID, EVENT_TRACE_PROPERTIES, EVENT_TRACE_LOGFILEW,
    PEVENT_RECORD_CALLBACK
)
from .constants import (
    WNODE_FLAG_TRACED_GUID, EVENT_TRACE_REAL_TIME_MODE,
    PROCESS_TRACE_MODE_REAL_TIME, PROCESS_TRACE_MODE_EVENT_RECORD,
    EVENT_TRACE_CONTROL_STOP, INVALID_PROCESSTRACE_HANDLE
)


# Windows DLL
advapi32 = ctypes.windll.advapi32
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

# ETW API
StartTraceW = advapi32.StartTraceW
StartTraceW.argtypes = [POINTER(c_ulonglong), ctypes.c_wchar_p, POINTER(EVENT_TRACE_PROPERTIES)]
StartTraceW.restype = c_ulong

ControlTraceW = advapi32.ControlTraceW
ControlTraceW.argtypes = [c_ulonglong, ctypes.c_wchar_p, POINTER(EVENT_TRACE_PROPERTIES), c_ulong]
ControlTraceW.restype = c_ulong

EnableTraceEx2 = advapi32.EnableTraceEx2
EnableTraceEx2.argtypes = [c_ulonglong, POINTER(GUID), c_ulong, c_ubyte, c_ulonglong, c_ulonglong, c_ulong, c_void_p]
EnableTraceEx2.restype = c_ulong

OpenTraceW = advapi32.OpenTraceW
OpenTraceW.argtypes = [POINTER(EVENT_TRACE_LOGFILEW)]
OpenTraceW.restype = c_ulonglong

ProcessTrace = advapi32.ProcessTrace
ProcessTrace.argtypes = [POINTER(c_ulonglong), c_ulong, c_void_p, c_void_p]
ProcessTrace.restype = c_ulong

CloseTrace = advapi32.CloseTrace
CloseTrace.argtypes = [c_ulonglong]
CloseTrace.restype = c_ulong

# Process API
OpenProcess = kernel32.OpenProcess
CloseHandle = kernel32.CloseHandle
GetProcessImageFileNameW = psapi.GetProcessImageFileNameW


def is_admin():
    """检查是否有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def stop_trace_session(session_name):
    """停止指定的跟踪会话"""
    try:
        size = sizeof(EVENT_TRACE_PROPERTIES) + 1024
        buf = ctypes.create_string_buffer(size)
        props = cast(buf, POINTER(EVENT_TRACE_PROPERTIES)).contents
        props.Wnode.BufferSize = size
        props.LoggerNameOffset = sizeof(EVENT_TRACE_PROPERTIES)
        return ControlTraceW(0, session_name, byref(props), EVENT_TRACE_CONTROL_STOP)
    except:
        return -1


def create_trace_properties(session_guid, buffer_size=64, min_buffers=4, max_buffers=64):
    """创建跟踪属性结构"""
    size = sizeof(EVENT_TRACE_PROPERTIES) + 1024
    props_buf = ctypes.create_string_buffer(size)
    props = cast(props_buf, POINTER(EVENT_TRACE_PROPERTIES)).contents
    
    props.Wnode.BufferSize = size
    props.Wnode.Flags = WNODE_FLAG_TRACED_GUID
    props.Wnode.ClientContext = 1  # QPC
    props.Wnode.Guid = session_guid
    props.BufferSize = buffer_size
    props.MinimumBuffers = min_buffers
    props.MaximumBuffers = max_buffers
    props.LogFileMode = EVENT_TRACE_REAL_TIME_MODE
    props.FlushTimer = 1
    props.LoggerNameOffset = sizeof(EVENT_TRACE_PROPERTIES)
    
    return props_buf, props


def create_logfile_struct(session_name, callback_func):
    """创建日志文件结构"""
    logfile = EVENT_TRACE_LOGFILEW()
    ctypes.memset(ctypes.addressof(logfile), 0, sizeof(EVENT_TRACE_LOGFILEW))
    logfile.LogFileName = None
    logfile.LoggerName = session_name
    logfile.LogFileMode = PROCESS_TRACE_MODE_REAL_TIME | PROCESS_TRACE_MODE_EVENT_RECORD
    logfile.EventRecordCallback = ctypes.cast(callback_func, c_void_p).value
    return logfile


def get_process_name(pid, cache=None):
    """获取进程名称"""
    if cache is not None and pid in cache:
        return cache[pid]
    
    if pid < 10:
        name = "System"
        if cache is not None:
            cache[pid] = name
        return name
    
    try:
        from .constants import PROCESS_QUERY_LIMITED_INFORMATION
        h = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if h:
            import os
            buf = ctypes.create_unicode_buffer(260)
            if GetProcessImageFileNameW(h, buf, 260):
                name = os.path.basename(buf.value)
                CloseHandle(h)
                if cache is not None:
                    cache[pid] = name
                return name
            CloseHandle(h)
    except:
        pass
    
    name = f"PID:{pid}"
    if cache is not None:
        cache[pid] = name
    return name