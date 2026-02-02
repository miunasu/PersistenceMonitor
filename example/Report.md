## 恶意软件持久化分析报告

### 一、威胁概述

该系统已被植入**双组件远控木马**，具备完整的持久化机制和C2通信能力。

---

### 二、恶意组件详情

#### 组件1: System.exe (伪装Cloudflare隧道)

| 属性 | 值 |
|------|-----|
| 路径 | `C:\ProgramData\Microsoft\System\System.exe` |
| PID | 6380 |
| 权限 | NT AUTHORITY\SYSTEM |
| 持久化 | 服务名 `cloudflared`，AUTO_START |
| C2地址 | `104.21.2.162:443` (ESTABLISHED) |
| 隧道配置 | `--hostname www.tamei.cyou --url tcp://127.0.0.1:443` |

**安装过程**: 由 `cloudflared_installer.tmp` 创建 `C:\ProgramData\Microsoft\System` 目录并释放

**关联文件**:
- `C:\ProgramData\Microsoft\System\System.exe.Manifest`
- `C:\ProgramData\Microsoft\System\System.exe.Local`
- `C:\ProgramData\Microsoft\System\tzres.dll`
- `C:\ProgramData\Microsoft\System\CRYPTBASE.dll`

---

#### 组件2: WindowsEvent.exe (远控客户端)

| 属性 | 值 |
|------|-----|
| 路径 | `C:\ProgramData\CfServerSoftwareDistribution\WindowsEvent.exe` |
| PID | 5348 |
| 权限 | DESKTOP-B7DPE6O\Tom (用户态) |
| 状态 | Not Responding (可能在等待指令) |
| C2地址 | `34.160.111.145:80` (ESTABLISHED) |

**释放的DLL劫持文件** (位于同目录):
- `schtasks.exe` - 计划任务工具副本
- `wininet.dll`, `mscoree.dll`, `amsi.dll` - DLL劫持
- `WINMM.dll`, `IPHLPAPI.DLL`, `dxgi.dll`, `DINPUT8.dll`
- `CoreMessaging.dll`, `CoreUIComponents.dll`, `PROPSYS.dll`
- `iertutil.dll`, `srvcli.dll`, `netutils.dll`, `SspiCli.dll`
- `Wldp.dll`, `profapi.dll`, `urlmon.dll`, `winnlsres.dll`

**下载的配置文件**: `C:\Users\Tom\AppData\Local\Microsoft\Windows\INetCache\IE\PBTVA2J0\raw[1].txt`

---

### 三、攻击链分析

```
1. 初始感染
   |
   v
2. cloudflared_installer.tmp 执行
   |
   +---> 创建 C:\ProgramData\Microsoft\System\
   +---> 释放 System.exe 及依赖DLL
   +---> 注册服务 "cloudflared" (伪装)
   |
   v
3. System.exe 启动
   |
   +---> 建立 Cloudflare 隧道到 www.tamei.cyou
   +---> 连接 C2: 104.21.2.162:443
   |
   v
4. 释放第二阶段载荷
   |
   +---> 创建 C:\ProgramData\CfServerSoftwareDistribution\
   +---> 释放 WindowsEvent.exe 及大量DLL劫持文件
   |
   v
5. WindowsEvent.exe 执行
   |
   +---> 连接 C2: 34.160.111.145:80
   +---> 下载配置 raw[1].txt
   +---> 等待远程指令
```

---

### 四、IOC (威胁指标)

**恶意文件路径**:
- `C:\ProgramData\Microsoft\System\System.exe`
- `C:\ProgramData\CfServerSoftwareDistribution\WindowsEvent.exe`
- `C:\ProgramData\CfServerSoftwareDistribution\*.dll` (多个DLL劫持文件)

**恶意域名/IP**:
- `www.tamei.cyou` (Cloudflare隧道目标)
- `104.21.2.162:443` (System.exe C2)
- `34.160.111.145:80` (WindowsEvent.exe C2)

**恶意服务**:
- 服务名: `cloudflared`
- 显示名: `cloudflared`

**可疑进程**:
- `System.exe` (PID 6380) - 注意: 真正的System进程PID为4
- `WindowsEvent.exe` (PID 5348)

---

### 五、清除建议

1. **停止恶意服务**: `sc stop cloudflared && sc delete cloudflared`
2. **终止恶意进程**: `taskkill /F /PID 6380` 和 `taskkill /F /PID 5348`
3. **删除恶意文件**:
   - `rd /s /q "C:\ProgramData\Microsoft\System"`
   - `rd /s /q "C:\ProgramData\CfServerSoftwareDistribution"`
4. **检查计划任务**: `schtasks /query` 查找可疑项
5. **检查启动项**: 注册表 Run/RunOnce 键值
6. **网络隔离**: 阻断与 C2 IP 的通信
7. **全盘扫描**: 使用杀毒软件进行深度扫描

---

### 六、风险评级

**严重程度: 高危**

- 已建立持久化机制 (服务)
- 已建立活跃C2通信
- 具备DLL劫持能力
- 以SYSTEM权限运行
- 使用Cloudflare隧道规避检测