import ipaddress
import os
import re
import socket
import subprocess
import asyncio

try:
    import psutil
except ImportError:  # pragma: no cover - runtime dependency
    psutil = None

try:
    from pysnmp.hlapi import (
        CommunityData,
        ContextData,
        Integer,
        ObjectIdentity,
        ObjectType,
        SnmpEngine,
        UdpTransportTarget,
        getCmd,
        nextCmd,
    )
    SNMP_MODE = "legacy"
except ImportError:  # pragma: no cover - runtime dependency
    try:
        from pysnmp.hlapi.v1arch import (
            CommunityData,
            ObjectIdentity,
            ObjectType,
            SnmpDispatcher,
            UdpTransportTarget,
            get_cmd,
            next_cmd,
        )

        CommunityData = CommunityData
        ContextData = None
        Integer = None
        ObjectIdentity = ObjectIdentity
        ObjectType = ObjectType
        SnmpEngine = SnmpDispatcher
        UdpTransportTarget = UdpTransportTarget
        getCmd = get_cmd
        nextCmd = next_cmd
        SNMP_MODE = "v1arch_asyncio"
    except ImportError:  # pragma: no cover - runtime dependency
        CommunityData = None
        ContextData = None
        Integer = None
        ObjectIdentity = None
        ObjectType = None
        SnmpEngine = None
        UdpTransportTarget = None
        getCmd = None
        nextCmd = None
        SNMP_MODE = None


SNMP_COMMUNITY = os.getenv("SNMP_COMMUNITY", "public")
SNMP_PORT = int(os.getenv("SNMP_PORT", "161"))
SNMP_TIMEOUT_SEC = float(os.getenv("SNMP_TIMEOUT_SEC", "1"))
SNMP_RETRIES = int(os.getenv("SNMP_RETRIES", "0"))

OID_HR_PROCESSOR_LOAD = "1.3.6.1.2.1.25.3.3.1.2"
OID_HR_MEMORY_SIZE = "1.3.6.1.2.1.25.2.2.0"
OID_HR_STORAGE_TYPE = "1.3.6.1.2.1.25.2.3.1.2"
OID_HR_STORAGE_ALLOC_UNIT = "1.3.6.1.2.1.25.2.3.1.4"
OID_HR_STORAGE_SIZE = "1.3.6.1.2.1.25.2.3.1.5"
OID_HR_STORAGE_USED = "1.3.6.1.2.1.25.2.3.1.6"
OID_HR_STORAGE_RAM_TYPE = "1.3.6.1.2.1.25.2.1.2"
OID_UCD_LOAD_1MIN = "1.3.6.1.4.1.2021.10.1.3.1"
OID_UCD_MEM_TOTAL_KB = "1.3.6.1.4.1.2021.4.5.0"
OID_UCD_MEM_AVAIL_KB = "1.3.6.1.4.1.2021.4.6.0"

# 增强ping时间匹配正则，覆盖更多场景
PING_TIME_PATTERNS = [
    re.compile(r"time[=<]?\s*(\d+(?:\.\d+)?)\s*ms", re.IGNORECASE),
    re.compile(r"时间[=<]?\s*(\d+(?:\.\d+)?)\s*ms"),
    re.compile(r"avg\/min\/max\/mdev = \d+\.\d+\/(\d+\.\d+)\/\d+\.\d+\/\d+\.\d+ ms", re.IGNORECASE),
    re.compile(r"平均\/最小\/最大\/偏差 = \d+\.\d+\/(\d+\.\d+)\/\d+\.\d+\/\d+\.\d+ ms"),
]


def _snmp_available():
    required = (
        CommunityData,
        ObjectIdentity,
        ObjectType,
        SnmpEngine,
        UdpTransportTarget,
        getCmd,
        nextCmd,
    )
    return all(item is not None for item in required) and SNMP_MODE in {
        "legacy",
        "v1arch_asyncio",
    }


def _build_transport(ip):
    if SNMP_MODE == "legacy":
        return UdpTransportTarget(
            (ip, SNMP_PORT),
            timeout=SNMP_TIMEOUT_SEC,
            retries=SNMP_RETRIES,
        )
    return UdpTransportTarget.create(
        (ip, SNMP_PORT),
        timeout=SNMP_TIMEOUT_SEC,
        retries=SNMP_RETRIES,
    )


def _normalize_oid(oid):
    return oid.lstrip(".")


