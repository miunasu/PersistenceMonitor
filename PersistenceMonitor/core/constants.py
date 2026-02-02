"""ETW 常量定义"""

# ETW 控制常量
WNODE_FLAG_TRACED_GUID = 0x00020000
EVENT_TRACE_REAL_TIME_MODE = 0x00000100
PROCESS_TRACE_MODE_REAL_TIME = 0x00000100
PROCESS_TRACE_MODE_EVENT_RECORD = 0x10000000
EVENT_TRACE_CONTROL_STOP = 1
EVENT_CONTROL_CODE_ENABLE_PROVIDER = 1
EVENT_CONTROL_CODE_DISABLE_PROVIDER = 0

# 跟踪级别
TRACE_LEVEL_CRITICAL = 1
TRACE_LEVEL_ERROR = 2
TRACE_LEVEL_WARNING = 3
TRACE_LEVEL_INFORMATION = 4
TRACE_LEVEL_VERBOSE = 5

# 无效句柄
INVALID_PROCESSTRACE_HANDLE = 0xFFFFFFFFFFFFFFFF

# 进程访问权限
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

# Microsoft-Windows-Kernel-File 事件 ID
EVENT_ID_NAMECREATE = 10    # 文件名创建
EVENT_ID_NAMEDELETE = 11    # 文件名删除
EVENT_ID_CREATE = 12        # Create/Open
EVENT_ID_CLEANUP = 13       # Cleanup
EVENT_ID_CLOSE = 14         # Close
EVENT_ID_READ = 15          # Read
EVENT_ID_WRITE = 16         # Write
EVENT_ID_SETINFO = 17       # SetInformation
EVENT_ID_DELETE = 18        # Delete
EVENT_ID_RENAME = 19        # Rename
EVENT_ID_DIRENUM = 20       # DirEnum
EVENT_ID_FLUSH = 21         # Flush
EVENT_ID_QUERYINFO = 22     # QueryInformation
EVENT_ID_FSCTL = 23         # FSControl
EVENT_ID_OPERATIONEND = 24  # OperationEnd
EVENT_ID_DIRNOTIFY = 25     # DirNotify

# 事件名称映射
EVENT_NAMES = {
    EVENT_ID_NAMECREATE: 'name_create',
    EVENT_ID_NAMEDELETE: 'name_delete',
    EVENT_ID_CREATE: 'create',
    EVENT_ID_CLEANUP: 'cleanup',
    EVENT_ID_CLOSE: 'close',
    EVENT_ID_READ: 'read',
    EVENT_ID_WRITE: 'write',
    EVENT_ID_SETINFO: 'setinfo',
    EVENT_ID_DELETE: 'delete',
    EVENT_ID_RENAME: 'rename',
    EVENT_ID_DIRENUM: 'direnum',
    EVENT_ID_FLUSH: 'flush',
    EVENT_ID_QUERYINFO: 'queryinfo',
    EVENT_ID_FSCTL: 'fsctl',
    EVENT_ID_OPERATIONEND: 'opend',
    EVENT_ID_DIRNOTIFY: 'dirnotify',
}

# 感兴趣的文件事件
INTERESTING_FILE_EVENTS = {
    EVENT_ID_NAMECREATE,
    EVENT_ID_NAMEDELETE,
    EVENT_ID_CREATE,
    EVENT_ID_WRITE,
    EVENT_ID_DELETE,
    EVENT_ID_RENAME,
}

# 高风险文件扩展名
HIGH_RISK_EXTENSIONS = {
    '.exe', '.dll', '.sys', '.bat', '.cmd', '.ps1', '.vbs',
    '.js', '.jar', '.msi', '.scr', '.com', '.pif', '.cpl',
    '.hta', '.wsf', '.vbe', '.jse'
}

# 中等风险扩展名
MEDIUM_RISK_EXTENSIONS = {
    '.lnk', '.url', '.inf', '.reg', '.msp', '.mst',
    '.application', '.gadget', '.efi', '.ocx'
}

# 噪音路径过滤
NOISE_PATH_PATTERNS = [
    "$MFT", "$LOGFILE", "$USNJRNL", "$EXTEND",
    "\\PREFETCH\\", "\\WINEVT\\", "\\CONFIG\\",
    ".ETL", ".LOG", ".PF", ".REGTRANS-MS", ".BLF"
]

# 会话名称
DEFAULT_SESSION_NAME = "SporeFileMonitorSession"