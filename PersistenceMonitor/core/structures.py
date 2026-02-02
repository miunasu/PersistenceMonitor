"""ETW 结构体定义"""

import ctypes
from ctypes import Structure, POINTER, c_void_p, WINFUNCTYPE
from ctypes import c_ulonglong, c_longlong, c_ulong, c_ushort, c_ubyte, c_wchar_p, c_wchar


class GUID(Structure):
    """GUID 结构体"""
    _fields_ = [
        ("Data1", c_ulong),
        ("Data2", c_ushort),
        ("Data3", c_ushort),
        ("Data4", c_ubyte * 8)
    ]
    
    def __str__(self):
        d4 = bytes(self.Data4)
        return f"{{{self.Data1:08X}-{self.Data2:04X}-{self.Data3:04X}-{d4[:2].hex().upper()}-{d4[2:].hex().upper()}}}"
    
    @classmethod
    def from_string(cls, guid_str):
        """从字符串创建 GUID"""
        guid_str = guid_str.strip('{}')
        parts = guid_str.split('-')
        data1 = int(parts[0], 16)
        data2 = int(parts[1], 16)
        data3 = int(parts[2], 16)
        data4 = bytes.fromhex(parts[3] + parts[4])
        return cls(data1, data2, data3, (c_ubyte * 8)(*data4))


# Microsoft-Windows-Kernel-File Provider GUID
KERNEL_FILE_PROVIDER_GUID = GUID(
    0xEDD08927, 0x9CC4, 0x4E65,
    (c_ubyte * 8)(0xB9, 0x70, 0xC2, 0x56, 0x0F, 0xB5, 0xC2, 0x89)
)

# 默认会话 GUID
DEFAULT_SESSION_GUID = GUID(
    0x12345678, 0x1234, 0x1234,
    (c_ubyte * 8)(0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0)
)


class WNODE_HEADER(Structure):
    """WNODE_HEADER 结构体"""
    _fields_ = [
        ("BufferSize", c_ulong),
        ("ProviderId", c_ulong),
        ("HistoricalContext", c_ulonglong),
        ("TimeStamp", c_longlong),
        ("Guid", GUID),
        ("ClientContext", c_ulong),
        ("Flags", c_ulong)
    ]


class EVENT_TRACE_PROPERTIES(Structure):
    """EVENT_TRACE_PROPERTIES 结构体"""
    _fields_ = [
        ("Wnode", WNODE_HEADER),
        ("BufferSize", c_ulong),
        ("MinimumBuffers", c_ulong),
        ("MaximumBuffers", c_ulong),
        ("MaximumFileSize", c_ulong),
        ("LogFileMode", c_ulong),
        ("FlushTimer", c_ulong),
        ("EnableFlags", c_ulong),
        ("AgeLimit", c_ulong),
        ("NumberOfBuffers", c_ulong),
        ("FreeBuffers", c_ulong),
        ("EventsLost", c_ulong),
        ("BuffersWritten", c_ulong),
        ("LogBuffersLost", c_ulong),
        ("RealTimeBuffersLost", c_ulong),
        ("LoggerThreadId", c_void_p),
        ("LogFileNameOffset", c_ulong),
        ("LoggerNameOffset", c_ulong)
    ]


class EVENT_DESCRIPTOR(Structure):
    """EVENT_DESCRIPTOR 结构体"""
    _fields_ = [
        ("Id", c_ushort),
        ("Version", c_ubyte),
        ("Channel", c_ubyte),
        ("Level", c_ubyte),
        ("Opcode", c_ubyte),
        ("Task", c_ushort),
        ("Keyword", c_ulonglong)
    ]


class EVENT_HEADER(Structure):
    """EVENT_HEADER 结构体"""
    _fields_ = [
        ("Size", c_ushort),
        ("HeaderType", c_ushort),
        ("Flags", c_ushort),
        ("EventProperty", c_ushort),
        ("ThreadId", c_ulong),
        ("ProcessId", c_ulong),
        ("TimeStamp", c_longlong),
        ("ProviderId", GUID),
        ("EventDescriptor", EVENT_DESCRIPTOR),
        ("KernelTime", c_ulong),
        ("UserTime", c_ulong),
        ("ActivityId", GUID)
    ]