async def _get_snmp_value_v1arch(ip, oid):
    transport = await _build_transport(ip)
    error_indication, error_status, _, var_binds = await getCmd(
        SnmpEngine(),
        CommunityData(SNMP_COMMUNITY),
        transport,
        ObjectType(ObjectIdentity(_normalize_oid(oid))),
    )
    if error_indication or error_status:
        return None

    for _, value in var_binds:
        return value
    return None


async def _walk_snmp_v1arch(ip, oid_prefix):
    values = []
    transport = await _build_transport(ip)
    current_oid = _normalize_oid(oid_prefix)

    while True:
        error_indication, error_status, _, var_binds = await nextCmd(
            SnmpEngine(),
            CommunityData(SNMP_COMMUNITY),
            transport,
            ObjectType(ObjectIdentity(current_oid)),
        )
        if error_indication or error_status:
            return []
        if not var_binds:
            return values

        should_continue = False
        for oid, value in var_binds:
            pretty_oid = oid.prettyPrint()
            if not pretty_oid.startswith(_normalize_oid(oid_prefix)):
                return values
            values.append((pretty_oid, value))
            current_oid = pretty_oid
            should_continue = True
        if not should_continue:
            return values


def get_snmp_value(ip, oid):
    if not _snmp_available():
        return None

    try:
        if SNMP_MODE == "v1arch_asyncio":
            return asyncio.run(_get_snmp_value_v1arch(ip, oid))

        iterator = getCmd(
            SnmpEngine(),
            CommunityData(SNMP_COMMUNITY, mpModel=0),
            _build_transport(ip),
            ContextData(),
            ObjectType(ObjectIdentity(_normalize_oid(oid))),
        )
        error_indication, error_status, _, var_binds = next(iterator)
        if error_indication or error_status:
            return None

        for _, value in var_binds:
            return value
    except Exception:
        return None
    return None


def walk_snmp(ip, oid_prefix):
    if not _snmp_available():
        return []

    values = []
    try:
        if SNMP_MODE == "v1arch_asyncio":
            return asyncio.run(_walk_snmp_v1arch(ip, oid_prefix))

        for error_indication, error_status, _, var_binds in nextCmd(
            SnmpEngine(),
            CommunityData(SNMP_COMMUNITY, mpModel=0),
            _build_transport(ip),
            ContextData(),
            ObjectType(ObjectIdentity(_normalize_oid(oid_prefix))),
            lexicographicMode=False,
        ):
            if error_indication or error_status:
                return []

            for oid, value in var_binds:
                if not oid.prettyPrint().startswith(_normalize_oid(oid_prefix)):
                    return values
                values.append((oid.prettyPrint(), value))
    except Exception:
        return []
    return values


def get_remote_cpu_percent(ip):
    loads = []
    for _, value in walk_snmp(ip, OID_HR_PROCESSOR_LOAD):
        try:
            loads.append(int(value))
        except (TypeError, ValueError):
            continue

    if loads:
        return round(sum(loads) / len(loads), 2)

    # Ubuntu commonly exposes load average through UCD-SNMP even when
    # HOST-RESOURCES-MIB processor metrics are unavailable.
    load_1min = get_snmp_value(ip, OID_UCD_LOAD_1MIN)
    if load_1min is None:
        return None
    try:
        return round(float(str(load_1min)), 2)
    except (TypeError, ValueError):
        return None


def get_remote_memory_percent(ip):
    total_kb = get_snmp_value(ip, OID_HR_MEMORY_SIZE)
    if total_kb is not None:
        try:
            total_kb = int(total_kb)
        except (TypeError, ValueError):
            total_kb = None

    storage_types = {
        oid.rsplit(".", 1)[-1]: value.prettyPrint()
        for oid, value in walk_snmp(ip, OID_HR_STORAGE_TYPE)
    }
    alloc_units = {
        oid.rsplit(".", 1)[-1]: int(value)
        for oid, value in walk_snmp(ip, OID_HR_STORAGE_ALLOC_UNIT)
        if str(value).isdigit()
    }
    sizes = {
        oid.rsplit(".", 1)[-1]: int(value)
        for oid, value in walk_snmp(ip, OID_HR_STORAGE_SIZE)
        if str(value).isdigit()
    }
    used_values = {
        oid.rsplit(".", 1)[-1]: int(value)
        for oid, value in walk_snmp(ip, OID_HR_STORAGE_USED)
        if str(value).isdigit()
    }

    for index, storage_type in storage_types.items():
        if storage_type != OID_HR_STORAGE_RAM_TYPE:
            continue

        alloc_unit = alloc_units.get(index)
        size = sizes.get(index)
        used = used_values.get(index)
        if not alloc_unit or size is None or used is None:
            continue

        total_bytes = size * alloc_unit
        used_bytes = used * alloc_unit
        if total_bytes <= 0:
            continue
        return round((used_bytes / total_bytes) * 100, 2)

    if total_kb and total_kb > 0:
        for index, used in used_values.items():
            if storage_types.get(index) != OID_HR_STORAGE_RAM_TYPE:
                continue
            alloc_unit = alloc_units.get(index)
            if not alloc_unit:
                continue
            used_kb = (used * alloc_unit) / 1024.0
            return round((used_kb / total_kb) * 100, 2)

    total_kb = get_snmp_value(ip, OID_UCD_MEM_TOTAL_KB)
    avail_kb = get_snmp_value(ip, OID_UCD_MEM_AVAIL_KB)
    try:
        total_kb = int(total_kb) if total_kb is not None else None
        avail_kb = int(avail_kb) if avail_kb is not None else None
    except (TypeError, ValueError):
        return None

    if total_kb and avail_kb is not None and total_kb > 0:
        used_kb = max(total_kb - avail_kb, 0)
        return round((used_kb / total_kb) * 100, 2)

    return None


def ping_device(ip):
    try:
        # 适配Windows/Linux不同的ping参数
        if os.name == "nt":
            ping_cmd = ["ping", "-n", "1", "-w", "1000", ip]
        else:
            ping_cmd = ["ping", "-c", "1", "-W", "1", ip]
        
        result = subprocess.run(
            ping_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
    except OSError:
        return None

    if result.returncode != 0:
        return None

    output = result.stdout or ""
    # 优先匹配具体的时间值
    for pattern in PING_TIME_PATTERNS:
        match = pattern.search(output)
        if match:
            try:
                delay = round(float(match.group(1)), 2)
                # 确保延迟值大于0（极小值）
                return delay if delay > 0 else 0.01
            except ValueError:
                continue

    # 若未匹配到具体时间但通了，返回极小非零值（替代原来的0.0）
    if "TTL=" in output.upper() or "TTL:" in output.upper():
        return 0.01
    return None


def collect_status(ip):
    local_ip = get_local_ip()

    delay = ping_device(ip)
    cpu = 0.0
    memory = 0.0

    if delay is not None:
        if ip == local_ip and psutil is not None:
            cpu = round(psutil.cpu_percent(interval=0.2), 2)
            memory = round(psutil.virtual_memory().percent, 2)
        else:
            remote_cpu = get_remote_cpu_percent(ip)
            remote_memory = get_remote_memory_percent(ip)
            if remote_cpu is not None:
                cpu = remote_cpu
            if remote_memory is not None:
                memory = remote_memory

    return {
        "ip": ip,
        "delay": delay,  # 此时delay要么是None，要么是>0的数值
        "cpu": cpu,
        "memory": memory,
    }


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def get_local_network():
    real_ip = get_local_ip()
    if real_ip.startswith("127.") or real_ip.startswith("169.254."):
        network = ipaddress.IPv4Network(f"{real_ip}/24", strict=False)
        return real_ip, network

    # 适配Windows/Linux不同的网络命令
    if os.name == "nt":
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            errors="ignore",
        )
    else:
        result = subprocess.run(
            ["ifconfig"],
            capture_output=True,
            text=True,
            errors="ignore",
        )
    
    text = result.stdout
    blocks = re.split(r"\r?\n\r?\n", text.strip())
    for block in blocks:
        if real_ip in block:
            mask_match = re.search(
                r"(Subnet Mask|子网掩码|netmask)[^\d]*(\d+\.\d+\.\d+\.\d+)",
                block,
                re.IGNORECASE,
            )
            if mask_match:
                mask = mask_match.group(2)
                try:
                    network = ipaddress.IPv4Network(f"{real_ip}/{mask}", strict=False)
                    return real_ip, network
                except Exception:
                    break

    network = ipaddress.IPv4Network(f"{real_ip}/24", strict=False)
    return real_ip, network


def discover_lan_hosts(timeout_per_host=0.2):
    local_ip, network = get_local_network()
    hosts = [local_ip]
    # 适配Windows/Linux的ping超时参数
    timeout_ms = int(timeout_per_host * 1000)
    for host in network.hosts():
        ip = str(host)
        if ip == local_ip:
            continue
        try:
            if os.name == "nt":
                ping_cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
            else:
                ping_cmd = ["ping", "-c", "1", "-W", str(int(timeout_per_host)), ip]
            
            result = subprocess.run(
                ping_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode == 0:
                hosts.append(ip)
        except OSError:
            continue
    return local_ip, hosts