class ETW_BUFFER_CONTEXT(Structure):
    """ETW_BUFFER_CONTEXT 结构体"""
    _fields_ = [
        ("ProcessorNumber", c_ubyte),
        ("Alignment", c_ubyte),
        ("LoggerId", c_ushort)
    ]


class EVENT_RECORD(Structure):
    """EVENT_RECORD 结构体"""
    _fields_ = [
        ("EventHeader", EVENT_HEADER),
        ("BufferContext", ETW_BUFFER_CONTEXT),
        ("ExtendedDataCount", c_ushort),
        ("UserDataLength", c_ushort),
        ("ExtendedData", c_void_p),
        ("UserData", c_void_p),
        ("UserContext", c_void_p)
    ]


class EVENT_TRACE_HEADER(Structure):
    """EVENT_TRACE_HEADER 结构体 (旧式)"""
    _fields_ = [
        ("Size", c_ushort),
        ("FieldTypeFlags", c_ushort),
        ("Type", c_ubyte),
        ("Level", c_ubyte),
        ("Version", c_ushort),
        ("ThreadId", c_ulong),
        ("ProcessId", c_ulong),
        ("TimeStamp", c_longlong),
        ("Guid", GUID),
        ("ClientContext", c_ulong),
        ("Flags", c_ulong),
    ]


class EVENT_TRACE(Structure):
    """EVENT_TRACE 结构体"""
    _fields_ = [
        ("Header", EVENT_TRACE_HEADER),
        ("InstanceId", c_ulong),
        ("ParentInstanceId", c_ulong),
        ("ParentGuid", GUID),
        ("MofData", c_void_p),
        ("MofLength", c_ulong),
        ("ClientContext", c_ulong),
    ]


class TIME_ZONE_INFORMATION(Structure):
    """TIME_ZONE_INFORMATION 结构体"""
    _fields_ = [
        ("Bias", ctypes.c_long),
        ("StandardName", c_wchar * 32),
        ("StandardDate", c_ubyte * 16),
        ("StandardBias", ctypes.c_long),
        ("DaylightName", c_wchar * 32),
        ("DaylightDate", c_ubyte * 16),
        ("DaylightBias", ctypes.c_long),
    ]


class TRACE_LOGFILE_HEADER(Structure):
    """TRACE_LOGFILE_HEADER 结构体"""
    _fields_ = [
        ("BufferSize", c_ulong),
        ("Version", c_ulong),
        ("ProviderVersion", c_ulong),
        ("NumberOfProcessors", c_ulong),
        ("EndTime", c_longlong),
        ("TimerResolution", c_ulong),
        ("MaximumFileSize", c_ulong),
        ("LogFileMode", c_ulong),
        ("BuffersWritten", c_ulong),
        ("StartBuffers", c_ulong),
        ("PointerSize", c_ulong),
        ("EventsLost", c_ulong),
        ("CpuSpeedInMHz", c_ulong),
        ("LoggerName", c_void_p),
        ("LogFileName", c_void_p),
        ("TimeZone", TIME_ZONE_INFORMATION),
        ("BootTime", c_longlong),
        ("PerfFreq", c_longlong),
        ("StartTime", c_longlong),
        ("ReservedFlags", c_ulong),
        ("BuffersLost", c_ulong),
    ]


# 回调函数类型
PEVENT_RECORD_CALLBACK = WINFUNCTYPE(None, POINTER(EVENT_RECORD))


class EVENT_TRACE_LOGFILEW(Structure):
    """EVENT_TRACE_LOGFILEW 结构体"""
    _fields_ = [
        ("LogFileName", c_wchar_p),
        ("LoggerName", c_wchar_p),
        ("CurrentTime", c_longlong),
        ("BuffersRead", c_ulong),
        ("LogFileMode", c_ulong),
        ("CurrentEvent", EVENT_TRACE),
        ("LogfileHeader", TRACE_LOGFILE_HEADER),
        ("BufferCallback", c_void_p),
        ("BufferSize", c_ulong),
        ("Filled", c_ulong),
        ("EventsLost", c_ulong),
        ("EventRecordCallback", c_void_p),
        ("IsKernelTrace", c_ulong),
        ("Context", c_void_p)
    ]